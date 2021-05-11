import hashlib
import os
import pickle
import tempfile

import numpy as np
import yfinance as yf
from utils.file import read_content, save_file


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


def get_history(symbols, start_date, end_date, interval):
    m = hashlib.sha256()
    m.update(
        ",".join((",".join(symbols), start_date, end_date, interval)).encode("utf-8")
    )
    hashsum = m.hexdigest()

    path = os.path.join(tempfile.gettempdir(), hashsum)

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
    else:
        return Column.DATE


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
    df = df[df[Column.OPEN].notna()]

    df[Column.SYMBOL] = symbol
    df[Column.PERCENT] = np.nan

    # Set base value to first data point
    if set_base_value and not df.empty:
        first_price = df.sort_values(date_column).iloc[0][Column.OPEN]
        df[Column.PERCENT] = df[Column.OPEN] / first_price

    return df
