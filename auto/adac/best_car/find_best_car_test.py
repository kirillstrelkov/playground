import os

import numpy as np
import pandas as pd
import pytest
from auto.adac.best_car.find_best_car import (
    NOT_NA_COLUMNS,
    Column,
    Constant,
    _filtered_cars,
    _fix_missing_values_by_adding_avg,
    _fix_numeric_columns,
    _get_columns_with_euro,
    _get_df_with_cost_to_own,
    _get_sorted_uniq_values,
    _is_model_name,
    get_cars,
    get_scored_df,
)
from numpy import nan


@pytest.fixture
def df_cars():
    return get_cars()


@pytest.fixture
def df_filtered_cars(df_cars):
    return _filtered_cars(df=df_cars)


@pytest.fixture
def df_scored_de_discount(df_filtered_cars):
    return get_scored_df(
        only_mentioned_cars=False,
        de_discount=True,
        keep_columns=["id"],
        filtered_cars=df_filtered_cars,
    )


@pytest.fixture
def df_scored(df_filtered_cars):
    return get_scored_df(only_mentioned_cars=False, filtered_cars=df_filtered_cars)


@pytest.fixture
def df_scored_mentioned_only(df_filtered_cars):
    return get_scored_df(only_mentioned_cars=True, filtered_cars=df_filtered_cars)


def test_join_adac_and_score(df_cars, df_scored_de_discount):
    df_joined = pd.merge(
        df_cars, df_scored_de_discount.drop("name", axis=1), on="id", how="left"
    )
    assert df_joined[df_joined["name"].str.contains("Impreza")].shape[0] >= 5


def test_all_vs_mentioned(df_scored, df_scored_mentioned_only):
    scored_rows = df_scored.shape[0]
    scored_mentioned_rows = df_scored_mentioned_only.shape[0]
    assert scored_rows > scored_mentioned_rows


def test_model3_score_better_than_impreza(df_scored_de_discount):
    model = df_scored_de_discount[
        df_scored_de_discount["name"].str.contains("Tesla")
    ].iloc[0]
    assert model[Column.TOTAL_SCORE] > 186
    assert model[Column.RANGE] >= 50 / 15 * 100
    assert model[Column.EURO_PER_SCORE] < 190


def test_no_combi(df_filtered_cars):
    for car in ["Octavia (IV) Combi", "VW Golf Variant"]:
        rows, cols = df_filtered_cars[df_filtered_cars["name"].str.contains(car)].shape
        assert rows == 0


def test_leon_proper_score(df_scored_de_discount):
    model = df_scored_de_discount[
        df_scored_de_discount["name"].str.contains("SEAT Leon 1.4 e-HYBRID")
    ].iloc[0]
    assert model[Column.RANGE] < 1000


def test_fix_missing_values_by_adding_avg(df_cars):
    df = df_cars
    df = _fix_numeric_columns(df)

    df = _fix_missing_values_by_adding_avg(df)

    for col in Constant.COLS_WITH_NUMERIC_DATA:
        if col == Column.BATTERY_CAPACITY:
            continue

        assert df[pd.isna(df[col])].shape[0] < 400, f"Bad data for {col}"


def test_filtered_cars(df_filtered_cars):
    for column in NOT_NA_COLUMNS:
        assert np.nan not in set(df_filtered_cars[column].tolist())


def test_filtered_cars_proper_seats(df_filtered_cars):
    seats_val = set(df_filtered_cars[Column.SEATS].tolist())
    assert 2 not in seats_val
    assert 3 not in seats_val


def test_filtered_cars_proper_transmission(df_filtered_cars):
    seats_val = set(df_filtered_cars[Column.TRANSMISSION].tolist())
    assert Constant.TRANSMISSION_MANUAL not in seats_val


def test_get_columns_with_euro():
    cols = _get_columns_with_euro()
    assert "Navigation" in cols
    assert "Marke" not in cols
    assert "Leergewicht (EU)" not in cols


