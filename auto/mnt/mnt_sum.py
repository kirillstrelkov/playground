import os
import re
from pathlib import Path

import pandas as pd
import yaml
from loguru import logger
from utils.misc import tqdm_concurrent_map

YEARS = list(range(2018, 2026))
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR_YEARS = DATA_DIR / "private"
__OUTPUT = DATA_DIR / "history.csv"
__SUV_PATH = DATA_DIR / "suvs.yaml"

PRIVATE_CUSTOMER = "FÜÜSILINE"

COLUMN_SHORT_NAME = "short name"
COLUMN_CUSTOMER = "Tüüp (isik)"
COLUMN_COUNT = "Arv"
COLUMN_CITY = "Linn"
COLUMN_REG_DATE = "Esm reg aasta"
COLUMN_ENGINE_TYPE = "Mootori tüüp"
COLUMN_TRANSMISSION = "Käigukasti tüüp"
COLUMN_SUV = "SUV"
COLUMN_MARK = "Mark"
COLUMN_COLOR = "Värv"
COLUMN_ENGINE_VOLUME = "Mootori maht"
COLUMNS = [
    COLUMN_MARK,
    "Mudel",
    COLUMN_SHORT_NAME,
    COLUMN_ENGINE_TYPE,
    COLUMN_ENGINE_VOLUME,
    "Mootori võimsus",
    COLUMN_TRANSMISSION,
    COLUMN_CITY,
    COLUMN_CUSTOMER,
    COLUMN_SUV,
    COLUMN_COUNT,
    COLUMN_COLOR,
]


def __get_name_by_split(name: str, times: str = 2) -> str:
    return " ".join(name.split()[:times])


def __get_bmw(name: str) -> str:
    name = name.replace("W M", "W ")
    if re.search(r"BMW [\d]", name):
        return name[:5]
    return __get_name_by_split(name)


def __replace(text, mappings):
    for _old, _new in mappings.items():
        text = text.replace(_old, _new)
    return text


def _fix_name(name: str) -> str:
    # remove double make
    parts = name.split()
    if parts[0] == parts[1]:
        name = parts[0] + " " + " ".join([p for p in parts[2:] if p != parts[0]])

    mark = name.split()[0]
    model_name_len = {
        "ASTON": 3,
        "ALFA": 3,
        "CITROEN": 3,
        "LAND": 10,
        "BYD": 3,
        "JEEP": 3,
        "GREAT": 10,
        "HONDA": 10,
        "HYNDAI": 3,
        "KG": 3,
        "LUCID": 10,
        "MAXUS": 3,
        "MERCEDES-AMG": 3,
        "TESLA": 3,
        "SSANGYONG": 3,
    }

    special_names = {
        "AUDI": lambda n: __replace(
            n,
            {
                "AUDI S ": "AUDI ",
                "AUDI S": "AUDI A",
                " RS ": " A",
                "AQ": "Q",
                "AUDI AE": "AUDI E",
                "A8L": "A8",
            },
        ),
        "BMW": __get_bmw,
        "HYUNDAI": lambda n: __replace(
            n,
            {
                "HYUNDAI I ": "HYUNDAI I",
                "0N": "0",
                "0 N": "0",
            },
        ).strip(),
        "LYNK&CO": lambda n: n.replace("LYNK & CO ", ""),
        "MERCEDES-BENZ": lambda n: n.replace("MERCEDES-BENZ AMG ", "MERCEDES-BENZ "),
        "TESLA": lambda n: n.replace("MOTORS ", ""),
        "OPEL": lambda n: n.replace("ASTRA+", "ASTRA"),
        "LEXUS": lambda n: n[:8],
    }
    if func := special_names.get(mark):
        name = func(name)

    return __get_name_by_split(name, model_name_len.get(mark, 2))


def get_summary(path: Path) -> pd.DataFrame:
    if Path(path).is_dir():
        files = sorted(
            [Path(os.path.join(path, p)) for p in os.listdir(path) if os.path.isfile(os.path.join(path, p))],
        )
    else:
        files = [path]

    dframes = []
    for f in files:
        if "lock." in f.name:
            continue
        logger.trace(f"Reading file {f}")
        df = pd.read_excel(io=f, sheet_name="Uued sõidukid", skiprows=3)
        df = df[df.Kategooria.apply(lambda x: "M1" in str(x))]

        # replace columns
        columns_mappings = {
            "Väljalaske aasta": COLUMN_REG_DATE,
            "MOOTORI_TYYP": COLUMN_ENGINE_TYPE,
            "V.KAS/OM Linn": COLUMN_CITY,
            "V.KAS/OM TYYP": COLUMN_CUSTOMER,
            "Year of ESMANE_REG_KP": COLUMN_REG_DATE,
            "tk": "Arv",
            "MOOTORI_VOIMSUS": "Mootori võimsus",
            "MOOTORI_MAHT": "Mootori maht",
            "VARV": "Värv",
            "KAIGUKASTI_TYYP": COLUMN_TRANSMISSION,
        }

        if COLUMN_CUSTOMER not in df.columns:
            columns_mappings.update({"Tüüp": COLUMN_CUSTOMER})

        df = df.rename(columns=columns_mappings)

        year = df[COLUMN_REG_DATE].value_counts(dropna=True, ascending=False).index.tolist()[0]
        df = df[df[COLUMN_REG_DATE] == year]
        df[COLUMN_REG_DATE] = pd.to_numeric(df[COLUMN_REG_DATE], downcast="integer")

        dframes.append(df)

    if not dframes:
        return pd.DataFrame()

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

    df[COLUMN_SHORT_NAME] = df["name"].apply(_fix_name)

    def _fix_customer(customer):
        customer = customer.upper()
        if "FYYSILINE" in customer:
            return PRIVATE_CUSTOMER
        if "JURIIDILINE" in customer:
            return "JÜRIIDILINE"
        return customer.replace(" ISIK", "")

    # Fix customers
    df[COLUMN_CUSTOMER] = df[COLUMN_CUSTOMER].apply(_fix_customer)

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
            lambda t: ("CNG" if "CNG" in t else __replace(t, {" ": "_", "Ü": "Y", "KAT.": "KATALYSAATOR"})),
        )
    )

    assert len(df.columns) == len(set(df.columns))

    suvs = set(yaml.safe_load(__SUV_PATH.read_text().upper()))
    df[COLUMN_SUV] = df[COLUMN_SHORT_NAME].str.upper().isin(suvs)

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


def get_history_df() -> pd.DataFrame:
    """Get full history dataframe."""
    return pd.read_csv(__OUTPUT).reset_index(drop=True)


def merge() -> None:
    """Merge all years data into single csv file."""
    dirs = [DATA_DIR_YEARS / str(year) for year in YEARS]
    dframes = tqdm_concurrent_map(get_summary, dirs)
    # dframes = [get_summary(p) for p in dirs]
    df = pd.concat(dframes)
    df.to_csv(__OUTPUT, index=False)
    print(f"Saved merged data to {__OUTPUT}")  # noqa: T201


if __name__ == "__main__":
    merge()
