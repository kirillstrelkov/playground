import json
import os

from utils.file import read_content

from auto.adac.vscar.prepare_json_file import NUMERIC_TYPES


def test_json_attributes():
    datas = json.loads(
        read_content(os.path.join(os.path.dirname(__file__), "car.json"))
    )
    for data in datas:
        supported_types = {"str"} | NUMERIC_TYPES
        name = data["name"]
        adac_id = data["adac_id"]
        assert data["attributes"]
        for attr in data["attributes"]:
            column_data = attr["column_data"]
            assert "type" in column_data
            attr_type = column_data["type"]
            assert (
                attr_type in supported_types
            ), f"Wrong type {attr_type} in {adac_id} {name}"

            if attr_type in NUMERIC_TYPES and attr["value"]:
                assert (
                    "min" in column_data["range"] and "max" in column_data["range"]
                ), f"Wrong data in {adac_id} {name}"
                assert column_data["range"]["min"] <= column_data["range"]["max"]
