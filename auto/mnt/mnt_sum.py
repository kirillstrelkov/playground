import os
from collections import defaultdict
from pprint import pprint

import pandas as pd


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

        dframes.append(df)

    df = pd.concat(dframes)
    for col in [
        "Mark",
        "Mudel",
    ]:
        df[col] = df[col].astype(str)

    df = df.convert_dtypes()

    # fix mark naming
    df["Mark"] = df["Mark"].str.upper()
    mark_namings = {"ŠKODA": "SKODA", "BMW I": "BMW"}
    df["Mark"] = df["Mark"].apply(lambda r: mark_namings.get(r, r))

    return df


def get_model_stats(df):
    group_columns = [
        "Mark",
        "Mudel",
    ]
    columns = [
        "Mark",
        "Mudel",
        "Arv",
    ]

    return (
        (df[columns].groupby(group_columns).sum())
        .reset_index()
        .sort_values("Arv", ascending=False)
    )
