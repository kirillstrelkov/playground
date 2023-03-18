import os

import pytest

from auto.mnt.mnt_sum import get_model_stats, get_summary


@pytest.mark.parametrize(
    "year,count",
    [
        ("2020", 1400),
        ("2022", 1526),
    ],
)
def test_get_model_stats(year, count):
    data_dir = os.path.join(os.path.dirname(__file__), "data", year)
    df = get_summary(data_dir)
    stats = get_model_stats(df)
    top = stats.iloc[0]
    assert top["Mark"] == "TOYOTA"
    assert top["Mudel"] == "RAV4"
    assert top["Arv"] == count


@pytest.mark.parametrize(
    "year",
    [
        ("2020"),
        ("2022"),
    ],
)
def test_fix_names(year):
    data_dir = os.path.join(os.path.dirname(__file__), "data", year)
    df = get_summary(data_dir)
    marks = df["Mark"].unique().tolist()

    assert "ŠKODA" not in marks
    assert "SKODA" in marks

    assert "BMW I" not in marks
    assert "BMW" in marks
