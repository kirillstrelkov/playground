import calendar
import os

import pandas as pd
import yfinance as yf
from loguru import logger
from pandas.core.frame import DataFrame
from utils.misc import concurrent_map


class Column(object):
    OPEN = "Open"
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    DAY_NAME = "day_name"
    MONTH_NAME = "month_name"
    WEEKDAY = "weekday"
    WEEK = "week"
    DATE = "Date"
    DATETIME = "Datetime"
    SYMBOL = "Symbol"
    PERCENT = "percent"
    HISTORY = "history"
    TIME = "time"
    QUARTER = "quarter"


__CACHE = {}


def __get_history(symbols, start_date, end_date, interval):
    key = (str(symbols), start_date, end_date, interval)
    if key not in __CACHE:
        __CACHE[key] = yf.download(
            symbols,
            interval=interval,
            start=start_date,
            end=end_date,
            group_by="ticker",
        )

    return __CACHE[key]


def __get_date_column_name(df):
    if Column.DATETIME in df.columns:
        return Column.DATETIME
    else:
        return Column.DATE


def __update_dataframe(df, symbol):
    df = df.reset_index()

    date_column = __get_date_column_name(df)
    df_date = df[date_column]
    for component in [
        Column.YEAR,
        Column.MONTH,
        Column.DAY,
        Column.HOUR,
        Column.MINUTE,
    ]:
        df[component] = df_date.apply(lambda x: getattr(x, component))

    df[Column.DAY_NAME] = df_date.apply(lambda x: x.day_name())
    df[Column.MONTH_NAME] = df_date.apply(lambda x: x.month_name())
    df[Column.WEEKDAY] = df_date.apply(lambda x: x.weekday())
    df[Column.WEEK] = df_date.apply(lambda x: x.isocalendar()[1])

    # Filteting NA in Open - this means usually a dividends
    df = df[df[Column.OPEN].notna()]

    df[Column.SYMBOL] = symbol

    # Set base value to first data point
    if not df.empty:
        first_price = df.sort_values(date_column).iloc[0][Column.OPEN]
        df[Column.PERCENT] = df[Column.OPEN] / first_price

    return df


def __get_symbols(filename, limit):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename))
    symbols = df[Column.SYMBOL]

    if limit:
        symbols = symbols[:limit]

    return symbols


def _get_best_weekday_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = __update_dataframe(df_symbols[Column.HISTORY], symbol)

    return df[[Column.YEAR, Column.WEEK, Column.WEEKDAY, Column.PERCENT]]


def get_best_weekday(filename, start_date, end_date, limit=None):
    return __wrapper(filename, start_date, end_date, limit, _get_best_weekday_diffs)


def _get_monthly_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = __update_dataframe(df_symbols[Column.HISTORY], symbol)

    return df[[Column.YEAR, Column.MONTH, Column.SYMBOL, Column.PERCENT]]


def get_best_month(filename, start_date, end_date, limit=None):
    return __wrapper(
        filename, start_date, end_date, limit, _get_monthly_diffs, interval="1mo"
    )


def _get_month_day_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = __update_dataframe(df_symbols[Column.HISTORY], symbol)

    return df[[Column.YEAR, Column.MONTH, Column.DAY, Column.SYMBOL, Column.PERCENT]]


def get_best_month_day(filename, start_date, end_date, limit=None):
    return __wrapper(filename, start_date, end_date, limit, _get_month_day_diffs)


def __wrapper(filename, start_date, end_date, limit, func, interval="1d"):
    symbols = __get_symbols(filename, limit)

    history_data = __get_history(
        symbols.values.tolist(), start_date, end_date, interval
    )
    symbols_with_history = [
        {Column.SYMBOL: symbol, Column.HISTORY: history_data[symbol]}
        for symbol in history_data.columns.get_level_values(0).unique().to_list()
    ]

    symbols_dfs = pd.concat(concurrent_map(func, symbols_with_history))

    symbols_dfs[Column.PERCENT] = symbols_dfs[Column.PERCENT] * 100

    symbols_dfs = symbols_dfs.convert_dtypes()

    return symbols_dfs


def _get_hour_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df_history = df_symbols[Column.HISTORY]

    df = __update_dataframe(df_history, symbol)

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


def get_best_hour(filename, start_date, end_date, limit=None):
    return __wrapper(
        filename,
        start_date,
        end_date,
        limit,
        _get_hour_diffs,
        interval="60m",
    )


def _get_quarter_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df_history = df_symbols[Column.HISTORY]

    df = __update_dataframe(df_history, symbol)

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


def get_best_quarter(filename, start_date, end_date, limit=None):
    # The requested range must be within the last 60 days.
    return __wrapper(
        filename,
        start_date,
        end_date,
        limit,
        _get_quarter_diffs,
        interval="15m",
    )


def _get_time_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df_history = df_symbols[Column.HISTORY]

    df = __update_dataframe(df_history, symbol)

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


def get_best_time(filename, start_date, end_date, limit=None):
    # The requested range must be within the last 60 days.
    return __wrapper(
        filename,
        start_date,
        end_date,
        limit,
        _get_time_diffs,
        interval="15m",
    )
