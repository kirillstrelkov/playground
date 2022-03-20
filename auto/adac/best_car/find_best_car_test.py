import pandas as pd
import pytest
from auto.adac.best_car.adac_test import FEATURES_PATH
from auto.adac.best_car.find_best_car import (
    NAME_SPLITTER,
    ZERO_POINTS_MAPPING,
    Column,
    _convert_to_float,
    _filter_by_models,
    _filtered_cars,
    _get_fixed_and_scaled_column_name,
    _get_fixed_column_name,
    _get_fixed_scaled_and_weighted_column_name,
    _get_mappings,
    get_cars,
    get_scored_df,
    get_weighted_column_name,
)
from auto.adac.best_car.utils import (
    COLUMN_FEATURE,
    COLUMN_FEATURE_TYPE,
    COLUMN_FEATURE_WEIGHT,
    FeatureType,
)
from numpy import nan


@pytest.fixture
def df_cars():
    return get_cars()


@pytest.fixture
def df_filtered_cars(df_cars):
    return _filtered_cars(df=df_cars)


@pytest.fixture
def df_scored_de_discount_minmax_scaler(df_filtered_cars):
    return get_scored_df(df_filtered_cars, de_discount=True)


@pytest.fixture
def df_scored_parent(df_filtered_cars):
    return get_scored_df(df_filtered_cars, feature_file_name="feature_parents.csv")


@pytest.fixture
def df_features():
    return pd.read_csv(FEATURES_PATH)


def test_scored_parents_suv_is_better(df_scored_parent):
    df = df_scored_parent
    for car_name, suv_name in [
        ("Astra", "Grandland"),
        ("i30", "Tucson"),
        ("Impreza", "Forester"),
        ("Golf", "Tiguan"),
    ]:
        car = df[df["name"].str.contains(car_name)].iloc[0]
        suv = df[df["name"].str.contains(suv_name)].iloc[0]
        assert (
            car[Column.TOTAL_SCORE] < suv[Column.TOTAL_SCORE]
        ), f"Car {car['name']}, {car.id} is better {suv['name']}, {suv.id}"


def test_ioniq_plugin_consumption_fixed(df_scored_de_discount_minmax_scaler):
    car_plugin = df_scored_de_discount_minmax_scaler[
        df_scored_de_discount_minmax_scaler["name"].str.contains(
            "Hyundai IONIQ PlugIn-Hybrid Prime"
        )
    ].iloc[0]

    assert car_plugin[_get_fixed_column_name(Column.CONSUPTION_COMBINED_WLTP)] > 3


def test_all_nans_are_properly_fix_scaled_weighted(
    df_scored_de_discount_minmax_scaler,
):
    weighted_columns = [
        col for col in df_scored_de_discount_minmax_scaler.columns if "weighted" in col
    ]
    for wcol in weighted_columns:
        df_weighted_na = df_scored_de_discount_minmax_scaler[
            df_scored_de_discount_minmax_scaler[wcol].isin(ZERO_POINTS_MAPPING)
        ]
        names = wcol.split(NAME_SPLITTER)
        for i in range(1, len(names) - 1):
            prev_name = NAME_SPLITTER.join(names[: len(names) - i])
            if prev_name in df_weighted_na.columns:
                df_empty = df_weighted_na[
                    ~df_weighted_na[prev_name].isin(ZERO_POINTS_MAPPING)
                ]
                assert df_empty.empty


def test_scaled_columns_minmax(df_scored_de_discount_minmax_scaler):
    df = df_scored_de_discount_minmax_scaler
    columns = [c for c in df.columns if c.endswith("scaled")]
    for col in columns:
        assert df[col].min() >= -0.01
        assert df[col].max() <= 1.01


def test_max_weights(df_scored_de_discount_minmax_scaler, df_features):
    df = df_scored_de_discount_minmax_scaler
    for _, row in df_features.iterrows():
        feature = row[COLUMN_FEATURE]
        type = row[COLUMN_FEATURE_TYPE]
        weight = row[COLUMN_FEATURE_WEIGHT]
        if type != FeatureType.SKIP:
            max_feature = df[get_weighted_column_name(df, feature)].max()
            assert max_feature < weight + 0.01


def test_tesla_scaled_consumption_better_than_subaru(
    df_scored_de_discount_minmax_scaler,
):
    df = df_scored_de_discount_minmax_scaler
    tesla = df[df[Column.ID] == 322475].iloc[0]
    subaru = df[df[Column.ID] == 283761].iloc[0]

    fixed_consumption = _get_fixed_column_name(Column.CONSUPTION_COMBINED_WLTP)
    scaled_consumption = _get_fixed_and_scaled_column_name(
        Column.CONSUPTION_COMBINED_WLTP
    )

    weighted_consumption = _get_fixed_scaled_and_weighted_column_name(
        Column.CONSUPTION_COMBINED_WLTP
    )
    assert df[df["id"].isin([250123, 250124])][weighted_consumption].notna().all()

    assert tesla[fixed_consumption] > subaru[fixed_consumption]
    assert tesla[scaled_consumption] > subaru[scaled_consumption]
    assert tesla[weighted_consumption] > subaru[weighted_consumption]


