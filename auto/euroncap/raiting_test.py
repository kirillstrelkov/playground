from typing import Any

import pytest

from auto.euroncap.raiting import (
    Constant,
    get_data,
    get_percent_key,
    get_points_and_percentage,
    get_points_key,
    get_raiting,
)


@pytest.mark.parametrize(
    "text,result",
    [
        ("Total 43 Pts / 87%", [43.0, 87.0]),
        ("VRU Protection:\nTotal 44.8 Pts / 82%", [44.8, 82.0]),
    ],
)
def test_get_points_and_percentage(text: str, result: Any):
    assert get_points_and_percentage(text) == result


def test_single_car_2022():
    url = "https://www.euroncap.com/en/results/smart/#1/48000"
    data = get_raiting(url)
    assert data[get_points_key(Constant.ADULT)] == 36.6
    assert data[get_percent_key(Constant.ADULT)] == 96
    assert data[get_points_key(Constant.CHILD)] == 43.8
    assert data[get_percent_key(Constant.CHILD)] == 89
    assert data[get_points_key(Constant.ROAD_USERS)] == 38.9
    assert data[get_percent_key(Constant.ROAD_USERS)] == 71
    assert data[get_points_key(Constant.ASSIST)] == 14.1
    assert data[get_percent_key(Constant.ASSIST)] == 88
    assert data[Constant.TOTAL_POINTS] == 133.4
    assert data[Constant.NAME] == "smart #1"
    assert data[Constant.ID] == 48000
    assert data[Constant.YEAR] == 2022


def test_single_car_2017():
    url = "https://www.euroncap.com/en/results/subaru/impreza/29084"
    data = get_raiting(url)
    assert data[get_points_key(Constant.ADULT)] == 35.8
    assert data[get_percent_key(Constant.ADULT)] == 94
    assert data[get_points_key(Constant.CHILD)] == 44.0
    assert data[get_percent_key(Constant.CHILD)] == 89
    assert data[get_points_key(Constant.ROAD_USERS)] == 34.6
    assert data[get_percent_key(Constant.ROAD_USERS)] == 82
    assert data[get_points_key(Constant.ASSIST)] == 8.3
    assert data[get_percent_key(Constant.ASSIST)] == 68
    assert data[Constant.TOTAL_POINTS] == 122.7
    assert data[Constant.NAME] == "Subaru Impreza"
    assert data[Constant.ID] == 29084
    assert data[Constant.YEAR] == 2017


@pytest.mark.parametrize(
    "name,stars",
    [
        ("impreza", 5),
        ("408", 4),
        ("i10", 3),
        ("logan", 2),
        ("jogger", 1),
        ("zoe", 0),
    ],
)
def test_stars(name, stars):
    urls = {
        "impreza": "https://www.euroncap.com/en/results/subaru/impreza/29084",
        "408": "https://www.euroncap.com/en/results/peugeot/408/48757",
        "i10": "https://www.euroncap.com/en/results/hyundai/i10/41393",
        "logan": "https://www.euroncap.com/en/results/dacia/logan/42505",
        "jogger": "https://www.euroncap.com/en/results/dacia/jogger/45231",
        "zoe": "https://www.euroncap.com/en/results/renault/zoe/44206",
    }
    data = get_raiting(urls[name])
    assert data[Constant.STARS] == stars


def test_get_data():
    data = get_data(name="impreza")
    assert len(data) >= 1
    impreza = data[0]
    assert impreza[Constant.TOTAL_POINTS] == 122.7
