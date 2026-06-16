import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
import urllib.error

WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
SECRET_NAME = "stock-dashboard/api-key"
TABLE_NAME = "serverless-stock-dashboard-movers"
BASE_URL = "https://api.massive.com"
REGION = "us-east-1"
REQUEST_DELAY_SECONDS = 13


def run_aws_command(args):
    result = subprocess.run(
        ["aws", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def get_api_key():
    response = run_aws_command([
        "secretsmanager",
        "get-secret-value",
        "--secret-id",
        SECRET_NAME,
        "--region",
        REGION,
    ])

    secret = json.loads(response["SecretString"])
    return secret["STOCK_API_KEY"].strip()


def fetch_daily_open_close(ticker, market_date, api_key):
    query = urllib.parse.urlencode({
        "adjusted": "true",
        "apiKey": api_key,
    })

    url = f"{BASE_URL}/v1/open-close/{ticker}/{market_date}?{query}"

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))

            open_price = float(data["open"])
            close_price = float(data["close"])
            percent_change = ((close_price - open_price) / open_price) * 100

            return {
                "date": market_date,
                "ticker": ticker,
                "percent_change": round(percent_change, 4),
                "close_price": round(close_price, 2),
                "direction": "up" if percent_change >= 0 else "down",
            }

        except (TimeoutError, urllib.error.URLError) as error:
            if attempt == 3:
                raise RuntimeError(f"{ticker} {market_date} timed out after 3 attempts") from error

            print(f"{ticker} {market_date} timed out, retrying attempt {attempt + 1}/3")
            time.sleep(15)


def save_winner(winner):
    item = {
        "record_type": {"S": "DAILY_WINNER"},
        "date": {"S": winner["date"]},
        "ticker": {"S": winner["ticker"]},
        "percent_change": {"N": str(winner["percent_change"])},
        "close_price": {"N": str(winner["close_price"])},
        "direction": {"S": winner["direction"]},
        "created_at": {"S": datetime.now(timezone.utc).isoformat()},
        "source": {"S": "manual_backfill"},
    }

    subprocess.run(
        [
            "aws",
            "dynamodb",
            "put-item",
            "--table-name",
            TABLE_NAME,
            "--item",
            json.dumps(item),
            "--region",
            REGION,
        ],
        check=True,
    )


def backfill_date(market_date, api_key):
    records = []

    print(f"\nBackfilling {market_date}")

    for index, ticker in enumerate(WATCHLIST):
        if index > 0:
            time.sleep(REQUEST_DELAY_SECONDS)

        record = fetch_daily_open_close(ticker, market_date, api_key)
        records.append(record)
        print(f"{ticker}: {record['percent_change']}% close ${record['close_price']}")

    winner = max(records, key=lambda item: abs(item["percent_change"]))
    save_winner(winner)

    print(f"Saved winner: {winner['ticker']} {winner['percent_change']}% close ${winner['close_price']}")


def main():
    dates = sys.argv[1:]

    if not dates:
        print("Usage: python backend/scripts/backfill_movers.py 2026-06-05 2026-06-08")
        raise SystemExit(1)

    api_key = get_api_key()

    for market_date in dates:
        backfill_date(market_date, api_key)


if __name__ == "__main__":
    main()