import json

from common.secrets import SecretError, get_stock_api_key
from ingest.dynamodb_writer import save_winner
from ingest.mover_calculator import select_top_mover
from ingest.stock_api import RateLimitError, StockApiError, fetch_watchlist_data


def lambda_handler(event, context):
    print("started daily stock scan")

    try:
        api_key = get_stock_api_key()
        stock_records = fetch_watchlist_data(api_key=api_key)

        if not stock_records:
            print("no valid stock records were returned from the stock API")

            return {
                "statusCode": 502,
                "body": json.dumps({
                    "message": "no valid stock records were available"
                }),
            }

        winner = select_top_mover(stock_records)

        print(f"winner selected: {winner['ticker']} with {winner['percent_change']}%")

        save_winner(winner)

        print("finished daily stock scan")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "daily stock mover saved successfully",
                "winner": winner,
            }),
        }

    except SecretError as error:
        print(f"secret error: {error}")

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "could not load stock API key"
            }),
        }

    except RateLimitError as error:
        print(f"rate limit error: {error}")

        return {
            "statusCode": 429,
            "body": json.dumps({
                "message": "stock API rate limit reached"
            }),
        }

    except StockApiError as error:
        print(f"stock API error: {error}")

        return {
            "statusCode": 502,
            "body": json.dumps({
                "message": "stock API request failed"
            }),
        }

    except Exception as error:
        print(f"unexpected ingestion error: {error}")

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "unexpected ingestion error"
            }),
        }