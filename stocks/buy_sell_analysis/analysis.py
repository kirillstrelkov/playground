import os

import numpy as np
import pandas as pd
from loguru import logger
from pandas.core.frame import DataFrame
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
    df = update_dataframe(df_symbols[Column.HISTORY], symbol)

    # if number of working days less than 3 - don't count
    number_of_good_working = 3

    # Filter columns
    df = df[[Column.YEAR, Column.WEEK, Column.WEEKDAY, Column.SYMBOL, Column.OPEN]]

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


def get_best_weekday(filename, start_date, end_date, limit=None):
    return __wrapper(filename, start_date, end_date, limit, _get_best_weekday_diffs)


def _get_monthly_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol)

    # Filter columns
    df = df[[Column.YEAR, Column.MONTH, Column.SYMBOL, Column.OPEN]]

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

    return df_months[[Column.YEAR, Column.MONTH, Column.SYMBOL, Column.PERCENT]]


def get_best_month(filename, start_date, end_date, limit=None):
    return __wrapper(
        filename, start_date, end_date, limit, _get_monthly_diffs, interval="1mo"
    )


def _get_month_day_diffs(df_symbols):
    symbol = df_symbols[Column.SYMBOL]
    df = update_dataframe(df_symbols[Column.HISTORY], symbol)

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

    df = update_dataframe(df_history, symbol)

    hours = df[Column.HOUR].unique()
    assert hours.shape[0] > 5, f"Wrong data for {symbol} {hours.values}"

    # Filter columns
    df = df[
        [Column.YEAR, Column.WEEK, Column.DAY, Column.HOUR, Column.SYMBOL, Column.OPEN]
    ]

    df_days = DataFrame()
    for year in df[Column.YEAR].unique():
        for week in df[Column.WEEK].unique():
            for day in df[Column.DAY].unique():
                df_day = df[
                    (df[Column.YEAR] == year)
                    & (df[Column.WEEK] == week)
                    & (df[Column.DAY] == day)
                ]
                if df_day.empty:
                    continue
                first_hour = df_day[Column.HOUR].min()
                df_day[Column.PERCENT] = (
                    df_day[Column.OPEN]
                    / df_day[df_day[Column.HOUR] == first_hour].iloc[0][Column.OPEN]
                )
                if df_day.shape[0] >= 5:  # good data is at least 5 hours per day
                    df_days = df_days.append(df_day)
                else:
                    logger.debug(f"Not enough data for {symbol} in {week} {day}")

    return df_days[
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

    df = update_dataframe(df_history, symbol)

    minutes = df[Column.MINUTE].unique()
    assert minutes.shape[0] > 3, f"Wrong data for {symbol} {minutes.values}"

    # Filter columns
    df = df[
        [
            Column.YEAR,
            Column.WEEK,
            Column.DAY,
            Column.HOUR,
            Column.MINUTE,
            Column.SYMBOL,
            Column.OPEN,
        ]
    ]

    df_days = DataFrame()
    for year in df[Column.YEAR].unique():
        for week in df[Column.WEEK].unique():
            for day in df[Column.DAY].unique():
                for hour in df[Column.HOUR].unique():
                    df_hour = df[
                        (df[Column.YEAR] == year)
                        & (df[Column.WEEK] == week)
                        & (df[Column.DAY] == day)
                        & (df[Column.HOUR] == hour)
                    ]
                    if df_hour.empty:
                        continue
                    first_time = df_hour[Column.MINUTE].min()
                    df_hour[Column.PERCENT] = (
                        df_hour[Column.OPEN]
                        / df_hour[df_hour[Column.MINUTE] == first_time].iloc[0][
                            Column.OPEN
                        ]
                    )
                    if (
                        df_hour.shape[0] >= 2
                    ):  # good data is at least 2 times per hour (9:30, 9:45)
                        df_days = df_days.append(df_hour)
                    else:
                        logger.debug(f"Not enough data for {symbol} in {week} {day}")

    df_days[Column.QUARTER] = df_days[Column.MINUTE]
    return df_days[
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

    df = update_dataframe(df_history, symbol)

    minutes = df[Column.MINUTE].unique()
    assert minutes.shape[0] > 3, f"Wrong data for {symbol} {minutes.values}"

    # Filter columns
    df = df[
        [
            Column.YEAR,
            Column.WEEK,
            Column.DAY,
            Column.HOUR,
            Column.MINUTE,
            Column.SYMBOL,
            Column.OPEN,
        ]
    ]

    df[Column.TIME] = df.apply(lambda x: x[Column.HOUR] + x[Column.MINUTE] / 60, axis=1)

    df_days = DataFrame()
    for year in df[Column.YEAR].unique():
        for week in df[Column.WEEK].unique():
            for day in df[Column.DAY].unique():
                df_hour = df[
                    (df[Column.YEAR] == year)
                    & (df[Column.WEEK] == week)
                    & (df[Column.DAY] == day)
                ]
                if df_hour.empty:
                    continue
                first_time = df_hour[Column.TIME].min()
                df_hour[Column.PERCENT] = (
                    df_hour[Column.OPEN]
                    / df_hour[df_hour[Column.TIME] == first_time].iloc[0][Column.OPEN]
                )
                if (
                    df_hour.shape[0] >= 2
                ):  # good data is at least 2 times per hour (9:30, 9:45)
                    df_days = df_days.append(df_hour)
                else:
                    logger.debug(f"Not enough data for {symbol} in {week} {day}")

    return df_days[
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
