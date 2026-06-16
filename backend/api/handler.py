from api.dynamodb_reader import InvalidCursorError, get_recent_movers_page
from common.responses import json_response


DEFAULT_LIMIT = 7
MAX_LIMIT = 30


def get_query_params(event):
    return event.get("queryStringParameters") or {}


def get_limit(params):
    raw_limit = params.get("limit", str(DEFAULT_LIMIT))

    try:
        limit = int(raw_limit)
    except ValueError as error:
        raise ValueError("limit must be a number") from error

    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")

    return limit


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    legacy_method = event.get("httpMethod")
    request_method = method or legacy_method or "GET"

    if request_method == "OPTIONS":
        return json_response(200, {"message": "cors preflight ok"})

    if request_method != "GET":
        return json_response(405, {"message": "method not allowed"})

    print(f"{request_method} /movers request received")

    try:
        params = get_query_params(event)
        limit = get_limit(params)
        cursor = params.get("cursor")

        page = get_recent_movers_page(limit=limit, cursor=cursor)

        print(f"returned {page['count']} mover records")

        headers = {
            "X-Result-Count": str(page["count"]),
            "X-Page-Limit": str(page["limit"]),
        }

        if page["next_cursor"]:
            headers["X-Next-Cursor"] = page["next_cursor"]

        return json_response(200, page, headers=headers)

    except ValueError as error:
        print(f"invalid pagination request: {error}")
        return json_response(400, {"message": str(error)})

    except InvalidCursorError:
        print("invalid pagination cursor")
        return json_response(400, {"message": "invalid pagination cursor"})

    except Exception as error:
        print(f"failed to load movers: {error}")
        return json_response(500, {"message": "could not load movers"})
