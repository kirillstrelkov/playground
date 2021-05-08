import pytest
from stocks.buy_sell_analysis.analysis import get_best_month, get_best_weekday


def test_best_month():
    df = get_best_month("sp500.csv", limit=5)
    assert "January" in df.index
    assert df.loc["January"]["diff"] == 100.0
    assert df.loc["November"]["diff"] > 100.0


@pytest.mark.skip(reason="wip")
def test_best_month_day():
    pass


def test_best_weekday():
    df = get_best_weekday("sp500.csv", limit=5)
    assert "Monday" in df.index
    assert df.loc["Monday"]["diff"] == 100.0
    assert df.loc["Friday"]["diff"] > 100.0


@pytest.mark.skip(reason="wip")
def test_best_hour():
    pass


@pytest.mark.skip(reason="wip")
def test_best_15mins():
    pass


@pytest.mark.skip(reason="wip")
def test_best_time_hour_and_minute():
    pass
