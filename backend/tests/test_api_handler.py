import json

from api import handler


def test_api_handler_returns_movers(monkeypatch):
    def fake_get_recent_movers_page(limit, cursor=None):
        assert limit == 7
        assert cursor is None

        return {
            "items": [
                {
                    "date": "2026-06-12",
                    "ticker": "NVDA",
                    "percent_change": 3.41,
                    "close_price": 142.53,
                    "direction": "up",
                }
            ],
            "count": 1,
            "limit": limit,
            "next_cursor": None,
            "has_more": False,
        }

    monkeypatch.setattr(handler, "get_recent_movers_page", fake_get_recent_movers_page)

    response = handler.lambda_handler({"httpMethod": "GET"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["count"] == 1
    assert body["items"][0]["ticker"] == "NVDA"
    assert body["limit"] == 7
    assert body["has_more"] is False
    assert response["headers"]["X-Result-Count"] == "1"
    assert response["headers"]["X-Page-Limit"] == "7"
    assert response["headers"]["Cache-Control"] == "public, max-age=300"


def test_api_handler_supports_limit_and_cursor(monkeypatch):
    def fake_get_recent_movers_page(limit, cursor=None):
        assert limit == 3
        assert cursor == "abc123"

        return {
            "items": [],
            "count": 0,
            "limit": limit,
            "next_cursor": "next456",
            "has_more": True,
        }

    monkeypatch.setattr(handler, "get_recent_movers_page", fake_get_recent_movers_page)

    response = handler.lambda_handler(
        {
            "httpMethod": "GET",
            "queryStringParameters": {
                "limit": "3",
                "cursor": "abc123",
            },
        },
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["next_cursor"] == "next456"
    assert body["has_more"] is True
    assert response["headers"]["X-Next-Cursor"] == "next456"


def test_api_handler_returns_400_for_invalid_limit():
    response = handler.lambda_handler(
        {
            "httpMethod": "GET",
            "queryStringParameters": {
                "limit": "not-a-number",
            },
        },
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["message"] == "limit must be a number"


def test_api_handler_returns_400_for_limit_out_of_range():
    response = handler.lambda_handler(
        {
            "httpMethod": "GET",
            "queryStringParameters": {
                "limit": "100",
            },
        },
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["message"] == "limit must be between 1 and 30"


def test_api_handler_returns_400_for_invalid_cursor(monkeypatch):
    def fake_get_recent_movers_page(limit, cursor=None):
        raise handler.InvalidCursorError("invalid pagination cursor")

    monkeypatch.setattr(handler, "get_recent_movers_page", fake_get_recent_movers_page)

    response = handler.lambda_handler(
        {
            "httpMethod": "GET",
            "queryStringParameters": {
                "cursor": "bad-cursor",
            },
        },
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["message"] == "invalid pagination cursor"


def test_api_handler_returns_cors_preflight_response():
    response = handler.lambda_handler({"httpMethod": "OPTIONS"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["message"] == "cors preflight ok"


def test_api_handler_supports_http_api_method_format(monkeypatch):
    monkeypatch.setattr(
        handler,
        "get_recent_movers_page",
        lambda limit, cursor=None: {
            "items": [],
            "count": 0,
            "limit": limit,
            "next_cursor": None,
            "has_more": False,
        },
    )

    event = {
        "requestContext": {
            "http": {
                "method": "GET",
            }
        }
    }

    response = handler.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["items"] == []


def test_api_handler_returns_500_when_reader_fails(monkeypatch):
    def fake_get_recent_movers_page(limit, cursor=None):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(handler, "get_recent_movers_page", fake_get_recent_movers_page)

    response = handler.lambda_handler({"httpMethod": "GET"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert body["message"] == "could not load movers"


def test_api_handler_returns_405_for_unsupported_method():
    response = handler.lambda_handler({"httpMethod": "POST"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 405
    assert body["message"] == "method not allowed"
