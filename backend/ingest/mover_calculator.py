# chooses the top mover

from typing import Any

def calculate_percent_change(open_price: float, close_price: float) -> float:
    if open_price <= 0:
        raise ValueError("open price must be greater than 0")

    percent_change = ((close_price - open_price) / open_price) * 100
    return round(percent_change, 4)

def get_direction(percent_change: float) -> str:
    return "up" if percent_change >= 0 else "down"

def select_top_mover(stock_records: list[dict[str, Any]]) -> dict[str, Any]:
    if not stock_records:
        raise ValueError("no valid stock records were provided")

    movers = []

    for record in stock_records:
        ticker = record["ticker"]
        open_price = float(record["open_price"])
        close_price = float(record["close_price"])
        date = record["date"]

        percent_change = calculate_percent_change(open_price, close_price)

        movers.append(
            {
                "date": date,
                "ticker": ticker,
                "percent_change": percent_change,
                "close_price": round(close_price, 4),
                "direction": get_direction(percent_change),
            }
        )

    return max(movers, key=lambda mover: abs(mover["percent_change"]))