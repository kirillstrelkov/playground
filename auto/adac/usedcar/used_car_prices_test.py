from unittest import TestCase

from auto.adac.usedcar.used_car_prices import ADACRelease, _parse_csv_row

import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import os


def assert_in_hash(member, container):
    member = list(member.items())
    container = list(container.items())
    for m in member:
        assert m in container


def assert_model(
    line, expected_hash_in_data, expected_hash_in_prices, release=ADACRelease.Y2018
):
    data = _parse_csv_row(line.split(","), release=release)
    assert_in_hash(expected_hash_in_data, data)
    assert_in_hash(expected_hash_in_prices, data["prices"])


def test_2018_audi_a8_1():
    assert_model(
        "A8 L 4.0 TFSI cod quattro tiptronic (D4),,,,4,309,(420),VI 100200,,,,,,33950,30750,",
        {"model": "A8 L 4.0 TFSI cod quattro tiptronic (D4)", "kw": 309},
        {"new": 100200, "2013": 33950, "2012": 30750},
    )


def test_2018_audi_a8_2():
    assert_model(
        "A8 L 4.0 TFSI cod quattro tiptronic (D4),,,,4,320,(435),VI 110300,,56150,50750,43650,38400,34500,,",
        {"model": "A8 L 4.0 TFSI cod quattro tiptronic (D4)", "kw": 320},
        {
            "new": 110300,
            "2017": 56150,
            "2016": 50750,
            "2015": 43650,
            "2014": 38400,
            "2013": 34500,
        },
    )


def test_2018_audi_a8_3():
    assert_model(
        "A8 3.0 TDI quattro tiptronic (D4),,,,4,193,(262),VI,84000,40250,36700,33400,,,,",
        {"model": "A8 3.0 TDI quattro tiptronic (D4)", "kw": 193},
        {"new": 84000, "2017": 40250, "2016": 36700, "2015": 33400},
    )


def test_2019_d_max():
    assert_model(
        "D-Max 2.5 Diesel Double Cab Basic 4WD,4,120  (163),VI,29350,,18850,17150,15450,14050,12400,11300,,,,",
        {"model": "D-Max 2.5 Diesel Double Cab Basic 4WD", "kw": 120},
        {
            "new": 29350,
            "2017": 18850,
            "2016": 17150,
            "2015": 15450,
            "2014": 14050,
            "2013": 12400,
            "2012": 11300,
        },
        release=ADACRelease.Y2019,
    )


def test_2019_gti():
    assert_model(
        ",Golf GTI  (VII) GTI,3,169  (230),IV,30425,22000,19650,,,,,,,",
        {"model": "Golf GTI  (VII) GTI", "kw": 169},
        {"new": 30425, "2018": 22000, "2017": 19650},
        release=ADACRelease.Y2019,
    )


def test_2018_audi_a3():
    assert_model(
        "A3 Sportback 2.0 TDI (8V),,5,110,(150),IV,30550,18050,16450,,,,",
        {"model": "A3 Sportback 2.0 TDI (8V)", "kw": 110},
        {"new": 30550, "2017": 18050, "2016": 16450},
    )


def test_2019_jumper():
    assert_model(
        "Jumper Kombi Club 33 HDi 130 FAP Hochdach mittel,4,96  (130) VIII,,38468,,,,,12150,10200,9600,,,",
        {"model": "Jumper Kombi Club 33 HDi 130 FAP Hochdach mittel", "kw": 96},
        {"new": 38468, "2014": 12150, "2013": 10200, "2012": 9600},
        release=ADACRelease.Y2019,
    )


def test_2019_lada():
    assert_model(
        "4x4 5-Türer 1.7  (VAZ 2131),5,61  (83),IV,12990,8950,7975,,,,,,,,",
        {"model": "4x4 5-Türer 1.7  (VAZ 2131)", "kw": 61},
        {"new": 12990, "2018": 8950, "2017": 7975},
        release=ADACRelease.Y2019,
    )


def test_lada():
    df = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "data/df_gebrauchtwagenpreise_2019.csv")
    )
    assert df[df["mark"] == "Lada"].shape[0] == 20


def test_tesla():
    df = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "data/df_gebrauchtwagenpreise_2019.csv")
    )
    assert df[df["mark"] == "Tesla"].shape[0] == 22
