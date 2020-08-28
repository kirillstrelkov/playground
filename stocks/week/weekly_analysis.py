import pandas as pd
from utils.misc import concurrent_map

import yfinance as yf
import os
from pandas.core.frame import DataFrame
from more_itertools.recipes import flatten
from loguru import logger

START_DATE = "2015-1-1"
END_DATE = "2020-1-1"


def get_history(symbol):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1d", start=START_DATE, end=END_DATE)
    if not df.empty:
        df["Symbol"] = symbol
    return df


def get_weekly_diffs(df):
    symbol = df["Symbol"][0]
    df = df.reset_index()
    df["weekday"] = df["Date"].apply(lambda x: x.weekday())

    if df[df["weekday"] == 0].empty:
        return {}

    # getting first row that starts with Monday
    df = df[df[df["weekday"] == 0].index[0] :]
    prev_monday_price = 0
    full_weeks = []
    is_monday = False
    is_friday = False
    week = []
    for _, row in df.iterrows():
        weekday = row["weekday"]
        # filter weeks were all days were traiding days
        is_monday = weekday == 0
        is_friday = weekday == 4

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


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "nasdaq.csv"))
    symbols = df["Symbol"]
    histories = []
    for df_h in concurrent_map(get_history, symbols):
        if not df_h.empty:
            histories.append(df_h)

    symbols_dfs = flatten(concurrent_map(get_weekly_diffs, histories))

    df = DataFrame(symbols_dfs)
    df = (
        df[["weekday", "diff"]]
        .groupby("weekday", group_keys=False)
        .mean()
        .reset_index(drop=True)
    )

    df = df * 100
    print(df.to_markdown())
