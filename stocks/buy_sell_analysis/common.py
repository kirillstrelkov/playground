import hashlib
import os
import pickle
import tempfile
from datetime import datetime, timedelta
from enum import Enum, auto

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from loguru import logger
from matplotlib import pyplot
from seaborn import barplot, boxplot, lineplot, scatterplot
from utils.file import read_content, save_file
from utils.misc import concurrent_map


class YahooRange(Enum):
    YEARS_10 = auto()
    YEARS_2 = auto()
    DAYS_58 = auto()


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


TEMP_FOLDER = os.path.join(tempfile.gettempdir(), "stock_analysis")


def __get_hashsum(*args):
    m = hashlib.sha256()
    m.update(",".join([str(a) for a in args]).encode("utf-8"))
    hashsum = m.hexdigest()
    return hashsum


def __get_cached_value(hashsum, func_get_value):
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    path = os.path.join(TEMP_FOLDER, hashsum)
    logger.debug(f"Using history file: {path}")

    if not os.path.exists(path):
        data = func_get_value()
        save_file(path, pickle.dumps(data), mode="wb", encoding=None)

    data = pickle.loads(read_content(path, mode="rb", encoding=None))
    return data


def get_history(symbols, start_date, end_date, interval):
    hashsum = __get_hashsum(",".join(symbols), start_date, end_date, interval)

    df = __get_cached_value(
        hashsum,
        lambda: yf.download(
            symbols,
            interval=interval,
            start=start_date,
            end=end_date,
            group_by="ticker",
        ),
    )

    return df


def get_date_column_name(df):
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

    date_column = get_date_column_name(df)
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


def _get_symbols(filename, limit):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename))
    if Column.SYMBOL in df.columns:
        symbols = df[Column.SYMBOL].values.tolist()
    elif Column.ISIN in df.columns:
        isins = df[Column.ISIN].tolist()

        def __get_symbols_from_yf():
            symbols = []
            for isin in isins:
                symbol = __get_symbol(isin)
                if symbol:
                    symbols.append(symbol)

                if limit and len(symbols) >= limit:
                    break
            return symbols

        hashsum = __get_hashsum(*(isins + [str(limit)]))
        symbols = __get_cached_value(hashsum, __get_symbols_from_yf)

        assert symbols, f"Symbols not found {isins}"
    else:
        raise ValueError(f"{Column.SYMBOL} or {Column.ISIN} not found in {df.columns}")

    if limit:
        symbols = symbols[:limit]

    return symbols


def wrapper(filename: str, yahoo_range: YahooRange, limit, func, interval: str = "1d"):
    start_date, end_date = [
        _format_datetime(d) for d in _get_start_and_end_dates(yahoo_range)
    ]
    symbols = _get_symbols(filename, limit)

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


def plot(**kwargs):
    plot_ci = 95

    funcs = [boxplot, barplot, scatterplot, lineplot]
    # NOTE: after lineplot X will be float

    data = kwargs["data"]
    x = kwargs["x"]
    y = kwargs["y"]
    Y = data[y]
    print(kwargs["data"][[x, y]].groupby(x).mean().head())

    fig, axs = pyplot.subplots(nrows=len(funcs), figsize=(15, 20))

    plot_kwargs = dict([(func, kwargs.pop(func.__name__, {})) for func in funcs])

    for i, func in enumerate(funcs):
        ax = axs[i]

        if func == lineplot:
            data[x] = data[x].astype(float)
            kwargs["ci"] = plot_ci
        elif func == barplot:
            q_min, q_max = plot_kwargs.get(func).get("quantile", (0.50, 0.90))
            ax.set_ylim(Y.quantile(q_min), Y.quantile(q_max))
            kwargs["ci"] = plot_ci

        ax = func(**kwargs, ax=ax)

    fig.tight_layout()


def _get_start_and_end_dates(range_type: YahooRange):
    current_date = datetime.now()
    if range_type in (YahooRange.YEARS_10, YahooRange.YEARS_2):
        year = current_date.year
        end_date = datetime(year, 1, 1)

        if range_type is YahooRange.YEARS_10:
            year -= 10
        elif range_type is YahooRange.YEARS_2:
            year -= 2

        start_date = datetime(year, 1, 1)
    elif range_type is YahooRange.DAYS_58:
        end_date = current_date - timedelta(days=1)
        start_date = end_date - timedelta(days=58)
    else:
        raise ValueError(f"Unsupported range: {range_type}")

    return start_date, end_date


def _format_datetime(time: datetime):
    return datetime.strftime(time, "%Y-%m-%d")
