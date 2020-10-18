from auto.adac.best_car.find_best_car import (
    _filtered_cars,
    NOT_NA_COLUMNS,
    Column,
    Constant,
    _get_columns_with_euro,
    _get_df_with_cost_to_own,
    get_scored_df,
    _get_sorted_uniq_values,
    _is_model_name,
    _fix_missing_values_by_adding_avg,
    get_cars,
    _fix_numeric_columns,
    COLS_WITH_NUMERIC_DATA,
)
import numpy as np
from numpy import nan
import pandas as pd
import pytest
import os


def test_fix_missing_values_by_adding_avg():
    df = get_cars()
    df = _fix_numeric_columns(df)

    df = _fix_missing_values_by_adding_avg(df)

    for col in COLS_WITH_NUMERIC_DATA:
        assert df[pd.isna(df[col])].shape[0] < 400, f"Bad data for {col}"


def test_filtered_cars():
    df = _filtered_cars()
    for column in NOT_NA_COLUMNS:
        assert np.nan not in set(df[column].tolist())


def test_filtered_cars_proper_seats():
    df = _filtered_cars()
    seats_val = set(df[Column.SEATS].tolist())
    assert 2 not in seats_val
    assert 3 not in seats_val


def test_filtered_cars_proper_transmission():
    df = _filtered_cars()
    seats_val = set(df[Column.TRANSMISSION].tolist())
    assert Constant.TRANSMISSION_MANUAL not in seats_val


def test_get_columns_with_euro():
    cols = _get_columns_with_euro()
    assert "Navigation" in cols
    assert "Marke" not in cols
    assert "Leergewicht (EU)" not in cols


def test_calc_cost_to_own():
    auto = "subaru impreza"
    df = _get_df_with_cost_to_own(auto)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert car[Column.MY_M_COSTS] > 500
        assert car[Column.MY_M_COSTS] < 700
        assert car[Column.ACCELERATION] < 13
        assert car[Column.ACCELERATION] > 8
        assert car[Column.RANGE] > 500
        assert car[Column.TOTAL_PRICE] > 0

    assert not df[df[Column.NAME].str.contains("Subaru Impreza 2.0i Exclusive")].empty


def test_calc_cost_to_own_208():
    auto = "Peugeot 208"
    df = _get_df_with_cost_to_own(auto)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert car[Column.MY_M_COSTS] > 300
        assert car[Column.MY_M_COSTS] < 500


def test_calc_cost_to_own_corsa():
    auto = "opel corsa"
    df = _get_df_with_cost_to_own(auto)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert car[Column.MY_M_COSTS] > 300
        assert car[Column.MY_M_COSTS] < 500
        assert car[Column.ACCELERATION] < 11


def test_calc_cost_to_own_ceed():
    auto = "kia ceed"
    df = _get_df_with_cost_to_own(auto)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert car[Column.MY_M_COSTS] > 300
        assert car[Column.MY_M_COSTS] < 530
        assert car[Column.ACCELERATION] < 12


def test_calc_cost_to_own_ioniq():
    auto = "hyundai ioniq hybrid plugin"
    df = _get_df_with_cost_to_own(auto)
    assert len(df) > 1
    for index, car in df.iterrows():
        assert car[Column.MY_M_COSTS] > 400
        assert car[Column.MY_M_COSTS] < 600


def test_calc_cost_to_own_mb_a():
    auto = "Mercedes A"
    df = _get_df_with_cost_to_own(auto)
    assert not df[df[Column.NAME].str.contains("Mercedes A")].empty


def test_calc_cost_to_own_bmw_1():
    auto = "Bmw 1"
    df = _get_df_with_cost_to_own(auto)
    assert len(df) > 1


def test_calc_cost_to_own_3008():
    auto = "peugeot 3008"
    df = _get_df_with_cost_to_own(auto)
    assert len(df) >= 2


@pytest.mark.skip("TODO")
def test_euro_columns():
    df = _get_df_with_cost_to_own()
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


def test_missing_cars():
    scored = get_scored_df()
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


