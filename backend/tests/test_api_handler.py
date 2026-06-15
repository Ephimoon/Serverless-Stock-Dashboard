import json

from api import handler


def test_api_handler_returns_movers(monkeypatch):
    def fake_get_recent_movers(limit):
        assert limit == 7

        return [
            {
                "date": "2026-06-12",
                "ticker": "NVDA",
                "percent_change": 3.41,
                "close_price": 142.53,
                "direction": "up",
            }
        ]

    monkeypatch.setattr(handler, "get_recent_movers", fake_get_recent_movers)

    response = handler.lambda_handler({"httpMethod": "GET"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["count"] == 1
    assert body["items"][0]["ticker"] == "NVDA"
    assert response["headers"]["X-Result-Count"] == "1"
    assert response["headers"]["Cache-Control"] == "public, max-age=300"


def test_api_handler_returns_cors_preflight_response():
    response = handler.lambda_handler({"httpMethod": "OPTIONS"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["message"] == "cors preflight ok"


def test_api_handler_supports_http_api_method_format(monkeypatch):
    monkeypatch.setattr(handler, "get_recent_movers", lambda limit: [])

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
    def fake_get_recent_movers(limit):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(handler, "get_recent_movers", fake_get_recent_movers)

    response = handler.lambda_handler({"httpMethod": "GET"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert body["message"] == "could not load movers"