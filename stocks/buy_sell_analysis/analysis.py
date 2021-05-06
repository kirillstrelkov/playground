import os

import pandas as pd
import yfinance as yf
from loguru import logger
from more_itertools.recipes import flatten
from pandas.core.frame import DataFrame
from utils.misc import concurrent_map

START_DATE = "2015-1-1"
END_DATE = "2020-1-1"


def get_history(symbol):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1d", start=START_DATE, end=END_DATE)
    if not df.empty:
        df["Symbol"] = symbol
    return df


def get_weekly_diffs(df):
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
    return df.to_dict("r")


def get_best_weekday(filename, limit=None):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename))
    symbols = df["Symbol"]

    if limit:
        symbols = symbols[:limit]

    histories = []
    for df_h in concurrent_map(get_history, symbols):
        if not df_h.empty:
            histories.append(df_h)

    symbols_dfs = flatten(concurrent_map(get_weekly_diffs, histories))

    df = DataFrame(symbols_dfs)
    df = (
        df[["weekday", "diff"]]
        .groupby("weekday")
        .mean()
        .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    )

    df = df * 100
    return df
