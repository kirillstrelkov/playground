from stocks.buy_sell_analysis.analysis_base_first_date import (
    Column,
    get_best_hour,
    get_best_month,
    get_best_month_day,
    get_best_quarter,
    get_best_time,
    get_best_week,
    get_best_weekday,
    get_best_year_day,
)
from stocks.buy_sell_analysis.common import YahooRange, get_date_column_name

FILENAME = "sp500/sp500.csv"
LIMIT = 5


def test_best_month():
    df = get_best_month(FILENAME, YahooRange.YEARS_10, limit=LIMIT)
    df_year = df[df[Column.YEAR] == 2020]
    assert not df_year.empty
    assert (
        df_year[df_year[Column.MONTH] == 1][Column.PERCENT].mean()
        < df_year[df_year[Column.MONTH] == 11][Column.PERCENT].mean()
    )


def test_best_month_day():
    df = get_best_month_day(FILENAME, YahooRange.YEARS_2, limit=LIMIT)
    df_jan = df[df[Column.MONTH] == 7]
    assert not df_jan.empty
    assert (
        df_jan[df_jan[Column.DAY] == 1][Column.PERCENT].mean()
        < df_jan[df_jan[Column.DAY] == 31][Column.PERCENT].mean()
    )


def test_best_weekday():
    df = get_best_weekday(FILENAME, YahooRange.YEARS_2, limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.WEEKDAY] == 0][Column.PERCENT].mean()
        < df[df[Column.WEEKDAY] == 2][Column.PERCENT].mean()
    )


def test_best_hour():
    df = get_best_hour(FILENAME, YahooRange.DAYS_58, limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.HOUR] == 9][Column.PERCENT].mean()
        < df[df[Column.HOUR] == 15][Column.PERCENT].mean()
    )


def test_best_15mins():
    df = get_best_quarter(
        FILENAME,
        YahooRange.DAYS_58,
        limit=LIMIT,
    )
    assert not df.empty
    assert (
        df[df[Column.QUARTER] == 15][Column.PERCENT].mean()
        < df[df[Column.QUARTER] == 45][Column.PERCENT].mean()
    )
    assert df[Column.QUARTER].unique() == [0, 15, 30, 45]


def test_best_time_hour_and_minute():
    df = get_best_time(FILENAME, YahooRange.DAYS_58, limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.TIME] == 10.0][Column.PERCENT].mean()
        < df[df[Column.TIME] == 13.0][Column.PERCENT].mean()
    )
    assert df[Column.MINUTE].unique() == [0, 30]


def test_best_week():
    df = get_best_week(FILENAME, YahooRange.YEARS_2, limit=LIMIT)
    assert not df.empty
    assert (
        df[df[Column.WEEK] == 15][Column.PERCENT].mean()
        < df[df[Column.WEEK] == 40][Column.PERCENT].mean()
    )


def test_year_day():
    df = get_best_year_day(FILENAME, YahooRange.YEARS_2, limit=LIMIT)
    date_column_name = get_date_column_name(df)
    assert not df.empty
    assert (
        df[df[date_column_name] == df[date_column_name].min()][Column.PERCENT].mean()
        < df[df[date_column_name] == df[date_column_name].max()][Column.PERCENT].mean()
    )
