import os
from pathlib import Path
import re
from typing import DefaultDict

import pytest

from auto.mnt.mnt_sum import (
    COLUMN_CITY,
    COLUMN_COUNT,
    COLUMN_CUSTOMER,
    COLUMN_ENGINE_TYPE,
    COLUMN_REG_DATE,
    COLUMN_TRANSMISSION,
    COLUMNS,
    PRIVATE_CUSTOMER,
    get_model_stats,
    get_summary,
)

__YEARS = list(range(2018, 2025))


def test_columns():
    expected_set = DefaultDict(set)
    expected_set[2018] = {"Värv", "Käigukasti tüüp"}
    expected_set[2019] = {"Värv", "Käigukasti tüüp"}
    expected_set[2020] = {"Värv", "Käigukasti tüüp"}
    expected_set[2021] = {"Käigukasti tüüp"}
    expected_set[2022] = {"Käigukasti tüüp"}
    errors = []
    for path in Path(os.path.join(os.path.dirname(__file__), "data")).glob("**/*.xls*"):
        df = get_summary(path)
        columns = COLUMNS + [
            COLUMN_CUSTOMER,
            COLUMN_COUNT,
            COLUMN_CITY,
            COLUMN_REG_DATE,
            COLUMN_ENGINE_TYPE,
            COLUMN_TRANSMISSION,
        ]
        year = df[COLUMN_REG_DATE].unique().tolist()[0]
        diff = set(columns).difference(set(df.columns))
        if diff.difference(
            expected_set[year]
        ):  # expected_set can contain more - because in some months are more columns
            errors.append(f"Missing columns in {path.name}: {diff}")

    assert not errors, "\n".join(errors)


@pytest.mark.parametrize(
    "year,count,bestseller",
    [
        (2018, 925, "RENAULT CLIO"),
        (2019, 1194, "TOYOTA RAV4"),
        (2020, 1400, "TOYOTA RAV4"),
        (2021, 1440, "TOYOTA RAV4"),
        (2022, 1526, "TOYOTA RAV4"),
    ],
)
def test_get_model_stats(year, count, bestseller):
    top_mark, _ = bestseller.split()
    data_dir = os.path.join(os.path.dirname(__file__), "data", str(year))
    df = get_summary(data_dir)
    stats = get_model_stats(df)
    top = stats.iloc[0]
    assert top["Mark"] == top_mark
    assert top["short name"] == bestseller
    assert top["Arv"] == count


@pytest.mark.parametrize(
    "year",
    __YEARS,
)
def test_fix_names(year):
    data_dir = os.path.join(os.path.dirname(__file__), "data", str(year))
    df = get_summary(data_dir)
    marks = df["Mark"].unique().tolist()

    assert "ŠKODA" not in marks
    assert "SKODA" in marks

    assert "BMW I" not in marks
    assert "BMW" in marks


@pytest.mark.parametrize(
    "year",
    __YEARS,
)
def test_reg_date(year):
    data_dir = os.path.join(os.path.dirname(__file__), "data", str(year))
    df = get_summary(data_dir)
    assert [int(year)] == df["Esm reg aasta"].unique().tolist()


@pytest.mark.parametrize(
    "year",
    __YEARS,
)
def test_short_names(year):
    data_dir = os.path.join(os.path.dirname(__file__), "data", str(year))
    df = get_summary(data_dir)
    short_names = [
        "ALFA ROMEO GIULIA",
        "AUDI A1",
        "AUDI A6",
        "BENTLEY BENTAYGA",
        "BMW 3",
        "CITROEN C3 AIRCROSS",
        "CUPRA BORN",
        "CUPRA FORMENTOR",
        "HYUNDAI I 20",
        "HYUNDAI I 30",
        "HYUNDAI SANTA FE",
        "LEXUS ES",
        "LEXUS NX",
        "MERCEDES-BENZ AMG",
        "NISSAN LEAF",
        "OPEL ASTRA",
        "PORSCHE 911",
        "RENAULT ARKANA",
        "SEAT LEON",
        "SKODA ENYAQ",
        "SKODA OCTAVIA",
        "TOYOTA PRIUS",
        "TOYOTA YARIS CROSS",
        "VOLKSWAGEN ID.4",
    ]
    unique_names = set(df["short name"].unique().tolist())
    for grouped_name in short_names:
        filtered_names = [name for name in unique_names if grouped_name in name]
        if filtered_names:
            assert grouped_name in filtered_names
            assert len(filtered_names) == 1

    for name in [
        "AUDI RS 3",
        "AUDI S3 LIMOUSINE",
        "AUDI SQ2",
        "BMW M5",
        "HYUNDAI I 30N",
        "TOYOTA GR YARIS",
    ]:
        assert name not in unique_names


@pytest.mark.parametrize(
    "year",
    __YEARS,
)
def test_private_customers(year):
    data_dir = os.path.join(os.path.dirname(__file__), "data", str(year))
    df = get_summary(data_dir)

    values = df[COLUMN_CUSTOMER].unique().tolist()
    values_private = [v for v in values if re.search("F.+NE", v)]
    assert [PRIVATE_CUSTOMER] == values_private


@pytest.mark.parametrize(
    "year",
    __YEARS,
)
def test_cities(year):
    data_dir = os.path.join(os.path.dirname(__file__), "data", str(year))
    df = get_summary(data_dir)

    values = set(df[COLUMN_CITY].unique().tolist())

    assert not values.difference(
        {
            "Haapsalu",
            "Keila",
            "Kohtla-Järve",
            "Loksa",
            "Maardu",
            "Määramata",
            "Narva",
            "Narva-Jõesuu",
            "Paide",
            "Pärnu",
            "Rakvere",
            "Sillamäe",
            "Tallinn",
            "Tartu",
            "Viljandi",
            "Võru",
            "Tähtvere vald",
            "Põltsamaa",
            "Rapla",
        }
    )


@pytest.mark.parametrize(
    "year",
    __YEARS,
)
def test_engine_types(year):
    data_dir = os.path.join(os.path.dirname(__file__), "data", str(year))
    df = get_summary(data_dir)

    values = set(df[COLUMN_ENGINE_TYPE].unique().tolist())
    assert not values.difference(
        {
            "ELEKTER",
            "DIISEL",
            "DIISEL_HYBRIID",
            "BENSIIN",
            "BENSIIN_KATALYSAATOR",
            "BENSIIN_HYBRIID",
            "CNG",
        }
    )
