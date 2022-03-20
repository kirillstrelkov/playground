import seaborn as sns
from auto.adac.best_car.find_best_car import Column, get_scored_df


def coloraze(df, axis=1):
    cm = sns.light_palette("seagreen", as_cmap=True)
    return df.style.background_gradient(cmap=cm, axis=axis)


def __save_excels(de_discount, feature_path):
    scored_df = get_scored_df(de_discount=de_discount, feature_file_name=feature_path)
    coloraze(scored_df, axis=0).to_excel(
        f"/tmp/scored_cars_{feature_path.split('.')[0]}.xlsx"
    )
    cols = [Column.NAME, Column.PRICE, Column.TOTAL_SCORE, Column.EURO_PER_SCORE]

    print(f"Better subaru {feature_path}")
    subaru = scored_df[scored_df.id == 283761].iloc[0]
    best = scored_df[
        (scored_df[Column.TOTAL_SCORE] > subaru[Column.TOTAL_SCORE])
        & (scored_df[Column.EURO_PER_SCORE] < subaru[Column.EURO_PER_SCORE])
    ]
    print(
        best[cols].sort_values(Column.TOTAL_SCORE, ascending=False).head(20).to_string()
    )

    quantile = 0.95
    print(f"Better {quantile * 100}% {feature_path}")
    subaru = scored_df[scored_df.id == 283761].iloc[0]
    best = scored_df[
        (
            scored_df[Column.TOTAL_SCORE]
            > scored_df[Column.TOTAL_SCORE].quantile(quantile)
        )
    ]
    print(
        best[cols].sort_values(Column.TOTAL_SCORE, ascending=False).head(20).to_string()
    )


if __name__ == "__main__":
    for de_discount, feature_path in (
        (True, "feature.csv"),
        (False, "feature_parents.csv"),
    ):
        __save_excels(de_discount, feature_path)
