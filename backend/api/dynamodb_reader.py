from __future__ import annotations

from decimal import Decimal
from typing import Any

import boto3

from common.config import AWS_REGION, TABLE_NAME


def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return dynamodb.Table(TABLE_NAME)


def to_float(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)

    return float(value)


def normalize_mover_item(item: dict[str, Any]) -> dict[str, Any]:
    percent_change = to_float(item["percent_change"])

    return {
        "date": item["date"],
        "ticker": item["ticker"],
        "percent_change": percent_change,
        "close_price": to_float(item["close_price"]),
        "direction": item.get("direction", "up" if percent_change >= 0 else "down"),
    }


def get_recent_movers(limit: int = 7, table=None) -> list[dict[str, Any]]:
    table = table or get_table()

    response = table.scan()
    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    normalized_items = [normalize_mover_item(item) for item in items]
    sorted_items = sorted(normalized_items, key=lambda item: item["date"], reverse=True)

    return sorted_items[:limit]