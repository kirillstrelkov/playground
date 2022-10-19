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
    url = "https://www.euroncap.com/en/results/tesla/model+y/46618"
    data = get_raiting(url)
    assert data[get_points_key(Constant.ADULT)] == 36.9
    assert data[get_percent_key(Constant.ADULT)] == 97
    assert data[get_points_key(Constant.CHILD)] == 43
    assert data[get_percent_key(Constant.CHILD)] == 87
    assert data[get_points_key(Constant.ROAD_USERS)] == 44.8
    assert data[get_percent_key(Constant.ROAD_USERS)] == 82
    assert data[get_points_key(Constant.ASSIST)] == 15.7
    assert data[get_percent_key(Constant.ASSIST)] == 98
    assert data[Constant.TOTAL_POINTS] == 140.4


def test_single_car_2021():
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


def test_get_data():
    data = get_data(name="impreza")
    assert len(data) >= 1
    impreza = data[0]
    assert impreza[Constant.TOTAL_POINTS] == 122.7
