from phone.find_best_phone import _get_feature_scores, get_phone_df


def test_get_feature_scores_for_brightness():
    df = get_phone_df()
    row = df.loc[2]
    assert row[4] == "brightness"
    result = _get_feature_scores(row[5:]).to_dict()
    assert result == {
        "Nokia 7.1": 2.71,
        "s10e": 1.01,
        "Pixel 3": 0.39,
        "pixel 3a": 0.7,
        "Pixel 4a": 0.7,
        "Pixel 4": 1.32,
        "s8": 3.18,
        "s10": 5.35,
        "p30": 3.02,
        "p40": 3.69,
        "iphone se 2020": 3.8,
        "lg g7": 10.0,
        "mi a3": 0.0,
        "Nokia 7,2": 3.69,
    }


def test_get_feature_scores_for_height():
    df = get_phone_df()
    row = df.loc[0]
    assert row[4] == "height"
    result = _get_feature_scores(row[5:], reversed=True).to_dict()
    assert result["iphone se 2020"] == 10.0
    assert result == {
        "Nokia 7.1": 4.76,
        "s10e": 8.1,
        "Pixel 3": 6.67,
        "pixel 3a": 3.81,
        "Pixel 4a": 7.14,
        "Pixel 4": 5.71,
        "s8": 4.76,
        "s10": 4.76,
        "p30": 4.76,
        "p40": 5.24,
        "iphone se 2020": 10.0,
        "lg g7": 2.86,
        "mi a3": 2.86,
        "Nokia 7,2": 0.0,
    }
