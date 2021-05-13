import hashlib
import os
import pickle
import tempfile

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from loguru import logger
from utils.file import read_content, save_file
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
    ISIN = "ISIN"
    PERCENT = "Percent (mean)"
    HISTORY = "history"
    TIME = "time"
    QUARTER = "quarter"
    ALL = [
        SYMBOL,
        PERCENT,
        OPEN,
        YEAR,
        MONTH,
        MONTH_NAME,
        WEEK,
        WEEKDAY,
        DAY,
        DAY_NAME,
        HOUR,
        MINUTE,
    ]


def get_history(symbols, start_date, end_date, interval):
    m = hashlib.sha256()
    m.update(
        ",".join((",".join(symbols), start_date, end_date, interval)).encode("utf-8")
    )
    hashsum = m.hexdigest()

    folder = os.path.join(tempfile.gettempdir(), "stock_analysis")
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, hashsum)
    logger.debug(f"Using history file: {path}")

    if not os.path.exists(path):
        df = yf.download(
            symbols,
            interval=interval,
            start=start_date,
            end=end_date,
            group_by="ticker",
        )
        save_file(path, pickle.dumps(df), mode="wb", encoding=None)

    df = pickle.loads(read_content(path, mode="rb", encoding=None))

    return df


def __get_date_column_name(df):
    if Column.DATETIME in df.columns:
        return Column.DATETIME
    elif Column.DATE in df.columns:
        return Column.DATE
    else:
        datetime_col = None
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                datetime_col = col
                break

        assert datetime_col is not None, f"Date columns not found in {df.columns}"

        df[Column.DATETIME] = df[datetime_col]
        df.drop(columns=[datetime_col], inplace=True)

        return Column.DATETIME


def update_dataframe(df, symbol, set_base_value=False):
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
    if not df.empty:
        df = df[df[Column.OPEN].notna()]

    df[Column.SYMBOL] = symbol
    df[Column.PERCENT] = np.nan

    # Set base value to first data point
    if set_base_value and not df.empty:
        first_price = df.sort_values(date_column).iloc[0][Column.OPEN]
        df[Column.PERCENT] = df[Column.OPEN] / first_price

    return df


def __get_symbol(isin):
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={isin}&quotesCount=1&newsCount=0"
    r = requests.get(url)
    if r.status_code == 200:
        quotes = r.json().get("quotes")
        if quotes:
            symbol = quotes[0].get("symbol")
            if symbol:
                return symbol

    logger.debug(f"Symbol not found for {isin}")
    return None


def __get_symbols(filename, limit):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename))
    if Column.SYMBOL in df.columns:
        symbols = df[Column.SYMBOL].values.tolist()
    elif Column.ISIN in df.columns:
        isins = df[Column.ISIN].tolist()

        symbols = []
        for isin in isins:
            symbol = __get_symbol(isin)
            if symbol:
                symbols.append(symbol)

            if len(symbols) >= limit:
                break

        assert symbols, f"Symbols not found {isins}"
    else:
        raise ValueError(f"{Column.SYMBOL} or {Column.ISIN} not found in {df.columns}")

    if limit:
        symbols = symbols[:limit]

    return symbols


def wrapper(filename, start_date, end_date, limit, func, interval="1d"):
    symbols = __get_symbols(filename, limit)

    history_data = get_history(symbols, start_date, end_date, interval)
    symbols_with_history = [
        {Column.SYMBOL: symbol, Column.HISTORY: history_data[symbol]}
        for symbol in history_data.columns.get_level_values(0).unique().to_list()
        if not history_data.empty
        and not history_data[history_data[symbol][Column.OPEN].notna()].empty
    ]

    dfs = [df for df in concurrent_map(func, symbols_with_history) if not df.empty]
    if dfs:
        symbols_dfs = pd.concat(dfs, ignore_index=True)

        assert not symbols_dfs.isna().any().any()

        symbols_dfs[Column.PERCENT] = symbols_dfs[Column.PERCENT] * 100

        symbols_dfs = symbols_dfs.convert_dtypes()
    else:
        symbols_dfs = pd.DataFrame()

    return symbols_dfs
