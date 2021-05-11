import os

import pandas as pd
from stocks.buy_sell_analysis.common import Column, get_history, update_dataframe
from utils.misc import concurrent_map


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


def get_best_weekday(filename, start_date, end_date, limit=None):
    return __wrapper(filename, start_date, end_date, limit, _get_best_weekday_diffs)


def _get_monthly_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol, True)

    return df[[Column.YEAR, Column.MONTH, Column.SYMBOL, Column.PERCENT]]


def get_best_month(filename, start_date, end_date, limit=None):
    return __wrapper(
        filename, start_date, end_date, limit, _get_monthly_diffs, interval="1mo"
    )


def _get_month_day_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol, True)

    return df[[Column.YEAR, Column.MONTH, Column.DAY, Column.SYMBOL, Column.PERCENT]]


def get_best_month_day(filename, start_date, end_date, limit=None):
    return __wrapper(filename, start_date, end_date, limit, _get_month_day_diffs)


def __wrapper(filename, start_date, end_date, limit, func, interval="1d"):
    symbols = __get_symbols(filename, limit)

    history_data = get_history(symbols.values.tolist(), start_date, end_date, interval)
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
