import base64
import json
from decimal import Decimal

import pytest

from api import dynamodb_reader
from api.dynamodb_reader import (
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
    get_recent_movers,
    get_recent_movers_page,
    normalize_mover_item,
    to_float,
)


class FakeTable:
    def __init__(self, response):
        self.response = response
        self.query_kwargs = None

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return self.response


def test_to_float_converts_decimal():
    assert to_float(Decimal("3.41")) == 3.41


def test_to_float_converts_regular_number():
    assert to_float("3.41") == 3.41


def test_normalize_mover_item_formats_api_record():
    item = {
        "date": "2026-06-12",
        "ticker": "NVDA",
        "percent_change": Decimal("3.41"),
        "close_price": Decimal("142.53"),
        "direction": "up",
    }

    result = normalize_mover_item(item)

    assert result == {
        "date": "2026-06-12",
        "ticker": "NVDA",
        "percent_change": 3.41,
        "close_price": 142.53,
        "direction": "up",
    }


def test_normalize_mover_item_defaults_direction_from_percent_change():
    item = {
        "date": "2026-06-12",
        "ticker": "TSLA",
        "percent_change": Decimal("-6.0"),
        "close_price": Decimal("94.0"),
    }

    result = normalize_mover_item(item)

    assert result["direction"] == "down"


def test_encode_and_decode_cursor_round_trip():
    cursor = encode_cursor({"record_type": "DAILY_WINNER", "date": "2026-06-12"})

    assert decode_cursor(cursor) == {
        "record_type": "DAILY_WINNER",
        "date": "2026-06-12",
    }


def test_decode_cursor_rejects_invalid_cursor():
    with pytest.raises(InvalidCursorError, match="invalid pagination cursor"):
        decode_cursor("not-valid-json")


def test_get_recent_movers_queries_daily_winners_with_limit():
    fake_table = FakeTable(
        {
            "Items": [
                {
                    "record_type": "DAILY_WINNER",
                    "date": "2026-06-12",
                    "ticker": "NVDA",
                    "percent_change": Decimal("3.4"),
                    "close_price": Decimal("142"),
                    "direction": "up",
                }
            ]
        }
    )

    result = get_recent_movers(limit=7, table=fake_table)

    assert len(result) == 1
    assert result[0]["ticker"] == "NVDA"
    assert fake_table.query_kwargs["ScanIndexForward"] is False
    assert fake_table.query_kwargs["Limit"] == 7


def test_get_recent_movers_page_returns_next_cursor():
    fake_table = FakeTable(
        {
            "Items": [
                {
                    "record_type": "DAILY_WINNER",
                    "date": "2026-06-12",
                    "ticker": "NVDA",
                    "percent_change": Decimal("3.4"),
                    "close_price": Decimal("142"),
                    "direction": "up",
                }
            ],
            "LastEvaluatedKey": {
                "record_type": "DAILY_WINNER",
                "date": "2026-06-12",
            },
        }
    )

    page = get_recent_movers_page(limit=1, table=fake_table)

    assert page["count"] == 1
    assert page["limit"] == 1
    assert page["has_more"] is True
    assert decode_cursor(page["next_cursor"]) == {
        "record_type": "DAILY_WINNER",
        "date": "2026-06-12",
    }


def test_get_recent_movers_page_uses_cursor():
    cursor = encode_cursor({"record_type": "DAILY_WINNER", "date": "2026-06-12"})
    fake_table = FakeTable({"Items": []})

    page = get_recent_movers_page(limit=2, cursor=cursor, table=fake_table)

    assert page["items"] == []
    assert page["has_more"] is False
    assert fake_table.query_kwargs["ExclusiveStartKey"] == {
        "record_type": "DAILY_WINNER",
        "date": "2026-06-12",
    }


def test_get_table_returns_configured_dynamodb_table(monkeypatch):
    class FakeDynamoDBResource:
        def Table(self, table_name):
            return {"table_name": table_name}

    def fake_boto3_resource(service_name, region_name):
        assert service_name == "dynamodb"
        assert region_name == dynamodb_reader.AWS_REGION
        return FakeDynamoDBResource()

    monkeypatch.setattr(dynamodb_reader.boto3, "resource", fake_boto3_resource)

    table = dynamodb_reader.get_table()

    assert table == {"table_name": dynamodb_reader.TABLE_NAME}


def test_get_recent_movers_uses_default_table_when_table_not_provided(monkeypatch):
    fake_table = FakeTable(
        {
            "Items": [
                {
                    "record_type": "DAILY_WINNER",
                    "date": "2026-06-12",
                    "ticker": "NVDA",
                    "percent_change": Decimal("3.4"),
                    "close_price": Decimal("142"),
                    "direction": "up",
                }
            ]
        }
    )

    monkeypatch.setattr(dynamodb_reader, "get_table", lambda: fake_table)

    result = get_recent_movers(limit=1)

    assert len(result) == 1
    assert result[0]["ticker"] == "NVDA"
    assert fake_table.query_kwargs["Limit"] == 1


def test_decode_cursor_rejects_non_dict_payload():
    payload = json.dumps(["not", "a", "dict"]).encode("utf-8")
    cursor = base64.urlsafe_b64encode(payload).decode("utf-8")

    with pytest.raises(InvalidCursorError, match="invalid pagination cursor"):
        decode_cursor(cursor)