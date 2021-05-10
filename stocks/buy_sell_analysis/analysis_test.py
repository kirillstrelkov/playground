import pytest
from stocks.buy_sell_analysis.analysis import (
    get_best_month,
    get_best_month_day,
    get_best_weekday,
)


def test_best_month():
    df = get_best_month("sp500.csv", limit=5)
    df2018 = df[df["year"] == 2018]
    assert not df2018.empty
    assert (
        df2018[df2018["month"] == 1]["diff"].mean()
        < df2018[df2018["month"] == 11]["diff"].mean()
    )


def test_best_month_day():
    df = get_best_month_day("sp500.csv", limit=5)
    df_jan = df[df["month"] == 7]
    assert not df_jan.empty
    assert (
        df_jan[df_jan["day"] == 1]["diff"].mean()
        < df_jan[df_jan["day"] == 31]["diff"].mean()
    )


def test_best_weekday():
    df = get_best_weekday("sp500.csv", limit=5)
    assert not df.empty
    assert df[df["weekday"] == 0]["diff"].mean() < df[df["weekday"] == 4]["diff"].mean()


@pytest.mark.skip(reason="wip")
def test_best_hour():
    pass


@pytest.mark.skip(reason="wip")
def test_best_15mins():
    pass


@pytest.mark.skip(reason="wip")
def test_best_time_hour_and_minute():
    pass
