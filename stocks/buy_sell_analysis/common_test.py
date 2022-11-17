from datetime import datetime

from dateutil.relativedelta import relativedelta

from stocks.buy_sell_analysis import analysis, analysis_base_first_date
from stocks.buy_sell_analysis.common import (
    YahooRange,
    _format_datetime,
    _get_start_and_end_dates,
    _get_symbols,
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


def test_get_symbols():
    limit = 10000
    for filename, expected_results in [
        ("sp500/sp500.csv", 505),
        ("dax/dax_mdax_sdax.csv", 159),
    ]:
        assert len(_get_symbols(filename, limit)) == expected_results


def test_cached_df_from_different_modules():
    limit = 5
    for filename in ["sp500/sp500.csv", "dax/dax_mdax_sdax.csv"]:
        assert not analysis.get_best_month(
            filename, YahooRange.YEARS_2, limit=limit
        ).equals(
            analysis_base_first_date.get_best_month(
                filename, YahooRange.YEARS_2, limit=limit
            )
        )

        assert not analysis.get_best_month(
            filename, YahooRange.DAYS_58, limit=limit
        ).equals(
            analysis_base_first_date.get_best_hour(
                filename, YahooRange.DAYS_58, limit=limit
            )
        )


def test_cached_df_from_different_files():
    limit = 5
    assert not analysis.get_best_month(
        "sp500/sp500.csv", YahooRange.YEARS_2, limit=limit
    ).equals(
        analysis.get_best_month(
            "dax/dax_mdax_sdax.csv", YahooRange.YEARS_2, limit=limit
        )
    )