def test_calc_cost_to_own(df_filtered_cars):
    auto = "subaru impreza"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert car[Column.MY_M_COSTS] > 500
        assert car[Column.MY_M_COSTS] < 700
        assert car[Column.ACCELERATION] < 13
        assert car[Column.ACCELERATION] > 8
        assert car[Column.RANGE] > 500
        assert car[Column.TOTAL_PRICE] > 0

    assert not df[df[Column.NAME].str.contains("Subaru Impreza 2.0i Exclusive")].empty


def test_calc_cost_to_own_208(df_filtered_cars):
    auto = "Peugeot 208"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1
    for _, car in df.iterrows():
        assert 300 < car[Column.MY_M_COSTS] < 510
        capacity = car[Column.BATTERY_CAPACITY]
        tank = car[Column.FUEL_TANK_SIZE]
        if car[Column.ENGINE_TYPE] == "Elektro":
            assert pd.notna(capacity)
            assert pd.isna(tank)
        else:
            assert pd.notna(tank)
            assert pd.isna(capacity)


def test_calc_cost_to_own_corsa(df_filtered_cars):
    auto = "opel corsa"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert 300 < car[Column.MY_M_COSTS] < 500
        assert car[Column.ACCELERATION] < 11


def test_calc_cost_to_own_ceed(df_filtered_cars):
    auto = "kia ceed"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert car[Column.MY_M_COSTS] > 300
        assert car[Column.MY_M_COSTS] < 550
        assert car[Column.ACCELERATION] < 12


def test_calc_cost_to_own_ioniq(df_filtered_cars):
    auto = "hyundai ioniq hybrid plugin"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert car[Column.MY_M_COSTS] > 400
        assert car[Column.MY_M_COSTS] < 600


def test_calc_cost_to_own_mb_a(df_filtered_cars):
    auto = "Mercedes A"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert not df[df[Column.NAME].str.contains("Mercedes A")].empty


def test_calc_cost_to_own_bmw_1(df_filtered_cars):
    auto = "Bmw 1"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1


def test_calc_cost_to_own_3008(df_filtered_cars):
    auto = "peugeot 3008"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) >= 2


@pytest.mark.skip("TODO")
def test_euro_columns(df_filtered_cars):
    df = _get_df_with_cost_to_own(filtered_cars=df_filtered_cars)
    for col in df.columns:
        for i, row in df.iterrows():
            val = row[col]
            if type(val) == str:
                assert "euro" not in row[col].lower(), f"Found euro in '{col}'"


def test_get_sorted_uniq_values():
    input_data = [
        nan,
        "160 Euro",
        "190 Euro",
        "135 Euro",
        "100 Euro",
        "155 Euro",
        "Paket",
        "Serie",
    ]
    assert _get_sorted_uniq_values(
        input_data, [nan, r"(\d+) Euro", "Paket", "Serie"], True
    ) == [
        nan,
        "190 Euro",
        "160 Euro",
        "155 Euro",
        "135 Euro",
        "100 Euro",
        "Paket",
        "Serie",
    ]


def test_missing_cars(df_scored_mentioned_only):
    scored = df_scored_mentioned_only
    df_input = pd.read_excel(os.path.join(os.path.dirname(__file__), "cars.xlsx"))
    index = df_input.columns.tolist().index("weight")

    bad_cars = []
    for car in df_input.columns[index + 1 :]:
        found_car = False
        for i, row in scored.iterrows():
            if _is_model_name(row["name"], car):
                found_car = True
                break
        if not found_car:
            bad_cars.append(car)

    assert len(bad_cars) == 0


def test_score(df_scored):
    scored = df_scored
    for i, row in scored.iterrows():
        assert row[Column.TOTAL_SCORE] > 0
        assert row[Column.TOTAL_SCORE] < 400
        assert pd.isna(row["Acceleration <10"]) or row["Acceleration <10"] >= 0
        assert row["adaptive lights"] >= 0
        assert "LED matrix" in row.index.tolist()
        assert "mobile support" not in row.index.tolist()


def test_score_all_cars(df_scored):
    scored = df_scored
    for i, row in scored.iterrows():
        assert row[Column.TOTAL_SCORE] > 0
        assert row[Column.TOTAL_SCORE] < 400
        assert pd.isna(row["Acceleration <10"]) or row["Acceleration <10"] >= 0
        assert row["adaptive lights"] >= 0
        assert "mobile support" not in row.index.tolist()


