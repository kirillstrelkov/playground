from common import YahooRange
from tqdm import tqdm

from stocks.buy_sell_analysis import analysis, analysis_base_first_date

if __name__ == "__main__":
    # Receive all data and save it to tmp folder - cache it
    limit = None
    args = []
    for filename in ["sp500/sp500.csv", "dax/dax_mdax_sdax.csv"]:
        for module in [analysis, analysis_base_first_date]:
            for func, range in [
                ("get_best_month", YahooRange.YEARS_20),
                ("get_best_week", YahooRange.YEARS_20),
                ("get_best_month_day", YahooRange.YEARS_20),
                ("get_best_weekday", YahooRange.YEARS_20),
                ("get_best_hour", YahooRange.YEARS_2),
                ("get_best_time", YahooRange.DAYS_58),
                ("get_best_quarter", YahooRange.DAYS_58),
            ]:
                args.append((filename, module, func, range))

    for filename, module, func, range in tqdm(args):
        df = getattr(module, func)(filename, range, limit=limit)
        assert not df.empty
