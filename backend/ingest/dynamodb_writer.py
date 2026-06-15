# saves the winning stock result

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3

from common.config import AWS_REGION, TABLE_NAME

def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return dynamodb.Table(TABLE_NAME)

def to_decimal(value: float) -> Decimal:
    return Decimal(str(value))

def build_winner_item(winner: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "DAILY_WINNER",
        "date": winner["date"],
        "ticker": winner["ticker"],
        "percent_change": to_decimal(winner["percent_change"]),
        "close_price": to_decimal(winner["close_price"]),
        "direction": winner["direction"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

def save_winner(winner: dict[str, Any], table=None) -> dict[str, Any]:
    if table is None:
        table = get_table()
    item = build_winner_item(winner)

    table.put_item(Item=item)

    print(f"Saved record to DynamoDB for {item['ticker']} on {item['date']}")

    return item