import pytest
from stocks.buy_sell_analysis.analysis import (
    Column,
    get_best_month,
    get_best_month_day,
    get_best_weekday,
)


def test_best_month():
    df = get_best_month("sp500.csv", limit=5)
    df2018 = df[df[Column.YEAR] == 2018]
    assert not df2018.empty
    assert (
        df2018[df2018[Column.MONTH] == 1][Column.PERCENT].mean()
        < df2018[df2018[Column.MONTH] == 11][Column.PERCENT].mean()
    )


def test_best_month_day():
    df = get_best_month_day("sp500.csv", limit=5)
    df_jan = df[df[Column.MONTH] == 7]
    assert not df_jan.empty
    assert (
        df_jan[df_jan[Column.DAY] == 1][Column.PERCENT].mean()
        < df_jan[df_jan[Column.DAY] == 31][Column.PERCENT].mean()
    )


def test_best_weekday():
    df = get_best_weekday("sp500.csv", limit=5)
    assert not df.empty
    assert (
        df[df[Column.WEEKDAY] == 0][Column.PERCENT].mean()
        < df[df[Column.WEEKDAY] == 4][Column.PERCENT].mean()
    )


@pytest.mark.skip(reason="wip")
def test_best_hour():
    pass


@pytest.mark.skip(reason="wip")
def test_best_15mins():
    pass


@pytest.mark.skip(reason="wip")
def test_best_time_hour_and_minute():
    pass
