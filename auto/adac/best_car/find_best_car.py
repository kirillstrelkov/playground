import os
import re

import pandas as pd
from numpy import nan
from pandas.core.frame import DataFrame

NOT_NA_COLUMNS = [
    "Autom. Abstandsregelung",
    # "Fernlichtassistent", NOTE: Tesla doesn't have it
    "Regensensor",
    "Lichtsensor",
    # "Fußgängererkennung",
]


class Column(object):
    SEATS = "Sitzanzahl"
    TRANSMISSION = "Getriebeart"
    COSTS_OPERATING = "Betriebskosten"
    COSTS_FIX = "Fixkosten"
    COSTS_WORKSHOP = "Werkstattkosten"
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
    # New columns:
    NAME = "name"
    MY_M_COSTS = "my monthly costs"
    TOTAL_PRICE = "Total price"
    RANGE = "Range"
    TOTAL_SCORE = "Total Score"
    EURO_PER_SCORE = "Euro per score"
    WARRANTY_Y = "Garantie y"


class ColumnSpec(object):
    ADAC_COLUMN = "adac column"
    ADAC_VALUES = "adac values, ascending order"
    FEATURE = "feature"
    REVERSED = "reversed"
    WEIGHT = "weight"
    PREFIX = "prefix"


class Constant(object):
    TRANSMISSION_MANUAL = "Schaltgetriebe"

    COLS_WITH_NUMERIC_DATA = """
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
""".strip().splitlines() + [
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


def _get_columns_with_euro(df=None):
    if not df:
        df = _filtered_cars()

    cols = []
    for col in df.columns:
        if df[col].apply(lambda x: "euro" in str(x).lower()).any():
            cols.append(col)

    return cols


def _filter_column(df, column):
    return df[df[column].isin(_get_not_na_set(df[column]))]


def _get_not_na_set(serie):
    return [s for s in set(serie.tolist()) if not pd.isna(s)]


def __convert_to_float(x):
    if type(x) == str:
        match = re.search(r"\d+[.,]?\d*", x)

        if match:
            return float(match.group().replace(",", "."))
        else:
            return nan
    else:
        return x


def _fix_numeric_columns(df):

    # Klassenübliche Ausstattung nach ADAC-Vorgabe
    # Kopfairbag vorne
    # Airbag Deaktivierung
    # Metallic-Lackierung
    # Grundpreis
    # Rücksitzbank umklappbar
    # Schadstoffklasse
    # Lederausstattung
    # Einparkhilfe
    # Klimaanlage
    # Regensensor
    # Nebelscheinwerfer
    # Alufelgen
    # Xenon-Scheinwerfer
    # Berganfahrassistent
    # Seitenairbag vorne
    # Zusätzliche Garantien
    # KFZ-Steuer/Jahr (Kann aufgrund WLTP-Umstellung abweichen)
    # Speed-Limiter
    # Radio
    # Bremsassistent
    # Vollkaskobetrag 100% 500 Euro SB
    # KFZ-Steuer pro Jahr
    # Steuerbefreiung
    # Haftpflichtbeitrag 100%
    # Teilkaskobeitrag 150 Euro SB
    # Fahrzeugpreis für die Berechnung
    # Navigation
    # LED-Scheinwerfer
    # Fernlichtassistent
    # Verkehrsschild-Erkennung
    # Fensterheber elektr. hinten
    # Spurhalteassistent
    # City-Notbremsassistent
    # Müdigkeitserkennung
    # Notruffunktion
    # Kurvenlicht
    # Abbiegelicht
    # Runflat
    # Spurwechselassistent
    # Autom. Abstandsregelung
    # Aktive Kopfstützen
    # Einparkassistent
    # PreCrash-System
    # Head-up-Display (HUD)
    # Seitenairbag hinten
    # Querverkehrassistent
    # Aktivlenkung
    # Laserscheinwerfer
    # Ladezustandskontrolle
    # Trailer-Assist

    #  fix to numeric
    for col in Constant.COLS_WITH_NUMERIC_DATA:
        df[col] = df[col].apply(__convert_to_float)
    return df


def __fix_bad_data(df):
    df[Column.ACCELERATION] = df[Column.ACCELERATION].apply(
        lambda x: x / 10.0 if x > 100 else x
    )
    return df


def _fix_missing_values_by_adding_avg(df):
    # by Default - add 40% percentile data
    # add * to names if cars was modified
    def get_avg(col, groupby, value):
        return df[df[groupby] == value].groupby(groupby).mean().get(col, [pd.NA])[0]

        # fix by average mark, modell if that doesn't work fix by average mark

    for groupby_col in [Column.SERIE, Column.MARK]:
        for col in Constant.COLS_WITH_NUMERIC_DATA:
            if col in {Column.BATTERY_CAPACITY, Column.FUEL_TANK_SIZE}:
                continue

            df_bad = df[pd.isna(df[col])]
            for value in df_bad[groupby_col].unique():
                df.loc[
                    (df[groupby_col] == value) & (df.id.isin(df_bad.id)), col
                ] = get_avg(col, groupby_col, value)

    return df


def _filter_by_models(df, names):
    return df[
        df[Column.NAME].apply(
            lambda x: any([_is_model_name(x, name) for name in names])
        )
    ]


def _get_df_with_cost_to_own(name=None, de_discount=True, filtered_cars=None):
    if filtered_cars is None:
        df = _filtered_cars()
    else:
        df = filtered_cars

    if name:
        df = _filter_by_models(df, [name])

    df[Column.TOTAL_PRICE] = df[Column.ADAC_PAKET] + df[Column.PRICE]

    if not df.empty and de_discount:
        df = _apply_de_discount(df, Column.TOTAL_PRICE)

    # Range
    def __calc_range(row):
        tank = (
            row[Column.BATTERY_CAPACITY]
            if row[Column.ENGINE_TYPE] == "Elektro"
            else row[Column.FUEL_TANK_SIZE]
        )
        row[Column.RANGE] = tank / row[Column.CONSUPTION_COMBINED_WLTP] * 100

        # plugin Hybrid consumption is too small on long range
        if row["Motorart"] == "PlugIn-Hybrid":
            row[Column.RANGE] /= 4

        return row

    if not df.empty:
        df = df.apply(__calc_range, axis=1)

    # operating and workshop should be add due to 30k km per year
    df[Column.MY_M_COSTS] = (
        df[Column.COSTS_FIX]
        + df[Column.COSTS_OPERATING] * 2
        + df[Column.COSTS_WORKSHOP] * 2
    )

    return df.round(2)


def get_cars():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../adac.csv"))
    return pd.read_csv(path)


def _filtered_cars(df=None):
    if df is None:
        df = get_cars()

    df = _fix_numeric_columns(df)
    df = __fix_bad_data(df)

    for col in NOT_NA_COLUMNS:
        df = _filter_column(df, col)

    # TODO: remove filtering?
    # Filter seats
    df = df[df[Column.SEATS] > 3]

    df = df[df[Column.BODY_TYPE] != "Kombi"]

    # Filter transmission
    df = df[df[Column.TRANSMISSION] != Constant.TRANSMISSION_MANUAL]

    df = _fix_missing_values_by_adding_avg(df)

    return df


def __get_column_uniq_values(df):
    return df.unique()


def __string_to_adac_values(string):
    return eval(string)


def _get_sorted_uniq_values(df, ordered_values, reverse=False):
    regexps = [v for v in ordered_values if type(v) == str and r"\d" in v]
    if len(regexps) == 0:
        return ordered_values
    assert len(regexps) == 1, f"Wrong number of regexps found in {ordered_values}"
    regexp = regexps[0]
    regexp_index = ordered_values.index(regexp)
    str_values = [d for d in df if type(d) == str]
    sorted_str_values = [
        str_v
        for str_v, v in sorted(
            list(
                {
                    (v, int(re.search(regexp, v).group(1)))
                    for v in str_values
                    if re.search(regexp, v)
                }
            ),
            key=lambda x: x[1],
            reverse=reverse,
        )
    ]
    return (
        ordered_values[:regexp_index]
        + sorted_str_values
        + ordered_values[regexp_index + 1 :]
    )


def _apply_de_discount(df, column):
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
        motor_type = row["Motorart"]
        price = row[Column.PRICE]
        row[column] = row[column] - get_discount(price, motor_type)
        return row

    df = df.apply(apply_discount, axis=1)
    return df


def get_scored_df(
    only_mentioned_cars=True, de_discount=False, keep_columns=None, filtered_cars=None
):
    spec_df = pd.read_excel(
        os.path.join(os.path.dirname(__file__), "cars.xlsx"), sheet_name="Spec"
    )
    spec_df = spec_df.drop(columns=[ColumnSpec.PREFIX])

    spec_add_data_col = {
        ColumnSpec.ADAC_COLUMN,
        ColumnSpec.ADAC_VALUES,
        ColumnSpec.FEATURE,
        ColumnSpec.REVERSED,
        ColumnSpec.WEIGHT,
    }

    if only_mentioned_cars:
        df = DataFrame()
        for model in set(spec_df.columns).difference(spec_add_data_col):
            df = pd.concat(
                [
                    df,
                    _get_df_with_cost_to_own(
                        model, de_discount=de_discount, filtered_cars=filtered_cars
                    ),
                ]
            )
    else:
        df = _get_df_with_cost_to_own(
            de_discount=de_discount, filtered_cars=filtered_cars
        )

    columns_with_weights = spec_df[ColumnSpec.FEATURE]
    weighted_df = DataFrame()
    weighted_df[Column.NAME] = df[Column.NAME]
    weighted_df[Column.MARK] = df[Column.MARK]
    weighted_df[Column.SERIE] = df[Column.SERIE]
    weighted_df[Column.PERFORMANCE_KW] = df[Column.PERFORMANCE_KW]
    weighted_df[Column.TOTAL_PRICE] = df[Column.TOTAL_PRICE]
    weighted_df[Column.MY_M_COSTS] = df[Column.MY_M_COSTS]
    weighted_df[Column.RANGE] = df[Column.RANGE]
    if keep_columns:
        for col in keep_columns:
            weighted_df[col] = df[col]

    for i, row in spec_df.iterrows():
        feature = row[ColumnSpec.FEATURE]
        adac_col = row[ColumnSpec.ADAC_COLUMN]
        adac_vals = row[ColumnSpec.ADAC_VALUES]
        weight = row[ColumnSpec.WEIGHT]
        reverse = row[ColumnSpec.REVERSED] == "y"

        if only_mentioned_cars:
            # assert pd.notna(weight)
            # skip if na
            if pd.isna(weight):
                continue

        if pd.isna(adac_col):
            weight_feature = __get_feature_scores_excel(
                df[Column.NAME], row.drop(spec_add_data_col), weight
            )
        else:
            if df[adac_col].dtypes == object:
                # TODO: add support for regexp and not strings only
                df_uniq_values = __get_column_uniq_values(df[adac_col]).tolist()

                msg = f"Wrong data '{adac_vals}' in '{feature}' column: '{adac_col}', please use all possible values: {df_uniq_values}"

                assert not pd.isna(adac_vals), msg

                adac_vals = eval(adac_vals)
                adac_vals = _get_sorted_uniq_values(df[adac_col], adac_vals, reverse)
                diff = set(df_uniq_values).difference(set(adac_vals))

                # TODO: find fix for nan, nan is not hashable?????
                # assert not diff, msg + f", missing values: {diff}"

                values_data = dict(
                    zip(
                        adac_vals,
                        [
                            v / (len(adac_vals) - 1) * weight
                            for v in range(len(adac_vals))
                        ],
                    )
                )

                assert min(values_data.values()) == 0
                assert max(values_data.values()) == weight

                # TODO: fix default value! 0 if not reverse else max??
                weight_feature = df[adac_col].apply(lambda x: values_data.get(x, 0))

                # TODO: support reversed???
            else:
                weight_feature = __get_feature_scores_df(df[adac_col], weight, reverse)

        if weight_feature.isna().values.all():
            continue
        else:
            weighted_df[feature] = weight_feature

    weighted_df[Column.TOTAL_SCORE] = weighted_df.filter(columns_with_weights).sum(
        axis=1
    )
    weighted_df[Column.EURO_PER_SCORE] = (
        weighted_df[Column.TOTAL_PRICE] / weighted_df[Column.TOTAL_SCORE]
    )

    return weighted_df.sort_values(Column.TOTAL_SCORE, ascending=False)


def __get_feature_scores_df(df, weight=10, reverse=False):
    min = df.min()
    max = df.max()
    if max == min:
        df = df * weight
    else:
        if reverse:
            df = df.apply(lambda x: (1 - (x - min) / (max - min)) * weight)
        else:
            df = df.apply(lambda x: ((x - min) / (max - min)) * weight)
    return df.round(2)


def _is_model_name(full_name, part_name):
    words = re.findall(r"\w+", full_name.lower())
    search_words = re.findall(r"\w+", part_name.lower())
    if "bmw" == words[0] == search_words[0]:
        assert len(search_words) == 2, f"search '{part_name}' not supported for bmw"
        return words[1].startswith(search_words[1])
    else:
        return all([part in words for part in search_words])


def __get_feature_scores_excel(df_name, df_data, weight):
    df_data = __get_feature_scores_df(df_data.astype("float"), weight)

    def d(x):
        for key, value in df_data.iteritems():
            if _is_model_name(x, key):
                return value

        return nan

    return df_name.apply(d)
