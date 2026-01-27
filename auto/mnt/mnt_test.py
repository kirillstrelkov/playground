import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pytest

from auto.mnt.mnt_sum import (
    COLUMN_CITY,
    COLUMN_COUNT,
    COLUMN_CUSTOMER,
    COLUMN_ENGINE_TYPE,
    COLUMN_MARK,
    COLUMN_REG_DATE,
    COLUMN_SHORT_NAME,
    COLUMN_SUV,
    COLUMN_TRANSMISSION,
    COLUMNS,
    DATA_DIR,
    DATA_DIR_YEARS,
    PRIVATE_CUSTOMER,
    YEARS,
    _fix_name,
    get_history_df,
    get_model_stats,
)

__DATA_DIR_YEARS = DATA_DIR / "private"


@pytest.fixture(scope="module")
def history_df() -> pd.DataFrame:
    return get_history_df()


def test_columns(history_df: pd.DataFrame) -> None:
    expected_set = defaultdict(set)
    expected_set[2018] = {"Värv", "Käigukasti tüüp"}
    expected_set[2019] = {"Värv", "Käigukasti tüüp"}
    expected_set[2020] = {"Värv", "Käigukasti tüüp"}
    expected_set[2021] = {"Käigukasti tüüp"}
    expected_set[2022] = {"Käigukasti tüüp"}

    columns = [
        *COLUMNS,
        COLUMN_CUSTOMER,
        COLUMN_COUNT,
        COLUMN_CITY,
        COLUMN_REG_DATE,
        COLUMN_ENGINE_TYPE,
        COLUMN_TRANSMISSION,
    ]
    for col in columns:
        assert len(history_df[col].unique()) > 0, f"Missing data in column: {col}"


@pytest.mark.parametrize(
    ("year", "count", "bestseller"),
    [
        (2018, 925, "RENAULT CLIO"),
        (2019, 1194, "TOYOTA RAV4"),
        (2020, 1400, "TOYOTA RAV4"),
        (2021, 1440, "TOYOTA RAV4"),
        (2022, 1526, "TOYOTA RAV4"),
        (2023, 1311, "TOYOTA RAV4"),
        (2024, 1730, "SKODA OCTAVIA"),
        (2025, 775, "TOYOTA COROLLA"),
    ],
)
def test_get_model_stats(history_df: pd.DataFrame, year: int, count: int, bestseller: str) -> None:
    top_mark, _ = bestseller.split()
    df = history_df[history_df[COLUMN_REG_DATE] == year]
    stats = get_model_stats(df)
    top = stats.iloc[0]
    model = (top[COLUMN_MARK], top[COLUMN_SHORT_NAME], top[COLUMN_COUNT])
    assert model == (top_mark, bestseller, count), (
        f"Year {year} bestseller mismatch: {model}, expected {(top_mark, bestseller, count)}"
    )


def test_fix_names(history_df: pd.DataFrame) -> None:
    marks = history_df[COLUMN_MARK].unique().tolist()

    assert "ŠKODA" not in marks
    assert "SKODA" in marks

    assert "BMW I" not in marks
    assert "BMW" in marks


def test_reg_date(history_df: pd.DataFrame) -> None:
    years = history_df[COLUMN_REG_DATE].unique().tolist()
    assert years == YEARS


def test_short_names(history_df: pd.DataFrame) -> None:
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
    unique_names = set(history_df[COLUMN_SHORT_NAME].unique().tolist())

    # use this file for manual inspection if needed
    Path(DATA_DIR_YEARS / "unique_names.csv").write_text("\n".join(sorted(unique_names)), encoding="utf-8")

    single_names = [name for name in unique_names if len(name.split()) < 2]
    assert single_names == ["OMAVALMISTATUD"], f"Found short names with less than 2 words: {short_names}"

    make_twice = [name for name in unique_names if len(name.split()) > 1 and name.split()[0] == name.split()[1]]
    assert not make_twice, f"Found names with make twice: {make_twice}"

    for grouped_name in short_names:
        filtered_names = [name for name in unique_names if grouped_name in name]
        if filtered_names:
            assert grouped_name in filtered_names
            assert len(filtered_names) == 1

    for name in [
        "AUDI RS 3",
        "AUDI S3 LIMOUSINE",
        "AUDI SQ2",
        "HYUNDAI IONIQ5 N",
        "BYD SEAL U DM-I",
        "DODGE DURANGO SRT",
        "JEEP GRAND CHEROKEE SRT",
        "MASERATI GRECALE TROFEO",
        "PEUGEOT 208 R2",
        "TESLA MOTORS MODEL X",
        "SWM G01 PRO",
        "TOYOTA AYGO X",
        "BMW M5",
        "HYUNDAI I 30N",
        "TOYOTA GR YARIS",
    ]:
        assert name not in unique_names


def test_private_customers(history_df: pd.DataFrame) -> None:
    values = history_df[COLUMN_CUSTOMER].unique().tolist()
    values_private = [v for v in values if re.search("F.+NE", v)]
    assert values_private == [PRIVATE_CUSTOMER]


def test_cities(history_df: pd.DataFrame) -> None:
    values = set(history_df[COLUMN_CITY].unique().tolist())

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
        },
    )


