import json

from ingest import handler


def test_ingest_handler_saves_top_mover(monkeypatch):
    def fake_get_stock_api_key():
        return "fake-key"

    def fake_fetch_watchlist_data(api_key):
        assert api_key == "fake-key"

        return [
            {
                "date": "2026-06-12",
                "ticker": "AAPL",
                "open_price": 100,
                "close_price": 102,
            },
            {
                "date": "2026-06-12",
                "ticker": "TSLA",
                "open_price": 100,
                "close_price": 94,
            },
        ]

    saved_winners = []

    def fake_save_winner(winner):
        saved_winners.append(winner)

    monkeypatch.setattr(handler, "get_stock_api_key", fake_get_stock_api_key)
    monkeypatch.setattr(handler, "fetch_watchlist_data", fake_fetch_watchlist_data)
    monkeypatch.setattr(handler, "save_winner", fake_save_winner)

    response = handler.lambda_handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["winner"]["ticker"] == "TSLA"
    assert body["winner"]["percent_change"] == -6.0
    assert saved_winners[0]["ticker"] == "TSLA"


def test_ingest_handler_returns_502_when_no_records(monkeypatch):
    monkeypatch.setattr(handler, "get_stock_api_key", lambda: "fake-key")
    monkeypatch.setattr(handler, "fetch_watchlist_data", lambda api_key: [])

    response = handler.lambda_handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 502
    assert body["message"] == "no valid stock records were available"


def test_ingest_handler_returns_500_when_secret_fails(monkeypatch):
    def fake_get_stock_api_key():
        raise handler.SecretError("missing secret")

    monkeypatch.setattr(handler, "get_stock_api_key", fake_get_stock_api_key)

    response = handler.lambda_handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert body["message"] == "could not load stock API key"

def test_ingest_handler_returns_502_when_stock_api_fails(monkeypatch):
    def fake_fetch_watchlist_data(api_key):
        raise handler.StockApiError("api failed")

    monkeypatch.setattr(handler, "get_stock_api_key", lambda: "fake-key")
    monkeypatch.setattr(handler, "fetch_watchlist_data", fake_fetch_watchlist_data)

    response = handler.lambda_handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 502
    assert body["message"] == "stock API request failed"

def test_ingest_handler_returns_429_when_rate_limited(monkeypatch):
    def fake_fetch_watchlist_data(api_key):
        raise handler.RateLimitError("stock API rate limit reached")

    monkeypatch.setattr(handler, "get_stock_api_key", lambda: "fake-key")
    monkeypatch.setattr(handler, "fetch_watchlist_data", fake_fetch_watchlist_data)

    response = handler.lambda_handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 429
    assert body["message"] == "stock API rate limit reached"


def test_ingest_handler_returns_500_when_unexpected_error_happens(monkeypatch):
    def fake_save_winner(winner):
        raise RuntimeError("database failed")

    monkeypatch.setattr(handler, "get_stock_api_key", lambda: "fake-key")
    monkeypatch.setattr(
        handler,
        "fetch_watchlist_data",
        lambda api_key: [
            {
                "date": "2026-06-12",
                "ticker": "AAPL",
                "open_price": 100,
                "close_price": 105,
            }
        ],
    )
    monkeypatch.setattr(handler, "save_winner", fake_save_winner)

    response = handler.lambda_handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert body["message"] == "unexpected ingestion error"