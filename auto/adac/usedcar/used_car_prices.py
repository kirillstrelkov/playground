import csv
import os
import re
from collections import defaultdict

import plotly
from pandas.core.frame import DataFrame
from plotly.graph_objs import Layout
from plotly.graph_objs.graph_objs import Scattergl
from utils.file import read_file

# https://www.pdftoexcel.com/
from utils.misc import parse_int


class ADACRelease(object):
    Y2018 = "2018"
    Y2019 = "2019"
    Y2022 = "2022"


YEARS_HEADER_2018 = ["new"] + "2017 2016 2015 2014 2013 2012 2011".split(" ")
YEARS_HEADER_2019 = ["new"] + "2018 2017 2016 2015 2014 2013 2012".split(" ")
YEARS_HEADER_2022 = ["new"] + "2020 2019 2018 2017 2016 2015 2014".split(" ")
KM_CLASSES_2018 = ["I", "II", "III", "IV", "V", "VI", "VII"]
KM_CLASSES_2019 = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "X"]
KM_CLASSES_2022 = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "X"]


def _parse_csv_row(cols, release=ADACRelease.Y2018):
    if release == ADACRelease.Y2018:
        YEARS_HEADER = YEARS_HEADER_2018
        KM_CLASSES = KM_CLASSES_2018
    elif release == ADACRelease.Y2019:
        YEARS_HEADER = YEARS_HEADER_2019
        KM_CLASSES = KM_CLASSES_2019
    elif release == ADACRelease.Y2022:
        YEARS_HEADER = YEARS_HEADER_2022
        KM_CLASSES = KM_CLASSES_2022
    else:
        assert False, f"Unsupported release: {release}"
    KM_CLASSES.reverse()
    KM_CLASSES_REGEXP = "|".join(KM_CLASSES)

    while len(cols) > 0:
        if cols[0]:
            break
        else:
            cols = cols[1:]

    model = cols[0]

    km_class = [c for c in cols if re.search(KM_CLASSES_REGEXP, c)][-1]
    km_index = cols.index(km_class)
    # split into two parts by km class
    # right side contains year prices
    # left side - data for modle
    model_part = cols[:km_index]
    # taking last 4 parts
    if " " in km_class and release == ADACRelease.Y2019:
        kw, _, _ = re.split(r"\s+", km_class)
    else:
        match_hp_kw = re.findall(r"\d+", model_part[-1])
        if len(match_hp_kw) == 2:
            kw, _ = match_hp_kw
        else:
            kw = model_part[-2]

    price_part = cols[km_index:]
    if " " in price_part[0] and release == ADACRelease.Y2018:
        price_part = price_part[0].split(" ") + price_part[1:]
    year_prices = price_part[1:]
    if not year_prices[0]:
        year_prices = year_prices[1:]

    if len(year_prices) > len(YEARS_HEADER) and release == ADACRelease.Y2018:
        year_prices = [year_prices[0]] + year_prices[-(len(YEARS_HEADER) - 1) :]
    else:
        year_prices = year_prices[: len(YEARS_HEADER) + 1]

    year_dict = dict(
        [
            (year, int(price))
            for year, price in list(zip(YEARS_HEADER, year_prices))
            if re.match(r"\d+", price)
        ]
    )

    return {"model": model, "kw": parse_int(kw), "prices": year_dict}


def __get_cars(path, release=ADACRelease.Y2018):
    expected_marks = {
        "Toyota",
        "Skoda",
        "Hyundai",
        "Lexus",
        "Mitsubishi",
        "Borgward",
        "Cadillac",
        "Daihatsu",
        "DS Automobiles",
        "Jaguar",
        "Mercedes",
        "Maserati",
        "Fiat",
        "Jeep",
        "Nissan",
        "Subaru",
        "Suzuki",
        "Opel",
        "Porsche",
        "ALPINA",
        "Infiniti",
        "Lotus",
        "Peugeot",
        "KIA",
        "SsangYong",
        "Tesla",
        "Volvo",
        "Isuzu",
        "Mazda",
        "CUPRA",
        "Honda",
        "Audi",
        "Abarth",
        "smart",
        "Land Rover",
        "VW",
        "Lancia",
        "BMW",
        "Chevrolet",
        "Renault",
        "Ford",
        "MINI",
        "Lada",
        "SEAT",
        "Alfa Romeo",
        "Dacia",
        "Citroen",
    }
    marks = set()
    mark = None
    long_model_name = None
    with open(path) as f:
        for cols in csv.reader(f):
            line = ",".join(cols)
            # DON'T use line!!!
            if len(cols) == 1 and len(cols[0]) > 0:
                long_model_name = cols[0]

            if len(cols) < 5 and len(cols) != 1:
                continue

            all_except_first_are_empty = len(cols[0]) > 0 and all(
                [len(c) == 0 for c in cols[1:]]
            )

            is_mark_name = all_except_first_are_empty and re.match("^[\w\s]+$", cols[0])
            is_model = (
                any([re.search("|".join(KM_CLASSES_2019), c) for c in cols])
                and len([c for c in cols if re.match("^\d+$", c)]) > 2
                and "Fahrzeug" not in line
            )

            if is_mark_name:
                if cols[0] in expected_marks:
                    mark = cols[0]
                    marks.add(mark)
                else:
                    print(f"Found possible mark: {cols[0]}")
            elif mark is not None and is_model:
                model = cols[0]
                if long_model_name is not None:
                    model = long_model_name + " " + model
                    long_model_name = None

                car = _parse_csv_row(cols, release)
                car["mark"] = mark

                yield car
    print(f"All marks: {marks}")


def save_parsed_adac(filename, release=ADACRelease.Y2018):
    path = os.path.join(os.path.dirname(__file__), "data", filename)
    cars = []
    for car in list(__get_cars(path, release)):
        prices = dict(
            [[str(k), "" if v is None else str(v)] for k, v in car["prices"].items()]
        )
        del car["prices"]
        car.update(prices)
        cars.append(car)
    DataFrame(cars).to_csv(path.replace(filename, "df_" + filename))


def __main():
    # NOTE: remove all data before and after main table in csv!!!
    save_parsed_adac("gebrauchtwagenpreise_2018.csv", ADACRelease.Y2018)
    save_parsed_adac("gebrauchtwagenpreise_2019.csv", ADACRelease.Y2019)
    save_parsed_adac("gebrauchtwagenpreise_2022.csv", ADACRelease.Y2022)


if __name__ == "__main__":
    __main()
