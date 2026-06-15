import os

WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]

MASSIVE_BASE_URL = os.environ.get("MASSIVE_BASE_URL", "https://api.massive.com")
STOCK_API_KEY = os.environ.get("STOCK_API_KEY", "")
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "7"))

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
TABLE_NAME = os.environ.get("TABLE_NAME", "stock_movers")
SECRET_NAME = os.environ.get("SECRET_NAME", "stock-dashboard/api-key")