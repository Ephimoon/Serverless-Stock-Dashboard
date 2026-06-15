import json
from datetime import datetime, timezone


def lambda_handler(event, context):
    print("Started daily stock scan")
    print("Finished placeholder ingestion run")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Ingestion Lambda placeholder is working",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    }