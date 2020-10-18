import os
import pandas as pd
from pandas.io.excel import ExcelWriter
import seaborn as sns


def get_phone_df():
    path = os.path.join(os.path.dirname(__file__), "phone_data_only.ods")
    return pd.read_excel(path, engine="odf", sheet_name="Sheet2")


def _get_feature_scores(df, weight=10, reversed=False):
    min = df.min()
    max = df.max()
    if max != min:
        if reversed:
            df = df.apply(lambda x: (1 - (x - min) / (max - min)) * weight)
        else:
            df = df.apply(lambda x: ((x - min) / (max - min)) * weight)
    return df.fillna(-0.1).round(2)


def __check_data(df):
    for index, row in df.iterrows():
        feature = row["feature"]
        df_data = row.drop(["reversed", "feature", "weight"])
        cols = df_data.index
        for i, phone_model in enumerate(cols):
            value = df_data[i]

            assert not pd.isna(
                value
            ), f"Value '{value}' is not float for '{feature}' '{phone_model}'"


def get_filtered_df(df):
    df = df[df["weight"].notnull()]
    df = df.drop(columns=["source", "comments"])
    __check_data(df)
    return df


def get_weited_df(df):
    df = get_filtered_df(df)
    weighted_df = pd.DataFrame()

    # fix: iterate properly over rows
    def _fun(x):
        feature = x["feature"]
        weight = x["weight"]
        reversed = x["reversed"] == "y"
        x = x.drop(["feature", "weight", "reversed"])
        df_feature = _get_feature_scores(x, weight=weight, reversed=reversed)
        weighted_df[f"weighted {feature}"] = df_feature
        return df_feature

    df.apply(_fun, axis=1)

    weighted_df["total score"] = weighted_df.sum(axis=1)

    return weighted_df.transpose()


def __main():
    df = get_phone_df()

    writer = ExcelWriter(os.path.join(os.path.dirname(__file__), "phones.xlsx"))
    get_filtered_df(df).to_excel(writer, sheet_name="Input data")
    get_weited_df(df).to_excel(writer, sheet_name="Scores")
    # read data
    # check if all needed data are prefilled
    # get per feature score with weights
    # calc overall score


# Ultimate:
#  specify phone models
#  input features with weights
#  get result
# use jypiter

if __name__ == "__main__":
    __main()
