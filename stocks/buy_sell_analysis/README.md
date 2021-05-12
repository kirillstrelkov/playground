# Stock prices analysis with Python

Analysis is divided into two different implementations:

- `analysis.py` - _base point_ is first data point in the begging of each period
- `analysis_base_first_date.py` - _base point_ is first data point in dataset

Description:

- _base point_ - stock price that will be treated as 100%, all next values will be compared with this one.
- _data point_ - stock price from data row in dataset
- _stock price_ - value of 'Open' stock price
- _dataset_ - `pandas` `DataFrame` list of stock prices for specific period and specific interval
- [SP500](./sp500.csv] - list of stock symbols
