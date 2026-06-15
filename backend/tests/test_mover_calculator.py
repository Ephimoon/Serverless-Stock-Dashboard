import pytest

from ingest.mover_calculator import calculate_percent_change, select_top_mover


def test_calculate_percent_change_for_gain():
    result = calculate_percent_change(open_price=100, close_price=105)

    assert result == 5.0


def test_calculate_percent_change_for_loss():
    result = calculate_percent_change(open_price=100, close_price=92)

    assert result == -8.0


def test_calculate_percent_change_rejects_zero_open_price():
    with pytest.raises(ValueError, match="open price must be greater than 0"):
        calculate_percent_change(open_price=0, close_price=100)


def test_select_top_mover_uses_absolute_percent_change():
    records = [
        {
            "date": "2026-06-12",
            "ticker": "AAPL",
            "open_price": 100,
            "close_price": 103,
        },
        {
            "date": "2026-06-12",
            "ticker": "TSLA",
            "open_price": 100,
            "close_price": 94,
        },
        {
            "date": "2026-06-12",
            "ticker": "NVDA",
            "open_price": 100,
            "close_price": 104,
        },
    ]

    winner = select_top_mover(records)

    assert winner["ticker"] == "TSLA"
    assert winner["percent_change"] == -6.0
    assert winner["direction"] == "down"


def test_select_top_mover_rejects_empty_records():
    with pytest.raises(ValueError, match="no valid stock records were provided"):
        select_top_mover([])