def test_engine_types(history_df: pd.DataFrame) -> None:
    values = set(history_df[COLUMN_ENGINE_TYPE].unique().tolist())
    assert not values.difference(
        {
            "ELEKTER",
            "DIISEL",
            "DIISEL_HYBRIID",
            "BENSIIN",
            "BENSIIN_KATALYSAATOR",
            "BENSIIN_HYBRIID",
            "CNG",
        },
    )


def test_input_data() -> None:
    years = [y for y in DATA_DIR_YEARS.glob("*") if y.is_dir()]
    assert sorted([int(y.name) for y in years]) == YEARS

    for year_dir in years:
        months = year_dir.glob("*")
        assert len(list(months)) == 12, f"Year {year_dir.name} does not have 12 months"


def test_fix_name() -> None:
    data = """
ALFA ROMEO GIULIA QUADRIFOGLIO VERDE, ALFA ROMEO GIULIA
ALFA ROMEO STELVIO QUADRIFOGLIO, ALFA ROMEO STELVIO
ASTON MARTIN VANTAGE F1 EDITION, ASTON MARTIN VANTAGE
AUDI A1 ALLSTREET, AUDI A1
AUDI A3 40 TFSIE, AUDI A3
AUDI A3 ALLSTREET PHEV 150, AUDI A3
AUDI A3 SPORTBACK PHEV 150, AUDI A3
AUDI A4 ALLROAD QUATTRO, AUDI A4
AUDI A4 AVANT G-TRON, AUDI A4
AUDI A5 LIM 220KW TFSI E, AUDI A5
AUDI A6 AVANT 270KW TFSI E, AUDI A6
AUDI A6 AV E-TRON PERFORMANCE, AUDI A6
AUDI A6 SB E-TRON PERFORMANCE, AUDI A6
AUDI A8L, AUDI A8
AUDI E-TRON, AUDI E-TRON
AUDI E-TRON 55, AUDI E-TRON
AUDI E-TRON GT, AUDI E-TRON
AUDI E-TRON S, AUDI E-TRON
AUDI E-TRON S SPORTBACK, AUDI E-TRON
AUDI E-TRON SPORTBACK 55, AUDI E-TRON
AUDI RS 3 LIMOUSINE, AUDI A3
AUDI RS 7 SPORTBACK, AUDI A7
AUDI SQ5, AUDI Q5
AUDI SQ8, AUDI Q8
AUDI S E-TRON GT, AUDI E-TRON
BENTLEY BENTAYGA AZURE V8, BENTLEY BENTAYGA
BMW 116D, BMW 1
BMW 330D XDRIVE, BMW 3
BMW 330E, BMW 3
BMW IX XDRIVE50, BMW IX
BMW IX2 XDRIVE30, BMW IX2
BMW M140I XDRIVE, BMW 1
BMW X1 SDRIVE20I, BMW X1
BMW X7 M60I XDRIVE, BMW X7
BYD SEAL U, BYD SEAL U
BYD SEAL U DM-I, BYD SEAL U
HYUNDAI I 20, HYUNDAI I20
HYUNDAI I 20 N, HYUNDAI I20
HYUNDAI I 30, HYUNDAI I30
HYUNDAI I 30N, HYUNDAI I30
HYUNDAI I40, HYUNDAI I40
HYUNDAI NEXO, HYUNDAI NEXO
HYUNDAI TUCSON, HYUNDAI TUCSON
HYUNDAI IONIQ5 N, HYUNDAI IONIQ5
JEEP GRAND CHEROKEE, JEEP GRAND CHEROKEE
JEEP GRAND CHEROKEE SRT, JEEP GRAND CHEROKEE
JEEP GRAND CHEROKEE TRACKHAWK, JEEP GRAND CHEROKEE
KG MOBILITY TORRES, KG MOBILITY TORRES
KG MOBILITY TORRES EVX, KG MOBILITY TORRES
LAND ROVER RANGE ROVER, LAND ROVER RANGE ROVER
LAND ROVER RANGE ROVER EVOQUE, LAND ROVER RANGE ROVER EVOQUE
LAND ROVER RANGE ROVER SPORT, LAND ROVER RANGE ROVER SPORT
LAND ROVER RANGE ROVER VELAR, LAND ROVER RANGE ROVER VELAR
LYNK&CO LYNK & CO 01, LYNK&CO 01
LYNK&CO LYNK & CO 02, LYNK&CO 02
MERCEDES-BENZ A 250 E, MERCEDES-BENZ A
MERCEDES-BENZ AMG A 35, MERCEDES-BENZ A
TESLA MODEL X, TESLA MODEL X
TESLA MOTORS MODEL X, TESLA MODEL X
LEXUS ES300H, LEXUS ES
""".strip()
    for line in data.splitlines():
        name, expected = line.strip().split(", ")
        fixed_name = _fix_name(name)
        assert fixed_name == expected.strip(), f"Fix name failed: {name} -> {fixed_name}, expected: {expected}"


def test_suv(history_df: pd.DataFrame) -> None:
    unique_names = set(history_df[history_df[COLUMN_SUV]][COLUMN_SHORT_NAME].unique().tolist())

    suvs = """
MERCEDES-BENZ GLB
TESLA MODEL Y
PEUGEOT 2008
VOLKSWAGEN TIGUAN
""".strip()
    for suv in suvs.splitlines():
        assert suv in unique_names, f"SUV model missing: {suv}"
