import os

import numpy as np
import pandas as pd
import pytest
from auto.adac.best_car.find_best_car import (
    Column,
    Constant,
    _filtered_cars,
    _fix_missing_values_by_adding_avg,
    _fix_numeric_columns,
    _get_df_with_cost_to_own,
    _get_sorted_uniq_values,
    _get_value_scored_mappings,
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


def test_scored_parents(df_filtered_cars):
    df = get_scored_df(
        only_mentioned_cars=False,
        filtered_cars=df_filtered_cars,
        spec_file="parents.xlsx",
    )
    for car_name, suv_name in [
        ("Astra", "Grandland"),
        ("Golf", "Tiguan"),
        ("Impreza", "Forester"),
        ("Corolla", "RAV4"),
        ("i30", "Tucson"),
    ]:
        suv = df[df["name"].str.contains(suv_name)].iloc[0]
        car = df[df["name"].str.contains(car_name)].iloc[0]
        assert suv[Column.TOTAL_SCORE] > car[Column.TOTAL_SCORE]


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


def test_leon_proper_score(df_scored_de_discount):
    model = df_scored_de_discount[
        df_scored_de_discount["name"].str.contains("SEAT Leon 1.4 e-HYBRID")
    ].iloc[0]
    assert model[Column.RANGE] < 1000


def test_wheel_drive(df_scored_de_discount, df_filtered_cars):
    feature = "4x4"

    fwd = df_filtered_cars[df_filtered_cars["Antriebsart"] == "Front"].iloc[0]
    rwd = df_filtered_cars[df_filtered_cars["Antriebsart"] == "Heck"].iloc[0]
    awd = df_filtered_cars[df_filtered_cars["Antriebsart"] == "Allrad"].iloc[0]

    fwd_scored = df_scored_de_discount[df_scored_de_discount["id"] == fwd["id"]].iloc[0]
    rwd_scored = df_scored_de_discount[df_scored_de_discount["id"] == rwd["id"]].iloc[0]
    awd_scored = df_scored_de_discount[df_scored_de_discount["id"] == awd["id"]].iloc[0]
    assert fwd_scored[feature] < rwd_scored[feature] < awd_scored[feature]


def test_calc_cost_to_own(df_filtered_cars):
    auto = "subaru impreza"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1
    for _, car in df.iterrows():
        assert car[Column.CTO] > 600
        assert car[Column.CTO] < 950
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
        assert 500 < car[Column.CTO] < 850
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
    for _, car in df.iterrows():
        assert 500 < car[Column.CTO] < 900
        assert car[Column.ACCELERATION] < 14


def test_calc_cost_to_own_ceed(df_filtered_cars):
    auto = "kia ceed"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1
    for _, car in df.iterrows():
        assert car[Column.CTO] > 500
        assert car[Column.CTO] < 950
        assert car[Column.ACCELERATION] < 13


def test_calc_cost_to_own_ioniq(df_filtered_cars):
    auto = "hyundai ioniq hybrid plugin"
    df = _get_df_with_cost_to_own(auto, filtered_cars=df_filtered_cars)
    assert len(df) > 1
    for _, car in df.iterrows():
        assert car[Column.CTO] > 600
        assert car[Column.CTO] < 900


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


def test_get_sorted_uniq_values_euros():
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
        input_data, [nan, r"(\d+) Euro", "Paket", "Serie"], reverse=True
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
    assert _get_sorted_uniq_values(
        input_data, [nan, r"(\d+) Euro", "Paket", "Serie"], reverse=False
    ) == [
        nan,
        "100 Euro",
        "135 Euro",
        "155 Euro",
        "160 Euro",
        "190 Euro",
        "Paket",
        "Serie",
    ]


def test_get_sorted_uniq_values_years():
    input_data = [
        nan,
        "1 Yahre",
        "3 Yahre",
        "2 Yahre",
        "Paket",
        "Serie",
    ]
    assert _get_sorted_uniq_values(
        input_data, [nan, r"(\d+) Yahre", "Paket", "Serie"], reverse=True
    ) == [
        nan,
        "3 Yahre",
        "2 Yahre",
        "1 Yahre",
        "Paket",
        "Serie",
    ]
    assert _get_sorted_uniq_values(
        input_data, [nan, r"(\d+) Yahre", "Paket", "Serie"], reverse=False
    ) == [
        nan,
        "1 Yahre",
        "2 Yahre",
        "3 Yahre",
        "Paket",
        "Serie",
    ]


def test_get_value_scored_mappings():
    input_data = [
        nan,
        "n.b.",
        "Keine",
        "1 Yahre",
        "3 Yahre",
        "2 Yahre",
        "Paket",
        "Serie",
    ]
    assert _get_value_scored_mappings(
        input_data, [r"(\d+) Yahre", "Paket", "Serie"], reverse=True
    ) == {
        nan: 0,
        "n.b.": 0,
        "Keine": 0,
        "nicht bekannt": 0,
        "3 Yahre": 0.20,
        "2 Yahre": 0.40,
        "1 Yahre": 0.60,
        "Paket": 0.80,
        "Serie": 1,
    }
    assert _get_value_scored_mappings(
        input_data, [r"(\d+) Yahre", "Paket", "Serie"], reverse=False
    ) == {
        nan: 0,
        "n.b.": 0,
        "Keine": 0,
        "nicht bekannt": 0,
        "1 Yahre": 0.20,
        "2 Yahre": 0.40,
        "3 Yahre": 0.60,
        "Paket": 0.80,
        "Serie": 1,
    }


def test_missing_cars(df_scored_mentioned_only):
    scored = df_scored_mentioned_only
    df_input = pd.read_excel(os.path.join(os.path.dirname(__file__), "cars.xlsx"))
    index = df_input.columns.tolist().index("weight")

    bad_columns = []
    for car in df_input.columns[index + 1 :]:
        found_car = False
        for i, row in scored.iterrows():
            if _is_model_name(row["name"], car):
                found_car = True
                break
        if not found_car:
            bad_columns.append(car)

    assert bad_columns == [
        "reversed",
        "adac values, ascending order",
    ]


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
    for _, car in df.iterrows():
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
    for _, car in df.iterrows():
        is_electric = car["Motorart"] == "Elektro"
        if is_electric:
            assert car[Column.TOTAL_PRICE] < car[Column.PRICE]
        else:
            assert car[Column.TOTAL_PRICE] >= car[Column.PRICE]


@pytest.mark.skip("Not implemented")
def test_missing_features_in_input_excel():
    df_input = pd.read_excel(os.path.join(os.path.dirname(__file__), "cars.xlsx"))
    not_adac = df_input[df_input["adac column"].isna()]
    car_cols = not_adac.columns[not_adac.columns.tolist().index("weight") + 3 :]
    for _, row in not_adac.iterrows():
        feature = row["feature"]
        weight = row["weight"]
        assert row[car_cols].isna().sum() in (
            len(car_cols),
            0,
        ), f"Missing data for feature: {feature}, weight: {weight}"
