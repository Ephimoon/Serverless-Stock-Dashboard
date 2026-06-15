from api.dynamodb_reader import get_recent_movers
from common.responses import json_response


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
        movers = get_recent_movers(limit=7)

        print(f"returned {len(movers)} mover records")

        return json_response(
            200,
            {
                "items": movers,
                "count": len(movers),
            },
            headers={
                "X-Result-Count": str(len(movers)),
            },
        )

    except Exception as error:
        print(f"failed to load movers: {error}")

        return json_response(
            500,
            {
                "message": "could not load movers",
            },
        )