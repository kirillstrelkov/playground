import os
import re
from heapq import nlargest

import pandas as pd
from auto.adac.best_car.utils import (
    COLUMN_FEATURE,
    COLUMN_FEATURE_TYPE,
    COLUMN_FEATURE_WEIGHT,
    FeatureType,
)
from loguru import logger
from numpy import dtype, float64, nan
from pandas.core.frame import DataFrame
from sklearn.preprocessing import MinMaxScaler

ZERO_POINTS_MAPPING = {
    nan,
    "nicht bekannt",
    "n.b.",
    "Keine",
    "a.W.",
    "Aufpreis (noch nicht bekannt)",
}
NAME_SPLITTER = "|"


class Column(object):
    ID = "id"
    SEATS = "Sitzanzahl"
    TRANSMISSION = "Getriebeart"
    COSTS_OPERATING = "Betriebskosten"
    COSTS_FIX = "Fixkosten"
    COSTS_WORKSHOP = "Werkstattkosten"
    COSTS_DEPRECIATION = "Wertverlust"
    MARK = "Marke"
    SERIE = "Baureihe"
    PERFORMANCE_KW = "Leistung maximal in kW (Systemleistung)"
    ENGINE_TYPE = "Motorart"
    PRICE = "Grundpreis"
    ADAC_PAKET = "Klassenübliche Ausstattung nach ADAC-Vorgabe"
    ACCELERATION = "Beschleunigung 0-100km/h"
    FUEL_TANK_SIZE = "Tankgröße"
    BATTERY_CAPACITY = "Batteriekapazität (Netto) in kWh"
    CONSUPTION_TOTAL_NEFZ = "Verbrauch Gesamt (NEFZ)"
    CONSUPTION_COMBINED_WLTP = "Verbrauch kombiniert (WLTP)"
    BODY_TYPE = "Karosserie"
    TOP_SPEED = "Höchstgeschwindigkeit"
    # New columns:
    NAME = "name"
    CTO = "Costs to own"
    TOTAL_PRICE = "Total price"
    RANGE = "Range"
    TOTAL_SCORE = "Total Score"
    EURO_PER_SCORE = "Euro per score"


class ColumnSpec(object):
    ADAC_COLUMN = "adac column"
    ADAC_VALUES = "adac values, ascending order"
    FEATURE = "feature"
    REVERSED = "reversed"
    WEIGHT = "weight"
    PREFIX = "prefix"


class Constant(object):
    TRANSMISSION_MANUAL = "Schaltgetriebe"

    COLS_WITH_NUMERIC_DATA = set(
        """
CO2-Wert kombiniert (WLTP)
Höchstgeschwindigkeit
Beschleunigung 0-100km/h
Fahrgeräusch
Länge
Kofferraumvolumen normal
Kofferraumvolumen dachhoch mit umgeklappter Rücksitzbank
Bodenfreiheit maximal
Wertverlust
Betriebskosten
Fixkosten
Werkstattkosten
KFZ-Steuer pro Jahr ohne Steuerbefreiung
Haftpflichtbeitrag 100%
Vollkaskobetrag 100% 500 € SB
""".strip().splitlines()
        + [
            Column.COSTS_FIX,
            Column.COSTS_OPERATING,
            Column.COSTS_WORKSHOP,
            Column.ADAC_PAKET,
            Column.PRICE,
            Column.ACCELERATION,
            Column.FUEL_TANK_SIZE,
            Column.BATTERY_CAPACITY,
            Column.CONSUPTION_TOTAL_NEFZ,
            Column.CONSUPTION_COMBINED_WLTP,
        ]
    )


def _convert_to_float(x, strict=False):
    if type(x) == str:
        match = re.search(r"\d+[.,]?\d*", x)

        if match:
            return float(match.group().replace(".", "").replace(",", "."))
        elif strict:
            return x
        else:
            return nan
    else:
        return x


