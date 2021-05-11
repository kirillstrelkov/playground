from stocks.buy_sell_analysis.analysis_base_first_date import (
    Column,
    get_best_hour,
    get_best_month,
    get_best_month_day,
    get_best_quarter,
    get_best_time,
    get_best_weekday,
)

START_DATE = "2019-02-01"
END_DATE = "2021-01-01"
FILENAME = "sp500.csv"
LIMIT = 5


def test_best_month():
    df = get_best_month(FILENAME, START_DATE, END_DATE, limit=LIMIT)
    df2018 = df[df[Column.YEAR] == 2020]
    assert not df2018.empty
    assert (
        df2018[df2018[Column.MONTH] == 1][Column.PERCENT].mean()
        < df2018[df2018[Column.MONTH] == 11][Column.PERCENT].mean()
    )


def test_best_month_day():
    df = get_best_month_day(FILENAME, START_DATE, END_DATE, limit=LIMIT)
    df_jan = df[df[Column.MONTH] == 7]
    assert not df_jan.empty
    assert (
        df_jan[df_jan[Column.DAY] == 1][Column.PERCENT].mean()
        < df_jan[df_jan[Column.DAY] == 31][Column.PERCENT].mean()
    )


def test_best_weekday():
    df = get_best_weekday(FILENAME, START_DATE, END_DATE, limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.WEEKDAY] == 0][Column.PERCENT].mean()
        < df[df[Column.WEEKDAY] == 2][Column.PERCENT].mean()
    )


def test_best_hour():
    df = get_best_hour(FILENAME, "2021-04-01", "2021-05-01", limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.HOUR] == 9][Column.PERCENT].mean()
        < df[df[Column.HOUR] == 15][Column.PERCENT].mean()
    )


def test_best_15mins():
    df = get_best_quarter(
        FILENAME,
        "2021-04-01",
        "2021-05-01",
        limit=LIMIT,
    )
    assert not df.empty
    assert (
        df[df[Column.QUARTER] == 0][Column.PERCENT].mean()
        < df[df[Column.QUARTER] == 45][Column.PERCENT].mean()
    )


def test_best_time_hour_and_minute():
    df = get_best_time(FILENAME, "2021-04-01", "2021-05-01", limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.TIME] == 9.5][Column.PERCENT].mean()
        < df[df[Column.TIME] == 10.5][Column.PERCENT].mean()
    )
