# gets open and close prices

from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any

import requests

from common.config import LOOKBACK_DAYS, MASSIVE_BASE_URL, WATCHLIST


class StockApiError(Exception):
    """raised when the stock API cannot return usable data."""


def get_recent_market_dates(days_back: int = LOOKBACK_DAYS) -> list[str]:
    today = date.today()
    return [(today - timedelta(days=offset)).isoformat() for offset in range(days_back)]


def fetch_daily_open_close(
    ticker: str,
    market_date: str,
    api_key: str,
    max_retries: int = 3,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    url = f"{MASSIVE_BASE_URL}/v1/open-close/{ticker}/{market_date}"

    params = {
        "adjusted": "true",
        "apiKey": api_key,
    }

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout_seconds)

            if response.status_code == 429 or 500 <= response.status_code < 600:
                print(
                    f"rate limit or server issue for {ticker} on {market_date}. "
                    f"status {response.status_code}. attempt {attempt}/{max_retries}."
                )

                if attempt < max_retries:
                    time.sleep(2 ** (attempt - 1))
                    continue

            response.raise_for_status()
            payload = response.json()

            open_price = payload.get("open")
            close_price = payload.get("close")
            response_date = payload.get("from", market_date)
            symbol = payload.get("symbol", ticker)

            if open_price is None or close_price is None:
                raise StockApiError(f"missing open or close price for {ticker} on {market_date}")

            print(f"fetched {ticker} successfully for {response_date}")

            return {
                "date": response_date,
                "ticker": symbol,
                "open_price": float(open_price),
                "close_price": float(close_price),
            }

        except requests.Timeout as error:
            print(f"timeout fetching {ticker} on {market_date}. attempt {attempt}/{max_retries}. error: {error}")

            if attempt == max_retries:
                raise StockApiError(f"timed out fetching {ticker} on {market_date}") from error

            time.sleep(2 ** (attempt - 1))

        except requests.RequestException as error:
            raise StockApiError(f"request failed for {ticker} on {market_date}: {error}") from error

    raise StockApiError(f"failed to fetch {ticker} on {market_date}")


def fetch_watchlist_data(api_key: str, watchlist: list[str] | None = None) -> list[dict[str, Any]]:
    if not api_key:
        raise StockApiError("missing stock API key")

    tickers = watchlist or WATCHLIST
    market_dates = get_recent_market_dates()
    valid_records: list[dict[str, Any]] = []

    for ticker in tickers:
        ticker_was_fetched = False

        for market_date in market_dates:
            try:
                record = fetch_daily_open_close(ticker=ticker, market_date=market_date, api_key=api_key)
                valid_records.append(record)
                ticker_was_fetched = True
                break

            except StockApiError as error:
                print(f"failed to fetch {ticker} for {market_date}, trying next date if available. error: {error}")

        if not ticker_was_fetched:
            print(f"failed to fetch {ticker}, continuing with remaining watchlist")

    return valid_records