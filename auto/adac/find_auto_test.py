import os
from tempfile import TemporaryDirectory

from auto.adac.find_auto import find_auto, get_adac_data, get_model_urls


def __filter_model_urls(urls, url_part):
    return [url for url in urls if url_part in url]


def test_urls():
    price = 20000
    model_urls = get_model_urls(price)
    assert len(model_urls) > 70


def test_get_models_urls_vw():
    price = 28000
    mark = "VW"
    model_urls = get_model_urls(price, mark=mark)
    assert len(model_urls) > 20

    for model in ("t-roc", "t-cross", "polo"):
        assert len(__filter_model_urls(model_urls, model)) >= 1


def test_get_models_urls_many_cars():
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/autosuche/?newCarsOnly=true&basePrice.min=16000&basePrice.max=21000"

    model_urls = get_model_urls(url=url)
    assert len(model_urls) > 100


def test_get_models_urls():
    price = 20000
    model_urls = get_model_urls(price)
    assert len(model_urls) > 50


def test_get_adac_data_alfa():
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/alfa-romeo/giulia/952/311389/"
    data = get_adac_data(url)
    for key, expected in (
        ("id", "311389"),
        ("Xenon-Scheinwerfer", "877 Euro"),
        ("Durchrostung", "8 Jahre"),
        ("Metallic-Lackierung", "926 Euro"),
        ("Typ", "AT8"),
        ("Fixkosten", "139 €"),
        ("Leistung maximal in kW (Systemleistung)", "147"),
    ):
        assert key in data
        assert data[key] == expected


def test_get_adac_data_corsa():
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/opel/corsa/f/312301/"
    data = get_adac_data(url)
    assert data["image"] is not None
    for key, expected in (
        ("id", "312301"),
        ("Fixkosten", "87 €"),
        ("Betriebskosten", "107 €"),
    ):
        assert key in data
        assert data[key] == expected


def test_get_adac_data_tesla():
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/tesla/model-3/1generation/308033/"
    data = get_adac_data(url)
    assert data["image"] is not None
    for key, expected in (
        ("id", "308033"),
        ("Bremsassistent", "Serie"),
    ):
        assert key in data
        assert data[key] == expected


def test_find_cars_parallel():
    with TemporaryDirectory() as tmp_dir:
        json_path = os.path.join(tmp_dir, "adac.json")
        csv_path = os.path.join(tmp_dir, "adac.csv")
        cars = find_auto(11000, csv_path, json_path, parallel=True)
        rows, cols = cars.shape

        assert rows >= 4


def test_find_cars_iteratevly():
    with TemporaryDirectory() as tmp_dir:
        json_path = os.path.join(tmp_dir, "adac.json")
        csv_path = os.path.join(tmp_dir, "adac.csv")
        cars = find_auto(9000, csv_path, json_path, parallel=False)
        rows, cols = cars.shape

        assert rows >= 3
