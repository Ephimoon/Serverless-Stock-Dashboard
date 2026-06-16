# gets open and close prices

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests

from common.config import LOOKBACK_DAYS, MASSIVE_BASE_URL, WATCHLIST


REQUEST_DELAY_SECONDS = 13
MARKET_CLOSE_BUFFER_HOUR = 18


class StockApiError(Exception):
    """raised when the stock API cannot return usable data."""


class MarketDateUnavailableError(StockApiError):
    """raised when a market date is not available from the stock API."""


class RateLimitError(StockApiError):
    """raised when the stock API rate limit is reached."""


def get_recent_market_dates(days_back: int = LOOKBACK_DAYS) -> list[str]:
    eastern_now = datetime.now(ZoneInfo("America/New_York"))
    current_day = eastern_now.date()

    if eastern_now.weekday() < 5 and eastern_now.hour >= MARKET_CLOSE_BUFFER_HOUR:
        offset = 0
    else:
        offset = 1

    market_dates: list[str] = []

    while len(market_dates) < days_back:
        candidate = current_day - timedelta(days=offset)

        if candidate.weekday() < 5:
            market_dates.append(candidate.isoformat())

        offset += 1

    return market_dates


def wait_between_requests(index: int) -> None:
    if index > 0:
        print(f"waiting {REQUEST_DELAY_SECONDS} seconds before next stock API request")
        time.sleep(REQUEST_DELAY_SECONDS)


def fetch_daily_open_close(
    ticker: str,
    market_date: str,
    api_key: str,
    max_retries: int = 1,
    timeout_seconds: int = 5,
) -> dict[str, Any]:
    url = f"{MASSIVE_BASE_URL}/v1/open-close/{ticker}/{market_date}"

    params = {
        "adjusted": "true",
        "apiKey": api_key,
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(f"requesting stock API data for {ticker} on {market_date}")
            response = requests.get(url, params=params, timeout=timeout_seconds)

            if response.status_code == 403:
                raise MarketDateUnavailableError(
                    f"stock API access forbidden for {ticker} on {market_date}. "
                    "This usually means the market date is not available yet."
                )

            if response.status_code == 429:
                raise RateLimitError(f"stock API rate limit reached for {ticker} on {market_date}")

            if 500 <= response.status_code < 600:
                print(
                    f"stock API server issue for {ticker} on {market_date}. "
                    f"status {response.status_code}. attempt {attempt}/{max_retries}."
                )

                if attempt < max_retries:
                    time.sleep(REQUEST_DELAY_SECONDS)
                    continue

                raise StockApiError(f"stock API server error for {ticker} on {market_date}")

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
            print(
                f"timeout fetching {ticker} on {market_date}. "
                f"attempt {attempt}/{max_retries}."
            )

            if attempt == max_retries:
                raise StockApiError(f"timed out fetching {ticker} on {market_date}") from error

            time.sleep(REQUEST_DELAY_SECONDS)

        except requests.RequestException as error:
            raise StockApiError(f"request failed for {ticker} on {market_date}") from error

    raise StockApiError(f"failed to fetch {ticker} on {market_date}")


def fetch_watchlist_data(api_key: str, watchlist: list[str] | None = None) -> list[dict[str, Any]]:
    api_key = (api_key or "").strip()

    if not api_key:
        raise StockApiError("missing stock API key")

    tickers = WATCHLIST if watchlist is None else watchlist

    if not tickers:
        return []

    market_dates = get_recent_market_dates()
    request_index = 0

    for market_date in market_dates:
        valid_records: list[dict[str, Any]] = []
        market_date_unavailable = False

        for ticker in tickers:
            wait_between_requests(request_index)

            try:
                record = fetch_daily_open_close(
                    ticker=ticker,
                    market_date=market_date,
                    api_key=api_key,
                )
                valid_records.append(record)

            except MarketDateUnavailableError as error:
                print(f"market date {market_date} is unavailable. error: {error}")
                market_date_unavailable = True

            except RateLimitError:
                print(f"rate limit reached while fetching {ticker} for {market_date}")
                raise

            except StockApiError as error:
                print(f"failed to fetch {ticker} for {market_date}. error: {error}")

            request_index += 1

            if market_date_unavailable:
                break

        if valid_records:
            return valid_records

        print(f"no valid records for {market_date}, trying previous market date")

    return []
