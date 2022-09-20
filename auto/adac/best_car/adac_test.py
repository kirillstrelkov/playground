import os

import pandas as pd
from auto.adac.best_car.find_best_car import (
    Column,
    Constant,
    _filtered_cars,
    _fix_numeric_columns,
    _get_fixed_column_name,
)
from auto.adac.best_car.utils import (
    COLUMN_FEATURE,
    COLUMN_FEATURE_NUNIQUE,
    COLUMN_FEATURE_RANGE,
    COLUMN_FEATURE_TYPE,
    COLUMN_FEATURE_WEIGHT,
    FeatureType,
)
from pytest import fixture

ADAC_PATH = os.path.join(os.path.dirname(__file__), "../adac.csv")
FEATURES_PATH = os.path.join(os.path.dirname(__file__), "feature.csv")


def __get_range(df, x):
    if x in Constant.COLS_WITH_NUMERIC_DATA:
        tdf = _fix_numeric_columns(df)
        vals = tdf[_get_fixed_column_name(x)]
        return f"min: {vals.min():.2f} mean: {vals.mean():.2f} max: {vals.max():.2f}"
    else:
        return None


def __get_feature_df(df):
    new_df = df.agg(["nunique"]).transpose().reset_index()
    new_df.columns = [
        COLUMN_FEATURE,
        COLUMN_FEATURE_NUNIQUE,
    ]
    new_df[COLUMN_FEATURE_RANGE] = new_df[COLUMN_FEATURE_NUNIQUE]
    new_df[COLUMN_FEATURE_RANGE] = new_df[COLUMN_FEATURE].apply(
        lambda x: __get_range(df, x)
    )

    new_df[COLUMN_FEATURE_TYPE] = ",".join(FeatureType.all())
    new_df[COLUMN_FEATURE_WEIGHT] = 1
    new_df.columns = [
        COLUMN_FEATURE,
        COLUMN_FEATURE_NUNIQUE,
        COLUMN_FEATURE_RANGE,
        COLUMN_FEATURE_TYPE,
        COLUMN_FEATURE_WEIGHT,
    ]
    return new_df


def __process_initial_data(df):
    if not os.path.exists(FEATURES_PATH):
        new_df = __get_feature_df(df)
        new_df.to_csv(FEATURES_PATH, index=None)


@fixture
def df_features(df_adac):
    __process_initial_data(df_adac)
    yield pd.read_csv(FEATURES_PATH)


@fixture
def df_adac():
    return pd.read_csv(ADAC_PATH)


@fixture
def df_adac_fixed(df_adac):
    return _filtered_cars(df_adac)


def test_features_are_up_to_date(df_adac, df_features):
    df_feature_new = __get_feature_df(df_adac)
    assert not (
        set(df_feature_new[COLUMN_FEATURE].to_list()).difference(
            set(df_features[COLUMN_FEATURE].to_list())
        )
    )


def test_all_features(df_features, df_adac):
    assert len(df_adac.columns.tolist()) == len(set(df_adac.columns.tolist()))
    set1 = set(df_adac.columns.tolist())
    set2 = set(df_features[COLUMN_FEATURE].tolist())
    diff = set1.difference(set2)
    assert not diff
    diff = set2.difference(set1)
    assert not diff


def test_all_features_reviews(df_features):
    assert COLUMN_FEATURE_TYPE in df_features
    not_filled = df_features[~df_features[COLUMN_FEATURE_TYPE].isin(FeatureType.all())]
    assert not_filled.empty

    assert COLUMN_FEATURE_WEIGHT in df_features
    not_filled = df_features[df_features[COLUMN_FEATURE_WEIGHT].isna()]
    assert not_filled.empty
