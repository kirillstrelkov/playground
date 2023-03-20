import pandas as pd
import pytest
from numpy import nan

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
    _is_weighted,
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

__SUBARU_MY_IMPREZA_NAME = "Subaru Impreza"
__TESLA_M3_NAME = "Tesla Model 3"
__TESLA_MY_NAME = "Tesla Model Y Maximum Range"


@pytest.fixture
def df_cars():
    return get_cars()


@pytest.fixture
def df_filtered_cars(df_cars):
    return _filtered_cars(df=df_cars)


@pytest.fixture
def df_scored(df_filtered_cars):
    return get_scored_df(df_filtered_cars)


@pytest.fixture
def df_scored_parent(df_filtered_cars):
    return get_scored_df(df_filtered_cars, feature_file_name="feature_parents.csv")


@pytest.fixture
def df_features():
    return pd.read_csv(FEATURES_PATH)


def _get_diff(df, df_a, df_b, limit=10):
    df_tmp = df[df[Column.ID].isin([df_a[Column.ID], df_b[Column.ID]])]
    weighted = [col for col in df_tmp.columns if _is_weighted(col)]
    diff = (df_a[weighted] - df_b[weighted]).fillna(0).sort_values()
    return pd.concat([diff.head(limit), diff.tail(limit)])


def _get_car_by_name(df, name):
    df_filtered = df[df[Column.NAME].str.contains(name, regex=False)].sort_values(
        [Column.TOTAL_SCORE, _get_fixed_column_name(Column.PRICE)],
        ascending=[False, True],
    )
    assert not df_filtered.empty, f"Failed to find '{name}'"
    return df_filtered.iloc[0]


@pytest.mark.parametrize(
    "car_name, suv_name",
    [
        ("i30", "Tucson"),
        ("Impreza", "Forester"),
        ("Astra", "Grandland"),
        ("Impreza", "XV"),
        (" Ceed", "Sportage"),
    ],
)
def test_scored_parents_suv_is_better(df_scored_parent, car_name, suv_name):
    car = _get_car_by_name(df_scored_parent, car_name)
    suv = _get_car_by_name(df_scored_parent, suv_name)
    assert car[Column.TOTAL_SCORE] < suv[Column.TOTAL_SCORE]


def test_all_nans_are_properly_fix_scaled_weighted(
    df_scored,
):
    weighted_columns = [col for col in df_scored.columns if "weighted" in col]
    for wcol in weighted_columns:
        df_weighted_na = df_scored[df_scored[wcol].isin(ZERO_POINTS_MAPPING)]
        names = wcol.split(NAME_SPLITTER)
        for i in range(1, len(names) - 1):
            prev_name = NAME_SPLITTER.join(names[: len(names) - i])
            if prev_name in df_weighted_na.columns:
                df_empty = df_weighted_na[
                    ~df_weighted_na[prev_name].isin(ZERO_POINTS_MAPPING)
                ]
                assert df_empty.empty


def test_scaled_columns_minmax(df_scored):
    df = df_scored
    columns = [c for c in df.columns if c.endswith("scaled")]
    for col in columns:
        assert df[col].min() >= -0.01
        assert df[col].max() <= 1.01


def test_fixed_columens(df_scored):
    assert _get_fixed_column_name(Column.COSTS) in df_scored.columns


def test_max_weights(df_scored, df_features):
    df = df_scored
    for _, row in df_features.iterrows():
        feature = row[COLUMN_FEATURE]
        type = row[COLUMN_FEATURE_TYPE]
        weight = row[COLUMN_FEATURE_WEIGHT]
        if type != FeatureType.SKIP:
            max_feature = df[get_weighted_column_name(df, feature)].max()
            assert max_feature < weight + 0.01