def _get_mappings(column, values):
    # TODO: improve
    # special columns lesser index - better
    special_columns = {
        "Kopfairbag vorne - Bezeichnung": ["Windowbag", "Kopfairbag separat"],
        "Reifendruckkontrolle - Bezeichnung": [
            "direkte Messung (Sensor)",
            "indirekte Messung (ABS)",
        ],
        "Einparkhilfe - Bezeichnung": [
            "vo.+hi. mit Front- und Heckkamera",
            "Front- und Heckkamera",
            "vo.+hi. mit Rückfahrkamera",
            "hinten mit Rückfahrkamera",
            "vorne und hinten",
            "Rückfahrkamera",
            "hinten",
        ],
        "Kopfairbag vorne - Bezeichnung": ["Windowbag", "Kopfairbag separat"],
        "Seitenairbag vorne - Bezeichnung": [
            "inkl. Kopfschutz",
            "inkl. Hüftschutz",
            "Nur Fahrerseite",
        ],
        "Airbag Sonstige - Bezeichnung": [
            "Knieairbag Fahrer und Fußgängerairbag",
            "Knieairbag Fahrer und Beifahrer",
            "Knieairbag Fahrer (Serie), Gurtairbag hinten",
            "Mittenairbag vorne",
            "Knieairbag Fahrer",
            "Anti-Submarining-Airbag",
        ],
        "PreCrash-System - Bezeichnung": [
            "Reversible Gurtstraffer/Schließfunktion/Sitzposition",
            "Reversible Gurtstraffer/Schließfunktion",
            "Reversible Gurtstraffer",
        ],
        "Fußgängerschutz-System": ["Fußgängerairbag", "Aktive Motorhaube"],
        "Seitenairbag hinten - Bezeichnung": ["inkl. Kopfschutz"],
        "Isofix - Bezeichnung": [
            "Vorn und hinten mit Top-Tether",
            "Nur hinten mit Top-Tether",
            "Vorn und hinten",
            "Nur hinten",
            "Nur vorn",
        ],
        "CO2-Effizienzklasse": [
            "A+",
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
        ],
        "Federung hinten": ["Luft", "Drehstab", "Schraube", "Blattfeder"],
        "Bremse hinten": ["Scheibe", "Trommel"],
        "Federung vorne": ["Luft", "Blattfeder", "Schraube"],
        "Antriebsart": ["Allrad", "Heck", "Front"],
        "Getriebeart": [
            "Automatikgetriebe",
            "Automat. Schaltgetriebe (Doppelkupplung)",
            "CVT-Getriebe",
            "Automatisiertes Schaltgetriebe",
            "Schaltgetriebe",
        ],
    }

    mappings = {}
    if column in special_columns:
        vals = special_columns[column]
        mappings = dict(zip(vals, range(1, len(vals) + 1)))
        max_val = len(mappings) + 1
    else:
        for val in values:
            new_val = _convert_to_float(val, True)
            if type(new_val) == float and not pd.isna(new_val):
                mappings[val] = new_val

        if mappings:
            mappings["Paket"] = min(mappings.values())
            if len(mappings) > 2:
                max_val, max_second = nlargest(2, mappings.values())
                max_val = max(mappings.values()) + max_val - max_second
            else:
                max_val = max(mappings.values()) * 2
        else:
            mappings["Paket"] = 1
            max_val = 2

        mappings["Serie"] = 0

    if mappings:
        for v in ZERO_POINTS_MAPPING:
            mappings[v] = max_val

    return mappings


def _fix_category_columns(df, columns):
    for col in columns:
        unique_values = df[col].unique()
        mappings = _get_mappings(col, unique_values)

        diff_vals = set(unique_values).difference(set(mappings.keys()))
        if diff_vals:
            logger.warning(
                f"Failed to create mapping for '{col}': diff: {list(diff_vals)}"
            )
        else:
            df[_get_fixed_column_name(col)] = df[col].apply(lambda x: mappings[x])

    return df


