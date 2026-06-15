from decimal import Decimal

from api import dynamodb_reader
from api.dynamodb_reader import get_recent_movers, normalize_mover_item, to_float

class FakeTable:
    def __init__(self, responses):
        self.responses = responses
        self.scan_calls = []

    def scan(self, **kwargs):
        self.scan_calls.append(kwargs)
        return self.responses.pop(0)

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

def test_get_recent_movers_sorts_by_date_and_limits_results():
    fake_table = FakeTable(
        [
            {
                "Items": [
                    {
                        "date": "2026-06-10",
                        "ticker": "AAPL",
                        "percent_change": Decimal("1.2"),
                        "close_price": Decimal("100"),
                        "direction": "up",
                    },
                    {
                        "date": "2026-06-12",
                        "ticker": "NVDA",
                        "percent_change": Decimal("3.4"),
                        "close_price": Decimal("142"),
                        "direction": "up",
                    },
                    {
                        "date": "2026-06-11",
                        "ticker": "TSLA",
                        "percent_change": Decimal("-2.5"),
                        "close_price": Decimal("94"),
                        "direction": "down",
                    },
                ]
            }
        ]
    )

    result = get_recent_movers(limit=2, table=fake_table)

    assert [item["date"] for item in result] == ["2026-06-12", "2026-06-11"]

def test_get_recent_movers_reads_paginated_scan_results():
    fake_table = FakeTable(
        [
            {
                "Items": [
                    {
                        "date": "2026-06-10",
                        "ticker": "AAPL",
                        "percent_change": Decimal("1.2"),
                        "close_price": Decimal("100"),
                        "direction": "up",
                    }
                ],
                "LastEvaluatedKey": {"date": "2026-06-10"},
            },
            {
                "Items": [
                    {
                        "date": "2026-06-11",
                        "ticker": "MSFT",
                        "percent_change": Decimal("2.2"),
                        "close_price": Decimal("200"),
                        "direction": "up",
                    }
                ]
            },
        ]
    )

    result = get_recent_movers(limit=7, table=fake_table)

    assert len(result) == 2
    assert fake_table.scan_calls[1] == {"ExclusiveStartKey": {"date": "2026-06-10"}}

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