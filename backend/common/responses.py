import json
from decimal import Decimal
from typing import Any


DEFAULT_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Cache-Control": "public, max-age=300",
    "Content-Type": "application/json",
    "X-Data-Source": "dynamodb",
}


def json_default(value: Any):
    if isinstance(value, Decimal):
        return float(value)

    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def json_response(status_code: int, body: dict[str, Any], headers: dict[str, str] | None = None):
    response_headers = DEFAULT_HEADERS.copy()

    if headers:
        response_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": json.dumps(body, default=json_default),
    }