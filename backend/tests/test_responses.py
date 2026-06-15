import json
from decimal import Decimal

import pytest

from common.responses import json_default, json_response


def test_json_response_serializes_decimal_values():
    response = json_response(
        200,
        {
            "ticker": "NVDA",
            "percent_change": Decimal("3.41"),
            "close_price": Decimal("142.53"),
        },
    )

    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["ticker"] == "NVDA"
    assert body["percent_change"] == 3.41
    assert body["close_price"] == 142.53
    assert response["headers"]["Content-Type"] == "application/json"


def test_json_response_merges_custom_headers():
    response = json_response(
        200,
        {"items": []},
        headers={
            "X-Result-Count": "0",
        },
    )

    assert response["headers"]["X-Result-Count"] == "0"
    assert response["headers"]["Cache-Control"] == "public, max-age=300"


def test_json_default_rejects_unsupported_type():
    with pytest.raises(TypeError, match="not JSON serializable"):
        json_default(object())