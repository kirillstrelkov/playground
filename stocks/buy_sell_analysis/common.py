import os
import tempfile
from datetime import datetime, timedelta
from enum import IntEnum, auto

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from loguru import logger
from matplotlib import pyplot
from seaborn import barplot, boxplot, lineplot, scatterplot
from utils.misc import concurrent_map

from caching_utils import get_cached_value, get_hashsum


class YahooRange(IntEnum):
    YEARS_20 = auto()
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


def _get_hashsum(*args):
    return get_hashsum(*args)


def _get_cached_value(hashsum, func_get_value):
    return get_cached_value(hashsum, func_get_value, TEMP_FOLDER)


def get_history(symbols, start_date, end_date, interval):
    hashsum = _get_hashsum(
        get_history.__name__, ",".join(symbols), start_date, end_date, interval
    )

    df = _get_cached_value(
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

    # DateTimeIndex as x for some data??
    df[Column.WEEKDAY] = [t.weekday() for t in df_date.tolist()]
    df[Column.WEEK] = [t.isocalendar()[1] for t in df_date.tolist()]

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
    r = requests.get(url, headers={"User-agent": "Mozilla/5.0"})
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

        hashsum = _get_hashsum(_get_symbols.__name__, *(isins + [str(limit)]))
        symbols = _get_cached_value(hashsum, __get_symbols_from_yf)

        assert symbols, f"Symbols not found {isins}"
    else:
        raise ValueError(f"{Column.SYMBOL} or {Column.ISIN} not found in {df.columns}")

    if limit:
        symbols = symbols[:limit]

    return symbols


def wrapper(filename: str, yahoo_range: YahooRange, limit, func, interval: str = "1d"):
    def __get_symbols_nested():
        start_date, end_date = [
            _format_datetime(d) for d in _get_start_and_end_dates(yahoo_range)
        ]
        symbols = _get_symbols(filename, limit)

        history_data = get_history(symbols, start_date, end_date, interval)
        if len(set(symbols)) == 1:
            symbols_with_history = [
                {Column.SYMBOL: symbols[0], Column.HISTORY: history_data}
            ]
        else:
            symbols_with_history = [
                {Column.SYMBOL: symbol, Column.HISTORY: history_data[symbol]}
                for symbol in history_data.columns.get_level_values(0)
                .unique()
                .to_list()
                if (
                    not history_data.empty
                    and not history_data[
                        history_data[symbol][Column.OPEN].notna()
                    ].empty
                )
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

    hashsum = _get_hashsum(
        wrapper.__name__,
        func.__module__,
        func.__name__,
        filename,
        yahoo_range,
        limit,
        interval,
    )
    logger.debug(
        "Hashsum for {}: {}",
        (
            wrapper.__name__,
            func.__module__,
            func.__name__,
            filename,
            yahoo_range,
            limit,
            interval,
        ),
        hashsum,
    )
    symbols_dfs = _get_cached_value(
        hashsum,
        __get_symbols_nested,
    )

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

    for i, func in enumerate(funcs):
        ax = axs[i]

        if func == lineplot:
            data[x] = data[x].astype(float)
            kwargs["ci"] = plot_ci
        elif func == barplot:
            kwargs["ci"] = plot_ci

        ax = func(**kwargs, ax=ax)
        if func == barplot:
            y_q2 = Y.quantile(0.93)
            y_q1 = Y.quantile(0.10)
            ax.set_ylim(y_q1, y_q2)

    fig.tight_layout()


def _get_start_and_end_dates(range_type: YahooRange):
    current_date = datetime.now()
    if range_type in (YahooRange.YEARS_10, YahooRange.YEARS_20):
        year = current_date.year
        end_date = datetime(year, 1, 1)

        if range_type == YahooRange.YEARS_10:
            year -= 10
        elif range_type == YahooRange.YEARS_20:
            year -= 20
        start_date = datetime(year, 1, 1)
    elif range_type == YahooRange.YEARS_2:
        # to be sure that range is within "last" 730 days
        start_date = datetime(
            current_date.year - 2, current_date.month, current_date.day
        ) + timedelta(days=2)
        # yesterday
        end_date = current_date - timedelta(days=1)
    elif range_type == YahooRange.DAYS_58:
        end_date = current_date - timedelta(days=1)
        start_date = end_date - timedelta(days=58)
    else:
        raise ValueError(f"Unsupported range: {range_type}")

    return start_date, end_date


def _format_datetime(time: datetime):
    return datetime.strftime(time, "%Y-%m-%d")