def test_score_all_cars_de(df_scored_de_discount):
    for i, row in df_scored_de_discount.iterrows():
        assert row[Column.TOTAL_SCORE] > 0
        assert row[Column.TOTAL_SCORE] < 400
        assert pd.isna(row["Acceleration <10"]) or row["Acceleration <10"] >= 0
        assert row["adaptive lights"] >= 0
        assert "mobile support" not in row.index.tolist()


def test_calc_cost_to_own_ioniq_with_german_discount(df_filtered_cars):
    auto = "hyundai ioniq"
    df = _get_df_with_cost_to_own(
        auto, de_discount=True, filtered_cars=df_filtered_cars
    )
    assert len(df) > 1
    for index, car in df.iterrows():
        is_electric = car["Motorart"] in ["PlugIn-Hybrid", "Elektro"]
        if is_electric:
            assert car[Column.TOTAL_PRICE] < car[Column.PRICE]
        else:
            assert (
                pd.isna(car[Column.TOTAL_PRICE])
                or car[Column.TOTAL_PRICE] >= car[Column.PRICE]
            )


def test_calc_cost_to_own_corsa_e_with_german_discount(df_filtered_cars):
    auto = "opel corsa-e"
    df = _get_df_with_cost_to_own(
        auto, de_discount=True, filtered_cars=df_filtered_cars
    )
    assert len(df) > 1
    for index, car in df.iterrows():
        is_electric = car["Motorart"] == "Elektro"
        if is_electric:
            assert car[Column.TOTAL_PRICE] < car[Column.PRICE]
        else:
            assert car[Column.TOTAL_PRICE] >= car[Column.PRICE]


def test_missing_features_in_input_excel():
    df_input = pd.read_excel(os.path.join(os.path.dirname(__file__), "cars.xlsx"))
    not_adac = df_input[df_input["adac column"].isna()]
    car_cols = not_adac.columns[not_adac.columns.tolist().index("weight") + 1 :]
    for _, row in not_adac.iterrows():
        feature = row["feature"]
        weight = row["weight"]
        assert row[car_cols].isna().sum() in (
            len(car_cols),
            0,
        ), f"Missing data for feature: {feature}, weight: {weight}"


@pytest.mark.skip("TODO: find and fix missing data in adac!!")
def test_missing_features_in_adac(df_filtered_cars):
    df_input = pd.read_excel(os.path.join(os.path.dirname(__file__), "cars.xlsx"))
    cols = set(["name"] + df_input["adac column"].dropna().to_list()) - set(
        "LED-Scheinwerfer,Navigation,Querverkehrassistent,Aktive Kopfstützen,Fußgängererkennung,Kurvenlicht,Notbremsassistent,Spurhalteassistent,Stauassistent,Verkehrsschild-Erkennung".split(
            ","
        )
    )
    df = _get_df_with_cost_to_own(filtered_cars=df_filtered_cars)

    df_bad = pd.DataFrame()
    for i, row in df[cols].iterrows():
        nas = row[pd.isna(row[cols])]
        s_row = row.filter(["name"]).append(nas)
        if nas.size > 0:
            df_bad = df_bad.append(s_row, ignore_index=True)
    df_bad.to_excel("/tmp/bad.xlsx")
    assert df_bad.shape[0] / float(df.shape[0]) < 0.10


@pytest.mark.skip("TODO: find and fix missing data in adac!!")
def test_get_scored_df_no_na(df_scored):
    df = df_scored
    df_bad = df[df.apply(lambda x: pd.isna(x).any(), axis=1)]
    cols = df_bad.columns[1:]

    #  remove columns without NAs
    cols = cols[df_bad[cols].isna().any().values]
    df_bad = df_bad[["name"] + cols.to_list()]

    # replace NA with True
    df_bad[cols] = df_bad[cols].apply(lambda x: pd.isna(x[cols]), axis=1)
    df_bad.to_excel("/tmp/bad.xlsx")
    assert df_bad.shape[0] / float(df.shape[0]) < 0.10
