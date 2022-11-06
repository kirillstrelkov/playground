from auto.mobilede.mobilede import (
    _get_extra_data,
    get_data_from_mobile,
    get_data_from_mobile_page,
)


def test_get_data_single_page():
    # tesla model y
    url = "https://suchen.mobile.de/fahrzeuge/search.html?dam=0&fr=%3A2021&isSearchRequest=true&ms=135%3B6%3B%3B%3B&ref=srp&refId=b6a2129a-9f6d-5176-d7bc-73045b29eeec&s=Car&sb=rel&vc=Car"
    data = get_data_from_mobile_page(url)
    assert len(data) > 15
    first = data[0]
    assert first["power"] > 250
    assert first["reg_date"] > 2020
    assert first["milage"] > 1000
    assert first["price"] > 30000


def test_get_all_data():
    # tesla model y till 2021
    url = "https://suchen.mobile.de/fahrzeuge/search.html?dam=0&fr=%3A2021&isSearchRequest=true&ms=135%3B6%3B%3B%3B&ref=srp&refId=b6a2129a-9f6d-5176-d7bc-73045b29eeec&s=Car&sb=rel&vc=Car"
    data = get_data_from_mobile(url)
    assert len(data) > 50
    first = data[0]
    assert first["power"] > 250
    assert first["reg_date"] > 2021
    assert first["milage"] > 30000
    assert first["price"] > 30000


def test_get_extra_data():
    text = "EZ 09/2021, 31.828 km, 378 kW (514 PS)"
    assert _get_extra_data(text, "EZ") == "EZ 09/2021"
    assert _get_extra_data(text, "km") == "31.828 km"
    assert _get_extra_data(text, "kW") == "378 kW (514 PS)"

    text = "EZ 11/2021, 11.500 km"
    assert _get_extra_data(text, "EZ") == "EZ 11/2021"
    assert _get_extra_data(text, "km") == "11.500 km"
    assert _get_extra_data(text, "kw") is None
