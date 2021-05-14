import os

import pandas as pd
from stocks.buy_sell_analysis.common import (
    Column,
    YahooRange,
    get_date_column_name,
    update_dataframe,
    wrapper,
)


def __get_symbols(filename, limit):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename))
    symbols = df[Column.SYMBOL]

    if limit:
        symbols = symbols[:limit]

    return symbols


def _get_best_weekday_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol, True)

    return df[[Column.YEAR, Column.WEEK, Column.WEEKDAY, Column.PERCENT]]


def get_best_weekday(filename: str, yahoo_range: YahooRange, limit=None):
    return wrapper(filename, yahoo_range, limit, _get_best_weekday_diffs)


def _get_monthly_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol, True)

    return df[[Column.YEAR, Column.MONTH, Column.SYMBOL, Column.PERCENT]]


def get_best_month(filename: str, yahoo_range: YahooRange, limit=None):
    return wrapper(filename, yahoo_range, limit, _get_monthly_diffs, interval="1mo")


def _get_month_day_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol, True)

    return df[[Column.YEAR, Column.MONTH, Column.DAY, Column.SYMBOL, Column.PERCENT]]


def get_best_month_day(filename: str, yahoo_range: YahooRange, limit=None):
    return wrapper(filename, yahoo_range, limit, _get_month_day_diffs)


def _get_hour_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df_history = df_symbols[Column.HISTORY]

    df = update_dataframe(df_history, symbol, True)

    return df[
        [
            Column.YEAR,
            Column.WEEK,
            Column.DAY,
            Column.HOUR,
            Column.SYMBOL,
            Column.PERCENT,
        ]
    ]


def get_best_hour(filename: str, yahoo_range: YahooRange, limit=None):
    return wrapper(
        filename,
        yahoo_range,
        limit,
        _get_hour_diffs,
        interval="60m",
    )


def _get_quarter_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df_history = df_symbols[Column.HISTORY]

    df = update_dataframe(df_history, symbol, True)

    df[Column.QUARTER] = df[Column.MINUTE]
    return df[
        [
            Column.YEAR,
            Column.WEEK,
            Column.DAY,
            Column.HOUR,
            Column.MINUTE,
            Column.QUARTER,
            Column.SYMBOL,
            Column.PERCENT,
        ]
    ]


def get_best_quarter(filename: str, yahoo_range: YahooRange, limit=None):
    # The requested range must be within the last 60 days.
    return wrapper(
        filename,
        yahoo_range,
        limit,
        _get_quarter_diffs,
        interval="15m",
    )


def _get_time_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df_history = df_symbols[Column.HISTORY]

    df = update_dataframe(df_history, symbol, True)

    df[Column.TIME] = df.apply(lambda x: x[Column.HOUR] + x[Column.MINUTE] / 60, axis=1)

    return df[
        [
            Column.YEAR,
            Column.WEEK,
            Column.DAY,
            Column.HOUR,
            Column.MINUTE,
            Column.TIME,
            Column.SYMBOL,
            Column.PERCENT,
        ]
    ]


def get_best_time(filename: str, yahoo_range: YahooRange, limit=None):
    # The requested range must be within the last 60 days.
    return wrapper(
        filename,
        yahoo_range,
        limit,
        _get_time_diffs,
        interval="15m",
    )


def _get_week_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol, True)

    return df[
        [
            Column.YEAR,
            Column.WEEK,
            Column.SYMBOL,
            Column.PERCENT,
        ]
    ]


def get_best_week(filename: str, yahoo_range: YahooRange, limit=None):
    # The requested range must be within the last 60 days.
    return wrapper(
        filename,
        yahoo_range,
        limit,
        _get_week_diffs,
        interval="1wk",
    )


def _get_year_day_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol, True)
    date_column_name = get_date_column_name(df)

    return df[
        [
            date_column_name,
            Column.YEAR,
            Column.MONTH,
            Column.SYMBOL,
            Column.PERCENT,
        ]
    ]


def get_best_year_day(filename: str, yahoo_range: YahooRange, limit=None):
    # The requested range must be within the last 60 days.
    return wrapper(
        filename,
        yahoo_range,
        limit,
        _get_year_day_diffs,
        interval="1d",
    )