def _fix_numeric_columns(df, columns=None):
    if not columns:
        columns = Constant.COLS_WITH_NUMERIC_DATA

    if (
        Column.CONSUPTION_COMBINED_WLTP in columns
        and _get_fixed_column_name(Column.CONSUPTION_COMBINED_WLTP) not in df.columns
    ):
        df[_get_fixed_column_name(Column.CONSUPTION_COMBINED_WLTP)] = df.apply(
            lambda r: _convert_to_float(r.get(Column.CONSUPTION_COMBINED_WLTP, nan))
            * (4 if r[Column.ENGINE_TYPE] == "PlugIn-Hybrid" else 1),
            axis=1,
        )

    columns = [col for col in columns if _get_fixed_column_name(col) not in df.columns]

    df_numeric = df[columns].applymap(_convert_to_float)
    df_numeric.columns = [_get_fixed_column_name(col) for col in df_numeric.columns]

    return df.join(df_numeric)


def _fix_missing_values_by_adding_avg(df):
    def fix_name(df, df_bad, groupby_col, value):
        if (
            not df.loc[
                (df[groupby_col] == value) & (df.id.isin(df_bad.id)),
                Column.NAME,
            ]
            .iloc[0]
            .endswith("*")
        ):
            df.loc[
                (df[groupby_col] == value) & (df.id.isin(df_bad.id)),
                Column.NAME,
            ] += "*"

    # fix average by SERIE
    groupby_col = Column.SERIE
    for col in Constant.COLS_WITH_NUMERIC_DATA:
        if col in {Column.BATTERY_CAPACITY, Column.FUEL_TANK_SIZE}:
            continue

        df_bad = df[pd.isna(df[col])]
        if df_bad.empty:
            continue

        for value in df_bad[groupby_col].unique():
            df.loc[(df[groupby_col] == value) & (df.id.isin(df_bad.id)), col] = (
                df[df[groupby_col] == value]
                .groupby(groupby_col)
                .mean()
                .get(col, [pd.NA])[0]
            )
            fix_name(df, df_bad, groupby_col, value)

    # fix average by MARK and BODY_TYPE
    groupby_col = Column.MARK
    for col in Constant.COLS_WITH_NUMERIC_DATA:
        if col in {Column.BATTERY_CAPACITY, Column.FUEL_TANK_SIZE}:
            continue

        df_bad = df[pd.isna(df[col])]
        for value in df_bad[groupby_col].unique():
            body_types = (
                df.loc[(df[groupby_col] == value) & (df.id.isin(df_bad.id))][
                    Column.BODY_TYPE
                ]
                .unique()
                .tolist()
            )
            # NOTE: sometimes might be multiple body types
            body_type = body_types[0]
            df.loc[(df[groupby_col] == value) & (df.id.isin(df_bad.id)), col] = (
                df[(df[groupby_col] == value) & (df[Column.BODY_TYPE] == body_type)]
                .groupby(groupby_col)
                .mean()
                .get(col, [pd.NA])[0]
            )
            fix_name(df, df_bad, groupby_col, value)

    return df


def _filter_by_models(df, names):
    return df[
        df[Column.NAME].apply(
            lambda x: any([_is_model_name(x, name) for name in names])
        )
    ]


def get_cars():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../adac.csv"))
    return pd.read_csv(path)


def _filtered_cars(df=None, fix_missing=False):
    if df is None:
        df = get_cars()

    df = _fix_numeric_columns(df)

    if fix_missing:
        df = _fix_missing_values_by_adding_avg(df)

    return df


def _apply_de_discount(df, column):
    df = _fix_numeric_columns(df, [column])

    def get_discount(price, motor_type):
        netto_price = price * 0.81
        if motor_type == "Elektro":
            if netto_price <= 40000:
                return 9000
            elif netto_price <= 65000:
                return 7500
        elif motor_type == "PlugIn-Hybrid":
            if netto_price <= 40000:
                return 6750
            elif netto_price <= 65000:
                return 5625
        return 0

    def apply_discount(row):
        motor_type = row[Column.ENGINE_TYPE]
        price = row[_get_fixed_column_name(Column.PRICE)]
        row[_get_fixed_column_name(column)] = max(
            0, price - get_discount(price, motor_type)
        )
        return row

    df = df.apply(apply_discount, axis=1)
    return df


