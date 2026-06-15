from decimal import Decimal

from ingest import dynamodb_writer

from ingest.dynamodb_writer import build_winner_item, save_winner, to_decimal

class FakeTable:
    def __init__(self):
        self.saved_item = None

    def put_item(self, Item):
        self.saved_item = Item
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

def test_to_decimal_converts_float_to_decimal():
    result = to_decimal(3.41)

    assert result == Decimal("3.41")

def test_build_winner_item_formats_dynamodb_record():
    winner = {
        "date": "2026-06-12",
        "ticker": "NVDA",
        "percent_change": 3.41,
        "close_price": 142.53,
        "direction": "up",
    }

    item = build_winner_item(winner)

    assert item["date"] == "2026-06-12"
    assert item["ticker"] == "NVDA"
    assert item["percent_change"] == Decimal("3.41")
    assert item["close_price"] == Decimal("142.53")
    assert item["direction"] == "up"
    assert "created_at" in item

def test_save_winner_writes_item_to_table():
    fake_table = FakeTable()

    winner = {
        "date": "2026-06-12",
        "ticker": "TSLA",
        "percent_change": -6.0,
        "close_price": 94.0,
        "direction": "down",
    }

    saved_item = save_winner(winner, table=fake_table)

    assert fake_table.saved_item == saved_item
    assert saved_item["ticker"] == "TSLA"
    assert saved_item["percent_change"] == Decimal("-6.0")

def test_get_table_returns_configured_dynamodb_table(monkeypatch):
    class FakeDynamoDBResource:
        def __init__(self):
            self.table_name = None

        def Table(self, table_name):
            self.table_name = table_name
            return {"table_name": table_name}

    fake_resource = FakeDynamoDBResource()

    def fake_boto3_resource(service_name, region_name):
        assert service_name == "dynamodb"
        assert region_name == dynamodb_writer.AWS_REGION
        return fake_resource

    monkeypatch.setattr(dynamodb_writer.boto3, "resource", fake_boto3_resource)

    table = dynamodb_writer.get_table()

    assert table == {"table_name": dynamodb_writer.TABLE_NAME}