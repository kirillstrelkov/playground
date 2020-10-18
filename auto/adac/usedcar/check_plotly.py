import os
import re
from collections import defaultdict

import plotly
from plotly.graph_objs import Layout
from plotly.graph_objs.graph_objs import Scattergl

from utils.csv import get_row_dict_from_csv, save_dicts
from utils.file import read_file
from utils.misc import parse_int


def __filter_new_cars(data):
    # new cars - cars with data for 2017 year
    for car in data:
        prices = car["prices"]
        if prices["new"] and prices[2017]:
            yield car


def __add_changes_between(car, start_year, end_year):
    assert start_year > end_year
    prices = car["prices"]

    changes = {}
    prev_price = prices[start_year]
    # prices till 2014
    interested_years = list(range(start_year, end_year - 1, -1))
    interested_prices = [prices[year] for year in interested_years]

    if all([p is not None for p in interested_prices]):
        changes[interested_years[-1]] = (
            float(interested_prices[-1] - prev_price) / prev_price
        )

    car["changes"] = changes
    return car


def __set_percentage(car):
    prices = [(year, car[str(year)]) for year in range(2011, 2019)]
    prices_with_data = dict(
        [(year, float(price)) for year, price in prices if len(price) > 0]
    )
    max_year = max(prices_with_data.keys())
    max_price = prices_with_data[max_year]

    car["percentage"] = dict(
        [
            ((max_year - year), price / max_price)
            for year, price in prices_with_data.items()
        ]
    )
    return car


def __set_price_diff(car):
    prices = [(year, car[str(year)]) for year in range(2011, 2019)]
    prices_with_data = dict(
        [(year, float(price)) for year, price in prices if len(price) > 0]
    )
    max_year = max(prices_with_data.keys())
    max_price = prices_with_data[max_year]

    car["percentage"] = dict(
        [
            ((max_year - year), (price - max_price) / max_price)
            for year, price in prices_with_data.items()
        ]
    )
    return car


def __add_changes_per_year(car):
    prices = car["prices"]

    changes = {}
    prev_price = prices["new"]
    for i in range(1, len(YEARS_HEADER)):
        next_year = YEARS_HEADER[i]
        next_year_price = prices[next_year]
        if next_year_price:
            changes[next_year] = float(next_year_price - prev_price) / prev_price
            prev_price = next_year_price

    car["changes"] = changes
    return car


# def __plot(data):
#     scatters = []
#     for d in data:
#
#         scatters.append(Scattergl(x=prices, y=[name] * len(prices),
#                                   name=name,
#                                   text=name))
#
#     plotly.offline.plot({
#         "data": scatters,
#         "layout": Layout(title="ADAC min/max prices")
#     })


def __mark_data(cars):
    marks = defaultdict(lambda: defaultdict(list))
    for car in cars:
        year_prices = marks[car["mark"]]
        prices = car["changes"]
        for year, price in prices.items():
            if price:
                year_prices[year].append(price)

    return marks


def __plot_cars_new_year_change(cars, year):
    range(len(cars))

    scatters = []
    x = []
    y = []
    for car in cars:
        new_price_change = car["changes"].get(year)
        if new_price_change:
            x.append(car["model"])
            y.append(new_price_change)
    scatters.append(Scattergl(x=x, y=y, mode="markers"))

    plotly.offline.plot({"data": scatters, "layout": Layout(title="A")})


def save_parsed_adac():
    path = os.path.join(os.path.dirname(__file__), "gebrauchtwagenpreise_53800.csv")
    cars = []
    for car in list(__get_cars(path)):
        prices = dict(
            [[str(k), "" if v is None else str(v)] for k, v in car["prices"].items()]
        )
        del car["prices"]
        car.update(prices)
        cars.append(car)
    save_dicts("adac.csv", cars)


def __main():
    save_parsed_adac()
    return 0
    # NOTE: remove all data before and after main table in csv!!!
    # pprint(list(get_row_dict_from_csv(path)))
    path = os.path.join(os.path.dirname(__file__), "gebrauchtwagenpreise_53800.csv")

    cars = list(__get_cars(path))

    print("Cars:", len(cars))
    cars = [
        car
        for car in cars
        if car["prices"][2018] is not None and car["prices"][2018] <= 30000
    ]
    print("Cars filter:", len(cars))

    # pprint(list(__filter_new_cars(data)))
    cars = [
        car
        for car in cars
        if any(
            [
                name in car["model"].lower()
                for name in [
                    "sportage",
                    "3008",
                    "tiguan",
                    "compass",
                    "karoq",
                    "ateca",
                    "scenic",
                    "outback",
                    "tucson",
                ]
            ]
        )
    ]
    cars = [car for car in cars if car["mark"] == "VW"]

    min_year = 2017
    [__add_changes_between(car, 2018, min_year) for car in cars]
    # pprint(__mark_data(cars))

    cars = [
        car for car in cars if len(car["changes"]) > 0 and min_year in car["changes"]
    ]
    print("Cars filter:", len(cars))

    cars = [car for car in cars if car["changes"][min_year] > -0.25]
    print("Cars filter:", len(cars))

    __plot_cars_new_year_change(cars, min_year)


def is_suv(x):
    return any(
        [
            v.lower() in x.lower()
            for v in [
                "sportage",
                "3008",
                "tiguan",
                "compass",
                "yeti",
                "rav4",
                "grandland",
                "karoq",
                "ateca",
                "scenic",
                "tucson",
            ]
        ]
    )


def __main2(path):

    data = get_row_dict_from_csv(path)
    data = [d for d in data if is_suv(d["model"])]

    years = ["new", "2017"]

    data = [d for d in data if all([len(d[str(year)]) > 0 for year in years])]

    scatters = []

    i = 0
    for d in data:
        prices = [d[str(year)] for year in years]
        name = d["model"]

        scatters.append(Scattergl(x=["2018", "2017"], y=prices, name=name, text=name))
        i += 1

    plotly.offline.plot({"data": scatters, "layout": Layout(title="lost per years")})


def __change_new_to_year(data):
    for d in data:
        if "new" in d:
            d["2018"] = d["new"]
    return data


def __main3(path):
    data = list(get_row_dict_from_csv(path))
    data = __change_new_to_year(data)
    data = [d for d in data if is_suv(d["model"])]

    [__set_percentage(car) for car in data]

    scatters = []

    for d in data:
        percentages = d["percentage"].items()
        years_diff = [y for y, p in percentages]
        prices = [p for y, p in percentages]
        name = d["model"]
        scatters.append(Scattergl(x=years_diff, y=prices, name=name, text=name))

    plotly.offline.plot(
        {"data": scatters, "layout": Layout(title="lost per years in percentage")}
    )


def __main4(path):
    data = list(get_row_dict_from_csv(path))
    data = __change_new_to_year(data)
    data = [d for d in data if is_suv(d["model"])]

    [__set_price_diff(car) for car in data]

    scatters = []

    for d in data:
        percentages = d["percentage"].items()
        years_diff = [y for y, p in percentages]
        prices = [p for y, p in percentages]
        name = d["model"]
        scatters.append(Scattergl(x=years_diff, y=prices, name=name, text=name))

    plotly.offline.plot(
        {"data": scatters, "layout": Layout(title="lost per years in percentage")}
    )


if __name__ == "__main__":
    path = os.path.join(
        os.path.dirname(__file__), "data", "df_gebrauchtwagenpreise_2018.csv"
    )
    # __main2(path)
    __main3(path)
    # __main4(path)
    # __plot([{'bmw': [1,2,3,4]}])
