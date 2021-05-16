import os
import sys

from loguru import logger
from pandas.core.frame import DataFrame
from stocks.buy_sell_analysis import analysis, analysis_base_first_date
from stocks.buy_sell_analysis.common import (
    Column,
    YahooRange,
    _get_cached_value,
    _get_hashsum,
)

logger.remove()
logger.add(sys.stdout, level="WARNING")


def __get_data(filename, analysis_module, limit):
    data_to_collect = [
        (Column.MONTH, analysis_module.get_best_month, YahooRange.YEARS_20),
        (Column.DAY, analysis_module.get_best_month_day, YahooRange.YEARS_20),
        (Column.WEEK, analysis_module.get_best_week, YahooRange.YEARS_20),
        (Column.WEEKDAY, analysis_module.get_best_weekday, YahooRange.YEARS_20),
        (Column.HOUR, analysis_module.get_best_hour, YahooRange.YEARS_2),
        (Column.TIME, analysis_module.get_best_time, YahooRange.DAYS_58),
        (Column.QUARTER, analysis_module.get_best_quarter, YahooRange.DAYS_58),
    ]

    module_name = analysis_module.__name__

    data = []
    for column, func, yrange in data_to_collect:
        # TODO: fix add modulename
        hashsum = _get_hashsum(module_name, func.__name__, filename, yrange, limit)
        logger.info(f"{column}, {func.__name__}, {yrange} hashum: {hashsum}")
        data.append(
            (
                column,
                _get_cached_value(
                    hashsum,
                    lambda: func(filename, yrange, limit),
                ),
            )
        )

    data = [(k, df[[k, Column.PERCENT]].groupby(k).mean()) for k, df in data]
    return dict(data)


def __get_stats(*data, module_name=None, filename=None):
    assert len(data) > 0

    stats = []
    for key in data[0].keys():
        dfs = [d.get(key) for d in data]
        points_go_down = []
        points_go_up = []

        for df in dfs:
            prev_value = None
            df_point_go_down = set()
            df_point_go_up = set()
            for _, row in df.iterrows():
                cur_value = row[Column.PERCENT]
                if prev_value is None:
                    prev_value = cur_value
                    continue
                else:
                    # key is in index not in column!
                    point = row.name
                    if cur_value < prev_value:
                        df_point_go_down.add(point)
                    elif cur_value > prev_value:
                        df_point_go_up.add(point)

                    prev_value = cur_value

            points_go_down.append(df_point_go_down)
            points_go_up.append(df_point_go_up)

        stats.append(
            {
                "filename": os.path.basename(filename) if filename else None,
                "module": module_name.split(".")[-1] if module_name else None,
                "type": key,
                "down": set.intersection(*points_go_down) or None,
                "up": set.intersection(*points_go_up) or None,
            }
        )
    return stats


def print_stats(stats):
    print(DataFrame(stats).to_markdown())


if __name__ == "__main__":
    limit = None

    data = []
    for filename in ["sp500/sp500.csv", "dax/dax_mdax_sdax.csv"]:
        data_per_file = []
        for analysis_module in [analysis, analysis_base_first_date]:
            d = __get_data(filename, analysis_module, limit)
            data_per_file.append(d)

        print(f"File: {filename} combined:")
        stats_per_file = __get_stats(*data_per_file, filename=filename)
        print_stats(stats_per_file)
        data += data_per_file

    stats = __get_stats(*data)
    print("Combined:")
    print_stats(stats)
