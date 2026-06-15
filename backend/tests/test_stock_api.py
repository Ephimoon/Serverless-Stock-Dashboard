from datetime import date, timedelta

import pytest

from ingest import stock_api
from ingest.stock_api import StockApiError, fetch_daily_open_close, fetch_watchlist_data


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


def test_fetch_daily_open_close_retries_rate_limit(monkeypatch):
    responses = [
        FakeResponse(status_code=429, payload={}),
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

    result = fetch_daily_open_close("MSFT", "2026-06-12", "fake-key")

    assert result["ticker"] == "MSFT"
    assert result["open_price"] == 200.0
    assert result["close_price"] == 210.0


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

    results = fetch_watchlist_data(api_key="fake-key", watchlist=["AAPL", "TSLA", "NVDA"])

    assert [record["ticker"] for record in results] == ["AAPL", "NVDA"]


def test_fetch_watchlist_data_rejects_missing_api_key():
    with pytest.raises(StockApiError, match="missing stock API key"):
        fetch_watchlist_data(api_key="", watchlist=["AAPL"])

def test_get_recent_market_dates_returns_expected_dates():
    result = stock_api.get_recent_market_dates(days_back=3)

    expected = [
        date.today().isoformat(),
        (date.today() - timedelta(days=1)).isoformat(),
        (date.today() - timedelta(days=2)).isoformat(),
    ]

    assert result == expected


def test_fetch_daily_open_close_retries_after_timeout(monkeypatch):
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

    result = fetch_daily_open_close("NVDA", "2026-06-12", "fake-key")

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