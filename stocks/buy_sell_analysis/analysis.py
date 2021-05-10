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


def __get_history(symbols, interval):
    df = yf.download(
        symbols, interval=interval, start=START_DATE, end=END_DATE, group_by="ticker"
    )

    return df


def __update_dataframe(df):
    df = df.reset_index()

    for component in ["year", "month", "day", "hour", "minute"]:
        df[component] = df["Date"].apply(lambda x: getattr(x, component))

    df["day_name"] = df["Date"].apply(lambda x: x.day_name())
    df["month_name"] = df["Date"].apply(lambda x: x.month_name())
    df["weekday"] = df["Date"].apply(lambda x: x.weekday())
    df["week"] = df["Date"].apply(lambda x: x.isocalendar()[1])

    # Filteting NA in Open - this means usually a dividends
    df = df[df["Open"].notna()]

    return df


def __get_symbols(filename, limit):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename))
    symbols = df["Symbol"]

    if limit:
        symbols = symbols[:limit]

    return symbols


def _get_best_weekday_diffs(df_symbols):
    symbol = df_symbols["symbol"]
    df = __update_dataframe(df_symbols["history"])

    # if number of working days less than 3 - don't count
    number_of_good_working = 3

    # Filter columns
    df = df[["year", "week", "weekday", "Open"]]

    df_weeks = DataFrame()
    for year in df["year"].unique():
        for week in df["week"].unique():
            df_week = df[(df["year"] == year) & (df["week"] == week)]
            if df_week.empty:
                continue

            days = df_week["weekday"].values
            if df_week.shape[0] < number_of_good_working:
                # first and last week of year might contain only 1-2 days
                if week not in (1, 52, 53):
                    logger.debug(
                        f"Not enough data for {symbol} in {year} week {week}: {days}"
                    )
                continue

            first_weekday = df_week["weekday"].min()
            df_week["diff"] = (
                df_week["Open"]
                / df_week[df_week["weekday"] == first_weekday].iloc[0]["Open"]
            )
            assert (
                df_week.shape[0] >= number_of_good_working
            ), f"Wrong number of weekdays in dataframe {df_week.shape} for year {year} {week}: {days}"

            df_weeks = df_weeks.append(df_week)

    return df_weeks[["year", "week", "weekday", "diff"]]


def get_best_weekday(filename, limit=None):
    return __wrapper(filename, limit, _get_best_weekday_diffs)


def _get_monthly_diffs(df_symbols):
    symbol = df_symbols["symbol"]
    df = __update_dataframe(df_symbols["history"])

    df = df.groupby(["year", "month"], as_index=False).mean()

    # Filter columns
    df = df[["year", "month", "Open"]]

    df_months = DataFrame()
    for year in df["year"].unique():
        df_month = df[df["year"] == year]
        if df_month.shape[0] < 12:
            logger.debug(f"Not enough data for {symbol} in {year}")
            continue

        first_month = df_month["month"].min()
        df_month["diff"] = (
            df_month["Open"]
            / df_month[df_month["month"] == first_month].iloc[0]["Open"]
        )
        assert (
            df_month.shape[0] == 12
        ), f"Wrong number of month in dataframe {df_month.shape} for year {year}"

        df_months = df_months.append(df_month)

    return df_months[["year", "month", "diff"]]


def get_best_month(filename, limit=None):
    return __wrapper(filename, limit, _get_monthly_diffs)


def _get_month_day_diffs(df_symbols):
    symbol = df_symbols["symbol"]
    df = __update_dataframe(df_symbols["history"])

    # Filter columns
    df = df[["year", "month", "day", "Open"]]

    df_months = DataFrame()
    for year in df["year"].unique():
        for month in df["month"].unique():
            df_month = df[(df["year"] == year) & (df["month"] == month)]
            if df_month.empty:
                continue
            first_day = df_month["day"].min()
            df_month["diff"] = (
                df_month["Open"]
                / df_month[df_month["day"] == first_day].iloc[0]["Open"]
            )
            if (
                df_month.shape[0] >= 28 - 10
            ):  # 28 days in shortest Feb, 10 days - weeknds max
                df_months = df_months.append(df_month)
            else:
                logger.debug(f"Not enough data for {symbol} in {year}.{month}")

    return df_months[["year", "month", "day", "diff"]]


def get_best_month_day(filename, limit=None):
    return __wrapper(filename, limit, _get_month_day_diffs)


def __wrapper(filename, limit, func, post_func=None, interval="1d"):
    symbols = __get_symbols(filename, limit)

    history_data = __get_history(symbols.values.tolist(), interval)
    symbols_with_history = [
        {"symbol": symbol, "history": history_data[symbol]}
        for symbol in history_data.columns.get_level_values(0).unique().to_list()
    ]

    symbols_dfs = pd.concat(concurrent_map(func, symbols_with_history))
    if post_func:
        symbols_dfs = post_func(symbols_dfs)

    symbols_dfs["diff"] = symbols_dfs["diff"] * 100

    symbols_dfs = symbols_dfs.convert_dtypes()

    return symbols_dfs
