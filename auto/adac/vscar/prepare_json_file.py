import os

import pandas as pd


def __main():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, "../adac.csv"))

    # adding fuel, power, price
    df["fuel"] = df["Kraftstoffart"]
    df["transmission"] = df["Getriebeart"]
    df["power"] = df["Leistung maximal in kW (Systemleistung)"]
    df["price"] = df["Grundpreis"].str.replace(" Euro", "").astype(int)

    # replaceing column names
    old_cols = df.columns.to_list()
    # save columns which will be fields - "left part"
    last_db_field = "processed date"
    last_db_field_index = old_cols.index(last_db_field)
    df.columns = [
        {"id": "adac_id", "processed date": "processed_date"}.get(c, c)
        for c in old_cols
    ]

    old_cols = df.columns.to_list()
    new_columns = old_cols[: last_db_field_index + 1] + [
        col.replace(".", "") for col in old_cols[last_db_field_index + 1 :]
    ]

    df.columns = new_columns
    main_attributes = new_columns[: last_db_field_index + 1] + [
        "fuel",
        "price",
        "power",
        "transmission",
        "image",
    ]
    additional_attributes = [
        c for c in df.columns.to_list() if c not in main_attributes
    ]

    new_rows = []
    for _, row in df.iterrows():
        data = {k: v for k, v in row.items() if k in main_attributes}
        data["attributes"] = [
            {"name": k, "value": v}
            for k, v in row.items()
            if k in additional_attributes
        ]
        new_rows.append(data)

    df = pd.DataFrame(new_rows)
    df = df.drop_duplicates(subset=["adac_id"])
    df.to_json(os.path.join(cur_dir, "car.json"), orient="records")


if __name__ == "__main__":
    __main()