def test_model3_score_better_than_impreza(df_scored_de_discount_minmax_scaler):
    df = df_scored_de_discount_minmax_scaler
    model = df[df["name"].str.contains("Tesla")].iloc[0]
    assert model[Column.TOTAL_SCORE] > 186
    assert model[Column.EURO_PER_SCORE] < 190


@pytest.mark.parametrize(
    "id", [320815, 320817, 320814, 322563, 322564, 320083, 283761, 311428]
)
def test_model3_better(df_scored_de_discount_minmax_scaler, id):
    df = df_scored_de_discount_minmax_scaler
    tesla = df[df[Column.ID] == 322475].iloc[0]
    car = df[df[Column.ID] == id].iloc[0]
    assert tesla[Column.TOTAL_SCORE] > car[Column.TOTAL_SCORE]


def test_ioniq_plugin_better(df_scored_de_discount_minmax_scaler):
    df = df_scored_de_discount_minmax_scaler
    df = _filter_by_models(df, ["hyundai ioniq"])
    car_plugin = df[df["name"].str.contains("Hyundai IONIQ PlugIn-Hybrid Prime")].iloc[
        0
    ]
    car_hybrid = df[df["name"].str.contains("Hyundai IONIQ Hybrid Prime")].iloc[0]

    assert car_plugin[Column.TOTAL_SCORE] > car_hybrid[Column.TOTAL_SCORE]


def test_ioniq_with_german_discount(df_scored_de_discount_minmax_scaler):
    df = df_scored_de_discount_minmax_scaler
    df = _filter_by_models(df, ["hyundai ioniq"])
    assert len(df) > 1
    for _, car in df.iterrows():
        is_electric = car["Motorart"] in ["PlugIn-Hybrid", "Elektro"]
        if is_electric:
            assert car[_get_fixed_column_name(Column.PRICE)] < _convert_to_float(
                car[Column.PRICE]
            )


def test_small_test(df_scored_de_discount_minmax_scaler):
    df = df_scored_de_discount_minmax_scaler
    df_subaru = df[df.id == 283761].iloc[0]
    df_bmw = df[df.id == 315738].iloc[0]

    # less is better
    col_price = _get_fixed_column_name(Column.PRICE)
    assert df_subaru[col_price] < df_bmw[col_price]
    col_price = _get_fixed_scaled_and_weighted_column_name(Column.PRICE)
    assert df_subaru[col_price] > 1
    assert df_subaru[col_price] > df_bmw[col_price]

    # more is better
    assert df_subaru[Column.TOP_SPEED] < df_bmw[Column.TOP_SPEED]
    col_speed = _get_fixed_scaled_and_weighted_column_name(Column.TOP_SPEED)
    assert df_subaru[col_speed] < df_bmw[col_speed]

    col_auto = "Autom. Abstandsregelung"
    # more is better
    assert df_subaru[col_auto] == "Serie"
    assert df_bmw[col_auto] == "450 Euro"
    col_auto = _get_fixed_scaled_and_weighted_column_name(col_auto)
    assert df_subaru[col_auto] > df_bmw[col_auto]
    assert df_subaru[Column.TOTAL_SCORE] > df_bmw[Column.TOTAL_SCORE]
    assert df_subaru[Column.EURO_PER_SCORE] < df_bmw[Column.EURO_PER_SCORE]


def assert_mappings(actual, expected_part):
    for k, v in expected_part.items():
        assert k in actual
        assert actual[k] == v


def test_get_mappings_special():
    assert_mappings(
        _get_mappings("Seitenairbag hinten - Bezeichnung", {nan, "inkl. Kopfschutz"}),
        {
            "inkl. Kopfschutz": 1,
            nan: 2,
            "Keine": 2,
            "a.W.": 2,
            "n.b.": 2,
            "nicht bekannt": 2,
        },
    )


def test_get_mappings_empty():
    assert_mappings(
        _get_mappings("Querverkehrassistent", {nan}),
        {},
    )


def test_get_mappings_prices():
    assert_mappings(
        _get_mappings("", {nan, "Serie", "Paket", "100 Euro", "200 Euro"}),
        {"Serie": 0, "Paket": 100, "100 Euro": 100, "200 Euro": 200, nan: 300},
    )


def test_get_mappings_one_price():
    assert_mappings(
        _get_mappings("", {nan, "Serie", "Paket", "100 Euro"}),
        {"Serie": 0, "Paket": 100, "100 Euro": 100, nan: 200},
    )
