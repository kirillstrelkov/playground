import calendar
import os

import pandas as pd
import yfinance as yf
from loguru import logger
from pandas.core.frame import DataFrame
from utils.misc import concurrent_map

START_DATE = "2001-01-01"
START_DATE = "2011-01-01"
END_DATE = "2019-01-01"


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
    SYMBOL = "Symbol"
    PERCENT = "diff"
    HISTORY = "history"


def __get_history(symbols, interval):
    df = yf.download(
        symbols, interval=interval, start=START_DATE, end=END_DATE, group_by="ticker"
    )

    return df


def __update_dataframe(df):
    df = df.reset_index()

    for component in [
        Column.YEAR,
        Column.MONTH,
        Column.DAY,
        Column.HOUR,
        Column.MINUTE,
    ]:
        df[component] = df[Column.DATE].apply(lambda x: getattr(x, component))

    df[Column.DAY_NAME] = df[Column.DATE].apply(lambda x: x.day_name())
    df[Column.MONTH_NAME] = df[Column.DATE].apply(lambda x: x.month_name())
    df[Column.WEEKDAY] = df[Column.DATE].apply(lambda x: x.weekday())
    df[Column.WEEK] = df[Column.DATE].apply(lambda x: x.isocalendar()[1])

    # Filteting NA in Open - this means usually a dividends
    df = df[df[Column.OPEN].notna()]

    return df


def __get_symbols(filename, limit):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename))
    symbols = df[Column.SYMBOL]

    if limit:
        symbols = symbols[:limit]

    return symbols


def _get_best_weekday_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = __update_dataframe(df_symbols[Column.HISTORY])

    # if number of working days less than 3 - don't count
    number_of_good_working = 3

    # Filter columns
    df = df[[Column.YEAR, Column.WEEK, Column.WEEKDAY, Column.OPEN]]

    df_weeks = DataFrame()
    for year in df[Column.YEAR].unique():
        for week in df[Column.WEEK].unique():
            df_week = df[(df[Column.YEAR] == year) & (df[Column.WEEK] == week)]
            if df_week.empty:
                continue

            days = df_week[Column.WEEKDAY].values
            if df_week.shape[0] < number_of_good_working:
                # first and last week of year might contain only 1-2 days
                if week not in (1, 52, 53):
                    logger.debug(
                        f"Not enough data for {symbol} in {year} week {week}: {days}"
                    )
                continue

            first_weekday = df_week[Column.WEEKDAY].min()
            df_week[Column.PERCENT] = (
                df_week[Column.OPEN]
                / df_week[df_week[Column.WEEKDAY] == first_weekday].iloc[0][Column.OPEN]
            )
            assert (
                df_week.shape[0] >= number_of_good_working
            ), f"Wrong number of weekdays in dataframe {df_week.shape} for year {year} {week}: {days}"

            df_weeks = df_weeks.append(df_week)

    return df_weeks[[Column.YEAR, Column.WEEK, Column.WEEKDAY, Column.PERCENT]]


def get_best_weekday(filename, limit=None):
    return __wrapper(filename, limit, _get_best_weekday_diffs)


def _get_monthly_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = __update_dataframe(df_symbols[Column.HISTORY])

    df = df.groupby([Column.YEAR, Column.MONTH], as_index=False).mean()

    # Filter columns
    df = df[[Column.YEAR, Column.MONTH, Column.OPEN]]

    df_months = DataFrame()
    for year in df[Column.YEAR].unique():
        df_month = df[df[Column.YEAR] == year]
        if df_month.shape[0] < 12:
            logger.debug(f"Not enough data for {symbol} in {year}")
            continue

        first_month = df_month[Column.MONTH].min()
        df_month[Column.PERCENT] = (
            df_month[Column.OPEN]
            / df_month[df_month[Column.MONTH] == first_month].iloc[0][Column.OPEN]
        )
        assert (
            df_month.shape[0] == 12
        ), f"Wrong number of month in dataframe {df_month.shape} for year {year}"

        df_months = df_months.append(df_month)

    return df_months[[Column.YEAR, Column.MONTH, Column.PERCENT]]


def get_best_month(filename, limit=None):
    return __wrapper(filename, limit, _get_monthly_diffs)


def _get_month_day_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = __update_dataframe(df_symbols[Column.HISTORY])

    # Filter columns
    df = df[[Column.YEAR, Column.MONTH, Column.DAY, Column.OPEN]]

    df_months = DataFrame()
    for year in df[Column.YEAR].unique():
        for month in df[Column.MONTH].unique():
            df_month = df[(df[Column.YEAR] == year) & (df[Column.MONTH] == month)]
            if df_month.empty:
                continue
            first_day = df_month[Column.DAY].min()
            df_month[Column.PERCENT] = (
                df_month[Column.OPEN]
                / df_month[df_month[Column.DAY] == first_day].iloc[0][Column.OPEN]
            )
            if (
                df_month.shape[0] >= 28 - 10
            ):  # 28 days in shortest Feb, 10 days - weeknds max
                df_months = df_months.append(df_month)
            else:
                logger.debug(f"Not enough data for {symbol} in {year}.{month}")

    return df_months[[Column.YEAR, Column.MONTH, Column.DAY, Column.PERCENT]]


def get_best_month_day(filename, limit=None):
    return __wrapper(filename, limit, _get_month_day_diffs)


def __wrapper(filename, limit, func, post_func=None, interval="1d"):
    symbols = __get_symbols(filename, limit)

    history_data = __get_history(symbols.values.tolist(), interval)
    symbols_with_history = [
        {Column.SYMBOL: symbol, Column.HISTORY: history_data[symbol]}
        for symbol in history_data.columns.get_level_values(0).unique().to_list()
    ]

    symbols_dfs = pd.concat(concurrent_map(func, symbols_with_history))
    if post_func:
        symbols_dfs = post_func(symbols_dfs)

    symbols_dfs[Column.PERCENT] = symbols_dfs[Column.PERCENT] * 100

    symbols_dfs = symbols_dfs.convert_dtypes()

    return symbols_dfs