def _is_model_name(full_name, part_name):
    words = re.findall(r"\w+", full_name.lower())
    search_words = re.findall(r"\w+", part_name.lower())
    if "bmw" == words[0] == search_words[0]:
        assert len(search_words) == 2, f"search '{part_name}' not supported for bmw"
        return words[1].startswith(search_words[1])
    else:
        return all([part in words for part in search_words])


def get_scored_df(df=None, de_discount=False, feature_file_name="feature.csv"):
    if df is None:
        df = _filtered_cars()

    df_duplicates = df[df.duplicated([Column.ID])][
        [Column.ID, Column.NAME]
    ].reset_index(drop=True)
    logger.warning(f"Duplicates:\n{df_duplicates.to_string()}")
    df = df.drop_duplicates([Column.ID]).reset_index(drop=True)

    df_features = pd.read_csv(
        os.path.join(os.path.dirname(__file__), feature_file_name)
    )
    df_features_group = (
        df_features[df_features[COLUMN_FEATURE_TYPE] != FeatureType.SKIP]
        .groupby("type")[COLUMN_FEATURE]
        .apply(list)
    )

    if de_discount:
        df = _apply_de_discount(df, Column.PRICE)

    a1 = _apply_scaler(df, df_features_group[FeatureType.MORE_IS_BETTER])
    b1 = _apply_scaler(df, df_features_group[FeatureType.LESS_IS_BETTER], reversed=True)
    c1 = _apply_categorized_scaler(df, df_features_group[FeatureType.CATEGORY])

    a2 = _apply_weights(
        a1, df_features[df_features[COLUMN_FEATURE_TYPE] == FeatureType.MORE_IS_BETTER]
    )
    b2 = _apply_weights(
        b1, df_features[df_features[COLUMN_FEATURE_TYPE] == FeatureType.LESS_IS_BETTER]
    )
    c2 = _apply_weights(
        c1, df_features[df_features[COLUMN_FEATURE_TYPE] == FeatureType.CATEGORY]
    )

    tmp_df = df.reset_index(drop=True).join([a1, b1, c1])
    new_df = tmp_df.reset_index(drop=True).join([a2, b2, c2])
    df_cols = set(new_df.columns.tolist())
    cols = [c for c in df_cols if _is_weighted(c)]
    new_df[Column.TOTAL_SCORE] = new_df[cols].sum(axis=1)
    new_df[Column.EURO_PER_SCORE] = (
        new_df[_get_fixed_column_name(Column.PRICE)] / new_df[Column.TOTAL_SCORE]
    )
    return new_df.sort_values([Column.TOTAL_SCORE], ascending=False).reset_index(
        drop=True
    )


def _apply_scaler(df, columns, reversed=False):
    df = _fix_numeric_columns(df, columns)

    def __apply_scaler_for_columns(_df, _columns, _scaled_columns):
        scaler_obj = MinMaxScaler()

        if len(_columns) == 1:
            data = _df[_columns].values
        else:
            data = _df[_columns]
        _tmp_df = DataFrame(
            columns=_scaled_columns, data=scaler_obj.fit_transform(data)
        )

        if reversed:
            _tmp_df = 1 - _tmp_df
        return _tmp_df

    columns_to_scale = [
        col if col not in df.columns else _get_fixed_column_name(col) for col in columns
    ]
    scaled_columns = [_get_scaled_column_name(c) for c in columns_to_scale]

    for col in columns_to_scale:
        assert df[col].dtype != dtype("O"), f"Wrong type for {col}:"

    tmp_df = __apply_scaler_for_columns(df, columns_to_scale, scaled_columns)

    # TODO: split between electric and non electric
    if Column.CONSUPTION_COMBINED_WLTP in columns:
        karosie = [
            "SUV",
            "Kombi",
            "Schrägheck",
            "Stufenheck",
            "Van",
            "Coupe",
            "Cabrio",
            "Hochdach-Kombi",
            "Geländewagen",
            "Roadster",
            "Wohnmobil",
            "Pick-Up",
            "Kleintransporter",
        ]
        is_car = df[Column.BODY_TYPE].isin(karosie)
        is_electric = df[Column.ENGINE_TYPE] == "Elektro"

        dfs_applied = []
        fixed_col_name = _get_fixed_column_name(Column.CONSUPTION_COMBINED_WLTP)
        scaled_col_name = _get_fixed_and_scaled_column_name(
            Column.CONSUPTION_COMBINED_WLTP
        )

        for filter in (
            is_car & is_electric,
            is_car & ~is_electric,
            ~is_car & is_electric,
            ~is_car & ~is_electric,
        ):
            df_filter = df[filter]

            df_filter[scaled_col_name] = __apply_scaler_for_columns(
                df_filter, [fixed_col_name], [scaled_col_name]
            )[scaled_col_name].tolist()
            if not df_filter.empty:
                dfs_applied.append(df_filter)

        tmp_df[scaled_col_name] = pd.concat(dfs_applied).sort_index()[scaled_col_name]

    return tmp_df


