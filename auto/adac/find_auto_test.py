from unittest.case import TestCase

from auto.adac.find_auto import (
    _get_adac_data,
    _get_model_urls,
    _get_trim_level_urls,
    find_auto,
    get_adac_data,
    get_models_urls,
)
from tempfile import TemporaryDirectory
import os


def __filter_model_urls(urls, url_part):
    return [url for url in urls if url_part in url]


def test_get_models_urls():
    price = 24000
    mark = "VW"
    model_urls = get_models_urls(price, mark=mark)
    assert len(model_urls) > 40

    for model in ("t-roc", "t-cross", "golf"):
        assert len(__filter_model_urls(model_urls, model)) >= 1


def test_get_adac_data():
    url = "https://www.adac.de/infotestrat/autodatenbank/wunschauto/detail.aspx?mid=304532&bezeichnung=vw-polo-1-0-mpi-beats"
    data = _get_adac_data(url)
    for key, expected in (
        ("id", "304532"),
        (
            "image",
            "https://www.adac.de/_ext/itr/tests/ADAC40/Autodaten/Bilder/IM05016_1_VW_Polo_VI_1566x884.jpg",
        ),
        ("LED-Scheinwerfer", "985 Euro"),
        ("Durchrostung", "12 Jahre"),
        ("Metallic-Lackierung", "495 Euro"),
        ("Typ", "beats"),
        ("Haltedauer", "5 Jahre"),
        ("Fixkosten", "86 €"),
        ("Typklassen (KH/VK/TK)", "15/16/17"),
        ("Leistung maximal in kW (Systemleistung)", "59"),
        ("checksum", "c9de13c277287d75f42a2063c0c5dcd7"),
    ):
        assert key in data
        assert data[key] == expected


def test_get_adac_data2():
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/alfa-romeo/giulia/952/311389/"
    data = _get_adac_data(url)
    for key, expected in (
        ("id", "311389"),
        ("Xenon-Scheinwerfer", "877 Euro"),
        ("Durchrostung", "8 Jahre"),
        ("Metallic-Lackierung", "926 Euro"),
        ("Typ", "AT8"),
        ("Haltedauer", "5 Jahre"),
        ("Fixkosten", "137 €"),
        ("Typklassen (KH/VK/TK)", "20/24/23"),
        ("Leistung maximal in kW (Systemleistung)", "147"),
        ("checksum", "df456fd01bd9ca1e31a8753f3a4943cd"),
    ):
        assert key in data
        assert data[key] == expected


def test_get_adac_data_corsa():
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/opel/corsa/f/312301/"
    data = _get_adac_data(url)
    for key, expected in (
        ("id", "312301"),
        ("Fixkosten", "88 €"),
        ("Betriebskosten", "95 €"),
        ("checksum", "8b9998295d8f258149b8d7310f4b53ee"),
    ):
        assert key in data
        assert data[key] == expected


def test_get_adac_data_tesla():
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/tesla/model-3/1generation/308033/"
    data = _get_adac_data(url)
    for key, expected in (
        ("id", "308033"),
        ("Bremsassistent", "Serie"),
        ("checksum", "abc34625386d812f20dd9cc35e173a37"),
    ):
        assert key in data
        assert data[key] == expected


def test_find_models():
    initial_models = _get_model_urls(15000)
    assert 25 < len(initial_models) < 30
    assert "up!" in initial_models[-1]


def test_get_trim_level_urls():
    price = 10000
    model_urls = _get_model_urls(price)
    trim_level_urls = _get_trim_level_urls(price)
    assert len(model_urls) < len(trim_level_urls)


def test_find_cars_parallel():
    with TemporaryDirectory() as tmp_dir:
        json_path = os.path.join(tmp_dir, "adac.json")
        csv_path = os.path.join(tmp_dir, "adac.csv")
        cars = find_auto(10000, csv_path, json_path, parallel=True)
        rows, cols = cars.shape

        assert rows >= 4


def test_find_cars_iteratevly():
    with TemporaryDirectory() as tmp_dir:
        json_path = os.path.join(tmp_dir, "adac.json")
        csv_path = os.path.join(tmp_dir, "adac.csv")
        cars = find_auto(10000, csv_path, json_path, parallel=False)
        rows, cols = cars.shape

        assert rows >= 4
