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


def __get_history(symbol, interval):
    ticker = yf.Ticker(symbol)
    df = ticker.history(interval=interval, start=START_DATE, end=END_DATE)
    if not df.empty:
        df["Symbol"] = symbol
    return df


def _get_weekly_diffs(df_symbols):
    symbol = df_symbols["Symbol"]
    interval = df_symbols["interval"]
    df = __get_history(symbol, interval)

    first_day = "Monday"
    last_day = "Friday"

    symbol = df["Symbol"][0]
    df = df.reset_index()
    df["weekday"] = df["Date"].apply(lambda x: x.day_name())

    if df[df["weekday"] == first_day].empty:
        return {}

    # getting first row that starts with Monday
    df = df[df[df["weekday"] == first_day].index[0] :]
    prev_monday_price = 0
    full_weeks = []
    is_monday = False
    is_friday = False
    week = []
    for _, row in df.iterrows():
        weekday = row["weekday"]
        # filter weeks were all days were traiding days
        is_monday = weekday == first_day
        is_friday = weekday == last_day

        if is_monday:
            prev_monday_price = row["Open"]
            price_diff = 1
            week = [row]
        else:
            if prev_monday_price == 0:
                continue
            price_diff = row["Open"] / prev_monday_price
            week.append(row)
        row["diff"] = price_diff

        if is_friday and len(week) == 5:
            full_weeks += week

    logger.debug(f"{symbol} {len(full_weeks)} full weeks")

    if not full_weeks:
        return {}

    df = DataFrame(full_weeks)

    df["Symbol"] = symbol
    return df


def __get_symbols(filename, limit):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename))
    symbols = df["Symbol"]

    if limit:
        symbols = symbols[:limit]

    return symbols


def get_best_weekday(filename, limit=None):
    symbols = DataFrame(__get_symbols(filename, limit))
    symbols["interval"] = "1d"

    symbols_dfs = pd.concat(
        concurrent_map(_get_weekly_diffs, symbols.T.to_dict().values())
    )

    symbols_dfs = (
        symbols_dfs[["weekday", "diff"]]
        .groupby("weekday")
        .mean()
        .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    )

    symbols_dfs = symbols_dfs * 100
    return symbols_dfs


def _get_monthly_diffs(df_symbols):
    symbol = df_symbols["Symbol"]
    interval = df_symbols["interval"]
    interval = "1d"
    df = __get_history(symbol, interval)

    first_month = calendar.month_name[1]
    last_month = calendar.month_name[-1]

    df = df.reset_index()
    df["month"] = df["Date"].apply(lambda x: x.month)
    df["year"] = df["Date"].apply(lambda x: x.year)

    df = df.groupby(["year", "month"], as_index=False).mean()

    df["month"] = df["month"].apply(lambda x: calendar.month_name[x])

    if df[df["month"] == first_month].empty:
        return DataFrame()

    # Filteting NA in Open - this means usually a dividends
    df = df[df["Open"].notna()]

    # getting first row that starts with Monday
    df = df[df[df["month"] == first_month].index[0] :]
    prev_monday_price = 0
    full_months = []
    is_january = False
    is_december = False
    months = []
    for _, row in df.iterrows():
        month = row["month"]
        # filter months were all days were traiding days
        is_january = month == first_month
        is_december = month == last_month

        if is_january:
            prev_monday_price = row["Open"]
            price_diff = 1
            months = [row]
        else:
            if prev_monday_price == 0:
                continue
            price_diff = row["Open"] / prev_monday_price
            months.append(row)
        row["diff"] = price_diff

        # TODO: if there was a stock split - skip

        if is_december and len(months) == 12:
            full_months += months

    logger.debug(f"{symbol} {len(full_months)} full months")

    if not full_months:
        return DataFrame()

    df = DataFrame(full_months)

    df["Symbol"] = symbol
    return df


def get_best_month(filename, limit=None):
    symbols = DataFrame(__get_symbols(filename, limit))
    symbols["interval"] = "1mo"

    symbols_dfs = pd.concat(
        concurrent_map(_get_monthly_diffs, symbols.T.to_dict().values())
    )

    symbols_dfs = (
        symbols_dfs[["month", "diff"]]
        .groupby("month")
        .mean()
        .reindex([calendar.month_name[i] for i in range(1, 13)])
    )

    symbols_dfs = symbols_dfs * 100
    return symbols_dfs
