import json
import os

import numpy as np
import pandas as pd
from utils.file import read_content

from auto.adac.vscar.prepare_json_file import (
    NON_NUMERIC_COLUMNS,
    NUMERIC_COLUMNS,
    _get_column_data,
    _get_numeric_columns,
)


def test_numeric_columns():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, "../adac.csv"))

    expected_numeric_columns = {"Bodenfreiheit maximal", "Kofferraumvolumen normal"}
    expected_non_numeric_columns = {
        "Baureihenstart",
        "Modellstart",
        "Reifengröße",
        "Leistung / Drehmoment (Elektromotor 1)",
        "Ladezeiten",
    }

    numeric_columns = _get_numeric_columns(df)
    assert not set(numeric_columns).symmetric_difference(NUMERIC_COLUMNS)
    assert not expected_numeric_columns.difference(NUMERIC_COLUMNS)
    assert not expected_non_numeric_columns.difference(NON_NUMERIC_COLUMNS)
    assert not NUMERIC_COLUMNS.intersection(NON_NUMERIC_COLUMNS)


def test__get_column_data():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, "../adac.csv"))

    column_data = _get_column_data(df)

    column = "Bodenfreiheit maximal"
    data = column_data[column]
    assert column in column_data
    assert "range" in data
    assert data["range"]["min"] < data["range"]["max"]
    assert data["type"] == "int"
    assert not {np.nan, "n.b."}.difference(data["additional_values"])

    column = "Autom. Abstandsregelung"
    data = column_data[column]
    assert column in column_data
    assert "range" in data
    assert data["range"]["min"] < data["range"]["max"]
    assert data["type"] == "int"
    assert not {np.nan, "Paket", "Serie"}.difference(data["additional_values"])

    for column in [
        "Grundpreis",
        "Kofferraumvolumen normal",
        "Höchstgeschwindigkeit",
        "CO2-Wert (NEFZ)",
        "Verbrauch Gesamt (NEFZ)",
        "Klassenübliche Ausstattung nach ADAC-Vorgabe",
        "Fahrzeugpreis",
        "Beschleunigung 0-100km/h",
        "Verbrauch kombiniert (WLTP)",
        "CO2-Wert kombiniert (WLTP)",
        "Vollkaskobetrag 100% 500 € SB",
        "Fahrgeräusch",
    ]:
        data = column_data[column]
        assert data["type"] in ["int", "float"]
