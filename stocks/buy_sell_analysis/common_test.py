from datetime import datetime

from dateutil.relativedelta import relativedelta
from stocks.buy_sell_analysis.common import (
    YahooRange,
    _format_datetime,
    _get_start_and_end_dates,
)


def test_get_range_10years():
    start_date, end_date = _get_start_and_end_dates(YahooRange.YEARS_10)
    assert relativedelta(end_date, start_date).years == 10


def test_get_range_2years():
    start_date, end_date = _get_start_and_end_dates(YahooRange.YEARS_2)
    assert relativedelta(end_date, start_date).years == 2


def test_get_range_2month():
    start_date, end_date = _get_start_and_end_dates(YahooRange.DAYS_58)
    assert (end_date - start_date).days == 58


def test_format_datetime():
    assert _format_datetime(datetime.fromtimestamp(1621007034)) == "2021-05-14"
