import os
import re

import pandas as pd

PRIVATE_CUSTOMER = "FÜÜSILINE"

COLUMN_SHORT_NAME = "short name"
COLUMN_CUSTOMER = "Tüüp (isik)"
COLUMN_COUNT = "Arv"
COLUMN_CITY = "Linn"
COLUMN_REG_DATE = "Esm reg aasta"
COLUMN_ENGINE_TYPE = "Mootori tüüp"
COLUMNS = [
    "Mark",
    "Mudel",
    COLUMN_SHORT_NAME,
    "Mootori tüüp",
    "Mootori maht",
    "Mootori võimsus",
    COLUMN_CITY,
    COLUMN_CUSTOMER,
    "Arv",
    "Värv",
]


def get_summary(folder):
    files = sorted(
        [
            os.path.join(folder, p)
            for p in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, p))
        ]
    )

    dframes = []
    for f in files:
        if "lock." in f:
            continue
        df = pd.read_excel(io=f, sheet_name="Uued sõidukid", skiprows=3)
        df = df[df.Kategooria.apply(lambda x: "M1" in str(x))]

        # replace columns
        columns_mappings = {"Väljalaske aasta": COLUMN_REG_DATE}
        if COLUMN_CUSTOMER not in df.columns:
            columns_mappings.update({"Tüüp": COLUMN_CUSTOMER})

        df = df.rename(columns=columns_mappings)

        year = (
            df[COLUMN_REG_DATE]
            .value_counts(dropna=True, ascending=False)
            .reset_index()["index"]
            .tolist()[0]
        )
        df = df[df[COLUMN_REG_DATE] == year]
        df[COLUMN_REG_DATE] = pd.to_numeric(df[COLUMN_REG_DATE], downcast="integer")

        dframes.append(df)

    df = pd.concat(dframes)
    for col in [
        "Mark",
        "Mudel",
        "Mootori tüüp",
        COLUMN_CITY,
        COLUMN_CUSTOMER,
    ]:
        df[col] = df[col].astype(str)

    df = df.convert_dtypes()

    # fix mark naming
    df["Mark"] = df["Mark"].str.upper()
    mark_namings = {"ŠKODA": "SKODA", "BMW I": "BMW"}
    df["Mark"] = df["Mark"].apply(lambda r: mark_namings.get(r, r))

    df["name"] = df["Mark"] + " " + df["Mudel"]

    # add short name
    def _get_name_by_split(name, times=2):
        return " ".join(name.split(" ")[:times])

    def _get_bmw(name):
        name = name.replace("W M", "W ")
        if re.search(r"BMW [\d]", name):
            return name[:5]
        else:
            return _get_name_by_split(name)

    def _replace(text, mappings):
        for _old, _new in mappings.items():
            text = text.replace(_old, _new)
        return text

    def _fix_name(name):
        mark = name.split()[0]
        name_with_2_words = {
            "BENTLEY",
            "CUPRA",
            "FIAT",
            "HONDA",
            "MAZDA",
            "MERCEDES-BENZ",
            "MINI",
            "NISSAN",
            "PORSCHE",
            "RENAULT",
            "SEAT",
            "SKODA",
            "VOLKSWAGEN",
            "VOLVO",
        }
        special_names = {
            "AUDI": lambda n: _get_name_by_split(
                _replace(n, {" S": " A", " RS ": " A", "AQ": "Q", "AUDI AE": "AUDI E"})
            ),  # default 2 words
            "ALFA": lambda n: _get_name_by_split(n, 3),
            "BMW": _get_bmw,
            "CITROEN": lambda n: _replace(n, {"E-": ""}),
            "HYUNDAI": lambda n: _replace(n, {"0N": "0", "0 N": "0"}),
            "LEXUS": lambda n: n[:8],
            "OPEL": lambda n: _get_name_by_split(_replace(n, {"ASTRA+": "ASTRA"})),
            "TOYOTA": lambda n: _replace(
                n,
                {
                    " PHV": "",
                    " GR ": " ",
                    " PLUS": "",
                },
            ),
        }
        if mark in name_with_2_words:
            return _get_name_by_split(name)
        elif special_names.get(mark):
            func = special_names.get(mark)
            return func(name)
        else:
            return name

    df[COLUMN_SHORT_NAME] = df["name"].apply(_fix_name)

    # Fix customers
    df[COLUMN_CUSTOMER] = (
        df[COLUMN_CUSTOMER].str.upper().apply(lambda c: c.replace(" ISIK", ""))
    )

    # Fix city
    df[COLUMN_CITY] = (
        df[COLUMN_CITY]
        .str.replace(" linn", "")
        .str.strip()
        .apply(lambda c: {"Narva- Jõesuu": "Narva-Jõesuu"}.get(c, c))
    )

    # Fix engine types
    df[COLUMN_ENGINE_TYPE] = (
        df[COLUMN_ENGINE_TYPE]
        .str.upper()
        .apply(
            lambda t: "CNG"
            if "CNG" in t
            else _replace(t, {" ": "_", "Ü": "Y", "KAT.": "KATALYSAATOR"})
        )
    )

    assert len(df.columns) == len(set(df.columns))

    return df


def get_model_stats(df):
    columns = [
        COLUMN_SHORT_NAME,
        COLUMN_COUNT,
    ]

    tmp_df = (
        (df[columns].groupby(COLUMN_SHORT_NAME).sum([COLUMN_COUNT]))
        .reset_index()
        .sort_values(COLUMN_COUNT, ascending=False)
    )
    tmp_df["Mark"] = tmp_df[COLUMN_SHORT_NAME].str.split(expand=True)[0]
    return tmp_df[["Mark", COLUMN_SHORT_NAME, COLUMN_COUNT]]
