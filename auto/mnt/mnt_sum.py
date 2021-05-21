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
    return df


def get_model_stats(df):
    return (
        df[
            [
                "Mark",
                "Mudel",
                "Mootori võimsus",
                "Arv",
            ]
        ]
        .groupby(
            [
                "Mark",
                "Mudel",
                "Mootori võimsus",
            ]
        )
        .sum()
    )


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "data/2020")
    df = get_summary(data_dir)
    # stats = get_model_stats(df).sort_values("Arv", ascending=False)
    # print(stats.head(20))
