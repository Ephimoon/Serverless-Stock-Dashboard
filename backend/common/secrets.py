import json
import os

import boto3

from common.config import AWS_REGION, SECRET_NAME


class SecretError(Exception):
    """raised when the stock API key cannot be loaded."""


def get_stock_api_key() -> str:
    local_key = os.environ.get("STOCK_API_KEY", "").strip()

    if local_key and local_key not in {"placeholder", "your_key_here", "your_stock_api_key_here"}:
        return local_key

    if not SECRET_NAME:
        raise SecretError("missing SECRET_NAME for Secrets Manager lookup")

    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        response = client.get_secret_value(SecretId=SECRET_NAME)
        secret_string = response.get("SecretString", "")

        if not secret_string:
            raise SecretError("secret_string was empty")

        try:
            secret_payload = json.loads(secret_string)

            for key_name in ["STOCK_API_KEY", "MASSIVE_API_KEY", "apiKey"]:
                if secret_payload.get(key_name):
                    return secret_payload[key_name]

            raise SecretError("secret did not contain a supported API key field")

        except json.JSONDecodeError:
            return secret_string

    except Exception as error:
        raise SecretError(f"failed to load stock API key: {error}") from error