def test_score():
    scored = get_scored_df()
    for i, row in scored.iterrows():
        assert row[Column.TOTAL_SCORE] > 0
        assert row[Column.TOTAL_SCORE] < 400
        assert pd.isna(row["Acceleration <10"]) or row["Acceleration <10"] >= 0
        assert row["adaptive lights"] >= 0
        assert row["LED matrix"] >= 0
        assert "mobile support" not in row.index.tolist()


def test_score_all_cars():
    scored = get_scored_df(False)
    for i, row in scored.iterrows():
        assert row[Column.TOTAL_SCORE] > 0
        assert row[Column.TOTAL_SCORE] < 400
        assert pd.isna(row["Acceleration <10"]) or row["Acceleration <10"] >= 0
        assert row["adaptive lights"] >= 0
        assert "mobile support" not in row.index.tolist()


def test_score_all_cars_de():
    scored = get_scored_df(de_discount=True)
    for i, row in scored.iterrows():
        assert row[Column.TOTAL_SCORE] > 0
        assert row[Column.TOTAL_SCORE] < 400
        assert pd.isna(row["Acceleration <10"]) or row["Acceleration <10"] >= 0
        assert row["adaptive lights"] >= 0
        assert "mobile support" not in row.index.tolist()


def test_calc_cost_to_own_ioniq_with_german_discount():
    auto = "hyundai ioniq"
    df = _get_df_with_cost_to_own(auto, de_discount=True)
    assert len(df) > 1
    for index, car in df.iterrows():
        is_hybrid = car["Motorart"] == "PlugIn-Hybrid"
        if is_hybrid:
            assert car[Column.TOTAL_PRICE] < car[Column.PRICE]
        else:
            assert (
                pd.isna(car[Column.TOTAL_PRICE])
                or car[Column.TOTAL_PRICE] >= car[Column.PRICE]
            )


def test_calc_cost_to_own_corsa_e_with_german_discount():
    auto = "opel corsa-e"
    df = _get_df_with_cost_to_own(auto, de_discount=True)
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
    has_not_set = not_adac[not_adac.apply(lambda x: x[car_cols].isna().any(), axis=1)]
    for _, row in has_not_set.iterrows():
        feature = row["feature"]
        weight = row["weight"]
        print(f"Missing data for feature: {feature}, weight: {weight}")
    assert has_not_set.empty


# TODO: find and fix missing data in adac!!
def test_missing_features_in_adac():
    df_input = pd.read_excel(os.path.join(os.path.dirname(__file__), "cars.xlsx"))
    cols = set(["name"] + df_input["adac column"].dropna().to_list()) - set(
        "LED-Scheinwerfer,Navigation,Querverkehrassistent,Aktive Kopfstützen,Fußgängererkennung,Kurvenlicht,Notbremsassistent,Spurhalteassistent,Stauassistent,Verkehrsschild-Erkennung".split(
            ","
        )
    )
    df = _get_df_with_cost_to_own()

    df_bad = pd.DataFrame()
    for i, row in df[cols].iterrows():
        nas = row[pd.isna(row[cols])]
        s_row = row.filter(["name"]).append(nas)
        if nas.size > 0:
            df_bad = df_bad.append(s_row, ignore_index=True)
    df_bad.to_excel("/tmp/bad.xlsx")
    assert df_bad.shape[0] / float(df.shape[0]) < 0.10


def test_get_scored_df_no_na():
    df = get_scored_df(only_mentioned_cars=False)
    df_bad = df[df.apply(lambda x: pd.isna(x).any(), axis=1)]
    cols = df_bad.columns[1:]

    #  remove columns without NAs
    cols = cols[df_bad[cols].isna().any().values]
    df_bad = df_bad[["name"] + cols.to_list()]

    # replace NA with True
    df_bad[cols] = df_bad[cols].apply(lambda x: pd.isna(x[cols]), axis=1)
    df_bad.to_excel("/tmp/bad.xlsx")
    assert df_bad.shape[0] / float(df.shape[0]) < 0.10