def _get_fixed_column_name(column):
    if "fixed" in column:
        return column
    else:
        return column + NAME_SPLITTER + "fixed"


def _get_scaled_column_name(column):
    if "scaled" in column:
        return column
    else:
        return column + NAME_SPLITTER + "scaled"


def _get_weighted_column_name(column):
    if _is_weighted(column):
        return column
    else:
        return column + NAME_SPLITTER + "weighted"


def _is_weighted(column):
    return "weighted" in column


def _get_scaled_and_weighted_column_name(column):
    return _get_weighted_column_name(_get_scaled_column_name(column))


def _get_fixed_and_scaled_column_name(column):
    return _get_scaled_column_name(_get_fixed_column_name(column))


def _get_fixed_scaled_and_weighted_column_name(column):
    return _get_weighted_column_name(
        _get_scaled_column_name(_get_fixed_column_name(column))
    )


def _apply_categorized_scaler(df, columns):
    df = _fix_category_columns(df, columns)

    df_columns = set(df.columns.tolist())
    fixed_columns = [
        _get_fixed_column_name(c)
        for c in columns
        if _get_fixed_column_name(c) in df_columns
    ]

    return _apply_scaler(df, fixed_columns, reversed=True)


def _apply_weights(df, df_weights):
    tmp_df = df.copy()
    tmp_df.columns = [_get_weighted_column_name(col) for col in tmp_df.columns]

    df_non_default = df_weights[df_weights[COLUMN_FEATURE_WEIGHT] != 1]
    if not df_non_default.empty:
        for _, row in df_non_default.iterrows():
            feature = row[COLUMN_FEATURE]
            weight = row[COLUMN_FEATURE_WEIGHT]
            col_name1 = _get_fixed_scaled_and_weighted_column_name(feature)
            col_name2 = _get_scaled_and_weighted_column_name(feature)
            if col_name1 in tmp_df.columns:
                col_name = col_name1
            elif col_name2 in tmp_df.columns:
                col_name = col_name2
            else:
                assert False, f"Wrong feature: {feature}"
            tmp_df[col_name] = tmp_df[col_name] * weight

    return tmp_df


def get_weighted_column_name(df, column_name):
    possible_names = [
        _get_fixed_scaled_and_weighted_column_name(column_name),
        _get_scaled_and_weighted_column_name(column_name),
        _get_weighted_column_name(column_name),
    ]
    columns = set(df.columns.tolist())
    for name in possible_names:
        if name in columns:
            return name
    return None


def __df_to_string(df, weighted_column, limit=5, base_cols=["name", "id"]):
    names = weighted_column.split(NAME_SPLITTER)
    cols = [NAME_SPLITTER.join(names[: i + 1]) for i in range(len(names))]
    cols = [col for col in cols if col in df.columns]
    return df[base_cols + cols].head(limit).to_string()
