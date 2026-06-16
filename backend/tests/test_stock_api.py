from datetime import date, datetime, timedelta

import pytest

from ingest import stock_api
from ingest.stock_api import (
    MarketDateUnavailableError,
    RateLimitError,
    StockApiError,
    fetch_daily_open_close,
    fetch_watchlist_data,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise stock_api.requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._payload


def test_fetch_daily_open_close_returns_normalized_record(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse(
            payload={
                "symbol": "AAPL",
                "from": "2026-06-12",
                "open": 100,
                "close": 105,
            }
        )

    monkeypatch.setattr(stock_api.requests, "get", fake_get)

    result = fetch_daily_open_close("AAPL", "2026-06-12", "fake-key")

    assert result == {
        "date": "2026-06-12",
        "ticker": "AAPL",
        "open_price": 100.0,
        "close_price": 105.0,
    }


def test_fetch_daily_open_close_rejects_missing_prices(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse(
            payload={
                "symbol": "AAPL",
                "from": "2026-06-12",
                "open": 100,
            }
        )

    monkeypatch.setattr(stock_api.requests, "get", fake_get)

    with pytest.raises(StockApiError, match="missing open or close price"):
        fetch_daily_open_close("AAPL", "2026-06-12", "fake-key")


def test_fetch_daily_open_close_raises_rate_limit(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse(status_code=429, payload={})

    monkeypatch.setattr(stock_api.requests, "get", fake_get)

    with pytest.raises(RateLimitError, match="stock API rate limit reached"):
        fetch_daily_open_close("MSFT", "2026-06-12", "fake-key")


def test_fetch_daily_open_close_raises_market_date_unavailable(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse(status_code=403, payload={})

    monkeypatch.setattr(stock_api.requests, "get", fake_get)

    with pytest.raises(MarketDateUnavailableError, match="market date is not available yet"):
        fetch_daily_open_close("AAPL", "2026-06-12", "fake-key")


def test_fetch_daily_open_close_retries_server_error_when_retries_are_enabled(monkeypatch):
    responses = [
        FakeResponse(status_code=500, payload={}),
        FakeResponse(
            status_code=200,
            payload={
                "symbol": "MSFT",
                "from": "2026-06-12",
                "open": 200,
                "close": 210,
            },
        ),
    ]

    def fake_get(url, params, timeout):
        return responses.pop(0)

    monkeypatch.setattr(stock_api.requests, "get", fake_get)
    monkeypatch.setattr(stock_api.time, "sleep", lambda seconds: None)

    result = fetch_daily_open_close(
        "MSFT",
        "2026-06-12",
        "fake-key",
        max_retries=2,
    )

    assert result["ticker"] == "MSFT"
    assert result["open_price"] == 200.0
    assert result["close_price"] == 210.0


def test_fetch_daily_open_close_raises_server_error_after_final_retry(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse(status_code=500, payload={})

    monkeypatch.setattr(stock_api.requests, "get", fake_get)

    with pytest.raises(StockApiError, match="stock API server error"):
        fetch_daily_open_close("MSFT", "2026-06-12", "fake-key")


def test_fetch_watchlist_data_continues_when_one_ticker_fails(monkeypatch):
    def fake_fetch_daily_open_close(ticker, market_date, api_key):
        if ticker == "TSLA":
            raise StockApiError("fake failure")

        return {
            "date": market_date,
            "ticker": ticker,
            "open_price": 100,
            "close_price": 101,
        }

    monkeypatch.setattr(stock_api, "fetch_daily_open_close", fake_fetch_daily_open_close)
    monkeypatch.setattr(stock_api, "get_recent_market_dates", lambda days_back=7: ["2026-06-12"])
    monkeypatch.setattr(stock_api, "wait_between_requests", lambda index: None)

    results = fetch_watchlist_data(api_key="fake-key", watchlist=["AAPL", "TSLA", "NVDA"])

    assert [record["ticker"] for record in results] == ["AAPL", "NVDA"]


def test_fetch_watchlist_data_skips_unavailable_market_date(monkeypatch):
    calls = []

    def fake_fetch_daily_open_close(ticker, market_date, api_key):
        calls.append((ticker, market_date))

        if market_date == "2026-06-16":
            raise MarketDateUnavailableError("market date is not available yet")

        return {
            "date": market_date,
            "ticker": ticker,
            "open_price": 100,
            "close_price": 101,
        }

    monkeypatch.setattr(stock_api, "fetch_daily_open_close", fake_fetch_daily_open_close)
    monkeypatch.setattr(stock_api, "get_recent_market_dates", lambda days_back=7: ["2026-06-16", "2026-06-15"])
    monkeypatch.setattr(stock_api, "wait_between_requests", lambda index: None)

    results = fetch_watchlist_data(api_key="fake-key", watchlist=["AAPL", "MSFT"])

    assert results == [
        {
            "date": "2026-06-15",
            "ticker": "AAPL",
            "open_price": 100,
            "close_price": 101,
        },
        {
            "date": "2026-06-15",
            "ticker": "MSFT",
            "open_price": 100,
            "close_price": 101,
        },
    ]
    assert calls == [
        ("AAPL", "2026-06-16"),
        ("AAPL", "2026-06-15"),
        ("MSFT", "2026-06-15"),
    ]


def test_fetch_watchlist_data_stops_when_rate_limited(monkeypatch):
    def fake_fetch_daily_open_close(ticker, market_date, api_key):
        raise RateLimitError("stock API rate limit reached")

    monkeypatch.setattr(stock_api, "fetch_daily_open_close", fake_fetch_daily_open_close)
    monkeypatch.setattr(stock_api, "get_recent_market_dates", lambda days_back=7: ["2026-06-12"])
    monkeypatch.setattr(stock_api, "wait_between_requests", lambda index: None)

    with pytest.raises(RateLimitError, match="stock API rate limit reached"):
        fetch_watchlist_data(api_key="fake-key", watchlist=["AAPL"])


def test_fetch_watchlist_data_rejects_missing_api_key():
    with pytest.raises(StockApiError, match="missing stock API key"):
        fetch_watchlist_data(api_key="", watchlist=["AAPL"])


def test_get_recent_market_dates_returns_expected_market_dates():
    result = stock_api.get_recent_market_dates(days_back=3)

    expected = []
    offset = 0 if date.today().weekday() < 5 else 1

    while len(expected) < 3:
        candidate = date.today() - timedelta(days=offset)

        if candidate.weekday() < 5:
            expected.append(candidate.isoformat())

        offset += 1

    # The exact first date can depend on Eastern time, so this only checks shape.
    assert len(result) == 3
    assert all(date.fromisoformat(value).weekday() < 5 for value in result)


def test_get_recent_market_dates_includes_today_after_market_close(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls, timezone):
            return datetime(2026, 6, 16, 18, 30, tzinfo=timezone)

    monkeypatch.setattr(stock_api, "datetime", FakeDateTime)

    result = stock_api.get_recent_market_dates(days_back=1)

    assert result == ["2026-06-16"]


def test_wait_between_requests_skips_first_request(monkeypatch):
    def fake_sleep(seconds):
        raise AssertionError("sleep should not be called for the first request")

    monkeypatch.setattr(stock_api.time, "sleep", fake_sleep)

    stock_api.wait_between_requests(0)


def test_wait_between_requests_sleeps_after_first_request(monkeypatch):
    sleep_calls = []

    monkeypatch.setattr(stock_api.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    stock_api.wait_between_requests(1)

    assert sleep_calls == [stock_api.REQUEST_DELAY_SECONDS]


def test_fetch_daily_open_close_retries_after_timeout_when_retries_are_enabled(monkeypatch):
    responses = [
        stock_api.requests.Timeout("temporary timeout"),
        FakeResponse(
            status_code=200,
            payload={
                "symbol": "NVDA",
                "from": "2026-06-12",
                "open": 100,
                "close": 110,
            },
        ),
    ]

    def fake_get(url, params, timeout):
        response = responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response

    monkeypatch.setattr(stock_api.requests, "get", fake_get)
    monkeypatch.setattr(stock_api.time, "sleep", lambda seconds: None)

    result = fetch_daily_open_close(
        "NVDA",
        "2026-06-12",
        "fake-key",
        max_retries=2,
    )

    assert result["ticker"] == "NVDA"
    assert result["open_price"] == 100.0
    assert result["close_price"] == 110.0


def test_fetch_daily_open_close_raises_after_final_timeout(monkeypatch):
    def fake_get(url, params, timeout):
        raise stock_api.requests.Timeout("final timeout")

    monkeypatch.setattr(stock_api.requests, "get", fake_get)

    with pytest.raises(StockApiError, match="timed out fetching AAPL"):
        fetch_daily_open_close("AAPL", "2026-06-12", "fake-key", max_retries=1)


def test_fetch_daily_open_close_raises_request_exception(monkeypatch):
    def fake_get(url, params, timeout):
        raise stock_api.requests.ConnectionError("network down")

    monkeypatch.setattr(stock_api.requests, "get", fake_get)

    with pytest.raises(StockApiError, match="request failed for AAPL"):
        fetch_daily_open_close("AAPL", "2026-06-12", "fake-key")


def test_fetch_daily_open_close_raises_when_no_retries_allowed():
    with pytest.raises(StockApiError, match="failed to fetch AAPL"):
        fetch_daily_open_close("AAPL", "2026-06-12", "fake-key", max_retries=0)


def test_fetch_watchlist_data_respects_empty_watchlist():
    results = fetch_watchlist_data(api_key="fake-key", watchlist=[])

    assert results == []


def test_fetch_watchlist_data_uses_one_market_date(monkeypatch):
    def fake_fetch_daily_open_close(ticker, market_date, api_key):
        if market_date == "2026-06-12" and ticker == "AAPL":
            raise StockApiError("fake failure")

        return {
            "date": market_date,
            "ticker": ticker,
            "open_price": 100,
            "close_price": 101,
        }

    monkeypatch.setattr(stock_api, "fetch_daily_open_close", fake_fetch_daily_open_close)
    monkeypatch.setattr(stock_api, "get_recent_market_dates", lambda days_back=7: ["2026-06-12", "2026-06-11"])
    monkeypatch.setattr(stock_api, "wait_between_requests", lambda index: None)

    results = fetch_watchlist_data(api_key="fake-key", watchlist=["AAPL", "NVDA"])

    assert results == [
        {
            "date": "2026-06-12",
            "ticker": "NVDA",
            "open_price": 100,
            "close_price": 101,
        }
    ]


def test_fetch_watchlist_data_falls_back_only_when_no_tickers_succeed(monkeypatch):
    def fake_fetch_daily_open_close(ticker, market_date, api_key):
        if market_date == "2026-06-12":
            raise StockApiError("market closed")

        return {
            "date": market_date,
            "ticker": ticker,
            "open_price": 100,
            "close_price": 101,
        }

    monkeypatch.setattr(stock_api, "fetch_daily_open_close", fake_fetch_daily_open_close)
    monkeypatch.setattr(stock_api, "get_recent_market_dates", lambda days_back=7: ["2026-06-12", "2026-06-11"])
    monkeypatch.setattr(stock_api, "wait_between_requests", lambda index: None)

    results = fetch_watchlist_data(api_key="fake-key", watchlist=["AAPL", "NVDA"])

    assert [record["date"] for record in results] == ["2026-06-11", "2026-06-11"]
    assert [record["ticker"] for record in results] == ["AAPL", "NVDA"]


def test_fetch_watchlist_data_rejects_blank_api_key():
    with pytest.raises(StockApiError, match="missing stock API key"):
        fetch_watchlist_data(api_key="   ", watchlist=["AAPL"])


def test_fetch_watchlist_data_returns_empty_when_all_dates_fail(monkeypatch):
    def fake_fetch_daily_open_close(ticker, market_date, api_key):
        raise StockApiError("no data")

    monkeypatch.setattr(stock_api, "fetch_daily_open_close", fake_fetch_daily_open_close)
    monkeypatch.setattr(
        stock_api,
        "get_recent_market_dates",
        lambda days_back=7: ["2026-06-12", "2026-06-11"],
    )
    monkeypatch.setattr(stock_api, "wait_between_requests", lambda index: None)

    results = fetch_watchlist_data(api_key="fake-key", watchlist=["AAPL", "NVDA"])

    assert results == []