def test_consumption(
    df_scored,
):
    col_fixed = _get_fixed_column_name(Column.CONSUPTION_COMBINED_WLTP)
    col_scaled = _get_fixed_and_scaled_column_name(Column.CONSUPTION_COMBINED_WLTP)
    col_weighted = _get_fixed_scaled_and_weighted_column_name(
        Column.CONSUPTION_COMBINED_WLTP
    )
    df_e = df_scored[df_scored[Column.ENGINE_TYPE] == "Elektro"]
    df_non_e = df_scored[df_scored[Column.ENGINE_TYPE] != "Elektro"]
    cols = [
        "name",
        Column.CONSUPTION_COMBINED_WLTP,
        col_fixed,
        col_scaled,
        col_weighted,
    ]
    df_e_min = df_e[df_e[col_fixed] == df_e[col_fixed].min()][cols].iloc[0]
    df_e_max = df_e[df_e[col_fixed] == df_e[col_fixed].max()][cols].iloc[0]
    assert df_e_min[col_scaled] == 1.0
    assert df_e_max[col_scaled] < 0.01

    df_non_e_min = df_non_e[df_non_e[col_fixed] == df_non_e[col_fixed].min()][
        cols
    ].iloc[0]
    df_non_e_max = df_non_e[df_non_e[col_fixed] == df_non_e[col_fixed].max()][
        cols
    ].iloc[0]
    assert df_non_e_min[col_scaled] == 1.0
    assert df_non_e_max[col_scaled] < 0.01

    e_fixed_min = df_e[col_fixed].min()
    e_fixed_max = df_e[col_fixed].max()
    assert 3 < e_fixed_min < 6
    assert 30 < e_fixed_max < 35

    e_scaled_min = df_e[col_scaled].min()
    e_scaled_mean = df_e[col_scaled].mean()
    e_scaled_max = df_e[col_scaled].max()

    non_e_fixed_min = df_non_e[col_fixed].min()
    non_e_fixed_max = df_non_e[col_fixed].max()
    assert 1 < non_e_fixed_min < 3
    assert 10 < non_e_fixed_max < 15

    non_e_scaled_min = df_non_e[col_scaled].min()
    non_e_scaled_mean = df_non_e[col_scaled].mean()
    non_e_scaled_max = df_non_e[col_scaled].max()

    # electric
    e_car_min = df_e[df_e[col_scaled] == e_scaled_min].iloc[0]
    e_car_max = df_e[df_e[col_scaled] == e_scaled_max].iloc[0]
    assert e_car_min[col_fixed] > e_car_max[col_fixed]
    assert e_car_min[col_scaled] < e_car_max[col_scaled]

    # non electric
    non_e_car_min = df_non_e[df_non_e[col_scaled] == non_e_scaled_min].iloc[0]
    non_e_car_max = df_non_e[df_non_e[col_scaled] == non_e_scaled_max].iloc[0]
    assert non_e_car_min[col_fixed] > non_e_car_max[col_fixed]
    assert non_e_car_min[col_scaled] < non_e_car_max[col_scaled]

    tesla = _get_car_by_name(df_scored, __TESLA_M3_NAME)
    subaru = _get_car_by_name(df_scored, __SUBARU_MY_IMPREZA_NAME)
    df_tesla = tesla[cols]
    df_subaru = subaru[cols]

    assert tesla[col_fixed] < df_e[col_fixed].mean()
    assert tesla[col_scaled] > e_scaled_mean

    assert subaru[col_fixed] > df_non_e[col_fixed].mean()
    assert subaru[col_scaled] < 0.5
    assert subaru[col_scaled] < non_e_scaled_mean

    assert df_tesla[col_weighted] > df_subaru[col_weighted]


def test_tesla_scaled_consumption_better_than_subaru(
    df_scored,
):
    df = df_scored
    tesla = _get_car_by_name(df, __TESLA_M3_NAME)
    subaru = _get_car_by_name(df, __SUBARU_MY_IMPREZA_NAME)

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


def test_model3_score_better_than_impreza(df_scored):
    tesla = _get_car_by_name(df_scored, __TESLA_M3_NAME)
    subaru = _get_car_by_name(df_scored, __SUBARU_MY_IMPREZA_NAME)

    assert tesla[Column.TOTAL_SCORE] > subaru[Column.TOTAL_SCORE]
    assert tesla[Column.EURO_PER_SCORE] > subaru[Column.EURO_PER_SCORE]

    cols = [col for col in df_scored.columns if "Einparkhilfe - Bezeichnung" in col]
    tesla_park_assist = tesla[cols]
    subaru_park_assist = subaru[cols]
    assert tesla_park_assist.notna().all()
    assert subaru_park_assist.notna().all()

    wieghted_column = _get_fixed_scaled_and_weighted_column_name(
        "Einparkhilfe - Bezeichnung"
    )
    assert tesla[wieghted_column] < subaru[wieghted_column]


@pytest.mark.parametrize(
    "name1,name2",
    [
        (__TESLA_M3_NAME, "VW ID.3"),
        (__TESLA_M3_NAME, "VW ID.4"),
        (__TESLA_M3_NAME, "VW ID.5"),
        (__TESLA_M3_NAME, "KIA EV6"),
        (__TESLA_M3_NAME, "Polestar"),
        (__TESLA_M3_NAME, "IONIQ 5"),
        (__TESLA_M3_NAME, "KIA XCeed"),
        (__TESLA_M3_NAME, "Tesla Model Y"),
        (__TESLA_M3_NAME, __SUBARU_MY_IMPREZA_NAME),
        (__TESLA_M3_NAME, "Mazda MX-30"),
        (__TESLA_MY_NAME, "Audi A6"),
        (__TESLA_MY_NAME, "Mercedes-Benz E"),
        (__TESLA_MY_NAME, "Mercedes-Benz C"),
        (__TESLA_MY_NAME, "BMW 5"),
        (__TESLA_MY_NAME, "Hyundai IONIQ 5 (77,4 kWh) UNIQ-Paket 4WD"),
    ],
)
def test_compare_two_cars(df_scored, name1, name2):
    df = df_scored
    car1 = _get_car_by_name(df, name1)
    car2 = _get_car_by_name(df, name2)
    t = _get_diff(df, car1, car2, 20)
    assert car1[Column.TOTAL_SCORE] > car2[Column.TOTAL_SCORE]


def test_small_test(df_scored):
    df = df_scored
    df_subaru = _get_car_by_name(df, __SUBARU_MY_IMPREZA_NAME)
    df_bmw = _get_car_by_name(df, "BMW 118i M")

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
        {"Serie": 0, "Paket": 150, "100 Euro": 100, "200 Euro": 200, nan: 250},
    )


def test_get_mappings_one_price():
    assert_mappings(
        _get_mappings("", {nan, "Serie", "Paket", "100 Euro", "1000 Euro"}),
        {"Serie": 0, "Paket": 550, "100 Euro": 100, "1000 Euro": 1000, nan: 1450},
    )
