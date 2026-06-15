import json
from datetime import datetime, timezone


def lambda_handler(event, context):
    print("GET /movers request received")
    print("Returned placeholder movers response")

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps({
            "items": [],
            "message": "API Lambda placeholder is working",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    }