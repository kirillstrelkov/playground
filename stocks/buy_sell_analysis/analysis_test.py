import pytest
from stocks.buy_sell_analysis.analysis import get_best_weekday


@pytest.mark.skip(reason="wip")
def test_best_month():
    pass


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
def test_quaterly():
    pass


@pytest.mark.skip(reason="wip")
def test_best_time_hour_and_minute():
    pass
