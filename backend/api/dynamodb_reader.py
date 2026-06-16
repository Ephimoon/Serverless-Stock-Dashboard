from __future__ import annotations

import base64
import json
from binascii import Error as Base64Error
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from common.config import AWS_REGION, TABLE_NAME


class InvalidCursorError(Exception):
    """raised when the pagination cursor cannot be decoded."""


def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return dynamodb.Table(TABLE_NAME)


def to_float(value: Any) -> float:
    return float(value)


def encode_cursor(last_evaluated_key: dict[str, Any] | None) -> str | None:
    if not last_evaluated_key:
        return None

    payload = json.dumps(last_evaluated_key, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def decode_cursor(cursor: str | None) -> dict[str, Any] | None:
    if not cursor:
        return None

    try:
        payload = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        decoded = json.loads(payload)
    except (Base64Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidCursorError("invalid pagination cursor") from error

    if not isinstance(decoded, dict):
        raise InvalidCursorError("invalid pagination cursor")

    if set(decoded.keys()) != {"record_type", "date"}:
        raise InvalidCursorError("invalid pagination cursor")

    if not isinstance(decoded.get("record_type"), str) or not isinstance(decoded.get("date"), str):
        raise InvalidCursorError("invalid pagination cursor")

    return decoded


def normalize_mover_item(item: dict[str, Any]) -> dict[str, Any]:
    percent_change = to_float(item["percent_change"])

    return {
        "date": item["date"],
        "ticker": item["ticker"],
        "percent_change": percent_change,
        "close_price": to_float(item["close_price"]),
        "direction": item.get("direction", "up" if percent_change >= 0 else "down"),
    }


def get_recent_movers_page(
    limit: int = 7,
    cursor: str | None = None,
    table=None,
) -> dict[str, Any]:
    if table is None:
        table = get_table()

    query_args: dict[str, Any] = {
        "KeyConditionExpression": Key("record_type").eq("DAILY_WINNER"),
        "ScanIndexForward": False,
        "Limit": limit,
    }

    start_key = decode_cursor(cursor)

    if start_key:
        query_args["ExclusiveStartKey"] = start_key

    response = table.query(**query_args)
    items = response.get("Items", [])
    next_cursor = encode_cursor(response.get("LastEvaluatedKey"))

    return {
        "items": [normalize_mover_item(item) for item in items],
        "count": len(items),
        "limit": limit,
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None,
    }


def get_recent_movers(limit: int = 7, table=None) -> list[dict[str, Any]]:
    return get_recent_movers_page(limit=limit, table=table)["items"]
