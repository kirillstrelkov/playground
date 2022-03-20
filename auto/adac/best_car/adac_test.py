import os

import pandas as pd
from auto.adac.best_car.find_best_car import Column, _filtered_cars
from auto.adac.best_car.utils import (
    COLUMN_FEATURE,
    COLUMN_FEATURE_RANGE,
    COLUMN_FEATURE_TYPE,
    COLUMN_FEATURE_WEIGHT,
    FeatureType,
)
from pytest import fixture

ADAC_PATH = os.path.join(os.path.dirname(__file__), "../adac.csv")
FEATURES_PATH = os.path.join(os.path.dirname(__file__), "feature.csv")


def __process_initial_data(df):
    if not os.path.exists(FEATURES_PATH):
        new_df = df.agg(["nunique"]).transpose().reset_index()
        new_df.columns = [COLUMN_FEATURE, COLUMN_FEATURE_RANGE]
        new_df[COLUMN_FEATURE_TYPE] = None
        new_df[COLUMN_FEATURE_WEIGHT] = None
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


def test_all_features(df_features, df_adac):
    assert len(df_adac.columns.tolist()) == len(set(df_adac.columns.tolist()))
    assert sorted(df_adac.columns.tolist()) == sorted(
        df_features[COLUMN_FEATURE].tolist()
    )


def test_all_features_reviews(df_features):
    assert COLUMN_FEATURE_TYPE in df_features
    not_filled = df_features[~df_features[COLUMN_FEATURE_TYPE].isin(FeatureType.all())]
    assert not_filled.empty

    assert COLUMN_FEATURE_WEIGHT in df_features
    not_filled = df_features[df_features[COLUMN_FEATURE_WEIGHT].isna()]
    assert not_filled.empty
