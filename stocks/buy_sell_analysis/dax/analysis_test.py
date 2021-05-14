from stocks.buy_sell_analysis.analysis import (
    Column,
    get_best_hour,
    get_best_month,
    get_best_month_day,
    get_best_quarter,
    get_best_time,
    get_best_week,
    get_best_weekday,
)
from stocks.buy_sell_analysis.common import _get_symbols

START_DATE = "2019-01-01"
END_DATE = "2021-01-01"
FILENAME = "dax/dax_mdax_sdax.csv"
LIMIT = 5


def test_best_month():
    df = get_best_month(FILENAME, START_DATE, END_DATE, limit=LIMIT)
    df2018 = df[df[Column.YEAR] == 2020]
    assert not df2018.empty
    assert (
        df2018[df2018[Column.MONTH] == 4][Column.PERCENT].mean()
        < df2018[df2018[Column.MONTH] == 11][Column.PERCENT].mean()
    )


def test_best_month_day():
    df = get_best_month_day(FILENAME, START_DATE, END_DATE, limit=LIMIT)
    df_jan = df[df[Column.MONTH] == 7]
    assert not df_jan.empty
    assert (
        df_jan[df_jan[Column.DAY] == 1][Column.PERCENT].mean()
        < df_jan[df_jan[Column.DAY] == 27][Column.PERCENT].mean()
    )


def test_best_weekday():
    df = get_best_weekday(FILENAME, START_DATE, END_DATE, limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.WEEKDAY] == 4][Column.PERCENT].mean()
        < df[df[Column.WEEKDAY] == 2][Column.PERCENT].mean()
    )


def test_best_hour():
    df = get_best_hour(FILENAME, "2021-04-01", "2021-05-01", limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.HOUR] == 15][Column.PERCENT].mean()
        < df[df[Column.HOUR] == 13][Column.PERCENT].mean()
    )


def test_best_15mins():
    df = get_best_quarter(
        FILENAME, limit=LIMIT, start_date="2021-04-01", end_date="2021-05-01"
    )
    assert not df.empty
    assert (
        df[df[Column.QUARTER] == 45][Column.PERCENT].mean()
        < df[df[Column.QUARTER] == 15][Column.PERCENT].mean()
    )


def test_best_time_hour_and_minute():
    df = get_best_time(
        FILENAME, limit=LIMIT, start_date="2021-04-01", end_date="2021-05-01"
    )
    assert not df.empty
    assert (
        df[df[Column.TIME] == 15.0][Column.PERCENT].mean()
        < df[df[Column.TIME] == 13.0][Column.PERCENT].mean()
    )


def test_best_week():
    df = get_best_week(FILENAME, limit=LIMIT, start_date=START_DATE, end_date=END_DATE)
    assert not df.empty
    assert (
        df[df[Column.WEEK] == 15][Column.PERCENT].mean()
        < df[df[Column.WEEK] == 40][Column.PERCENT].mean()
    )


def test_symbols():
    # check that network request is used only once
    for _ in range(100):
        symbols = _get_symbols(FILENAME, None)
        assert symbols
        assert len(symbols) == 160
