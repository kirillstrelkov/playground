import os

import pandas as pd

from geekbench.cpu_stats import (
    AMD_REGEXP,
    INTEL_REGEXP,
    Constant,
    _get_cpu_as_int,
    _get_cpu_model,
    _get_cpu_model_as_int,
    _get_results,
    _prepare_query_data,
)

LOADED_DF = pd.read_excel(os.path.join(os.path.dirname(__file__), "result.xlsx"))


def test_single_row():
    result = _get_results("https://browser.geekbench.com/v5/cpu/search?page=1&q=4600h")[
        0
    ]
    assert result[Constant.SINGLE_CORE_SCORE] > 600
    assert result[Constant.MULTI_CORE_SCORE] > 2000
    assert "http" in result[Constant.URL]
    assert "4600H" in result[Constant.CPU_MODEL]
    assert "2020" not in result[Constant.MODEL]
    assert result[Constant.PLATFORM] in ["Windows", "Linux"]


def test_get_cpu_as_int():
    assert _get_cpu_as_int("4800u") == 4800
    assert _get_cpu_as_int("4800U") == 4800
    assert _get_cpu_as_int("4800h") == 4801
    assert _get_cpu_as_int("4800H") == 4801
    assert _get_cpu_as_int("4800hs") == 4802
    assert _get_cpu_as_int("4800HS") == 4802


def test_regexp():
    assert _get_cpu_model("AMD Ryzen 7 6800HS 3201 MHz (8 cores)") == "6800HS"
    assert _get_cpu_model("AMD Ryzen 9 6900HX 3301 MHz (8 cores)") == "6900HX"
    assert _get_cpu_model("Intel Core i7-12700H 2693 MHz (14 cores)") == "12700H"
    assert _get_cpu_model("Intel Core i7-1260P 2100 MHz (12 cores)") == "1260P"
    assert _get_cpu_model("Intel Core i5-1235U 2493 MHz (10 cores)") == "1235U"
    assert _get_cpu_model("AMD Ryzen 5 PRO 6650U 2901 MHz (6 cores)") == "6650U"
    assert _get_cpu_model("AMD Ryzen 7 PRO 6850U 2701 MHz (8 cores)") == "6850U"
    for cpu in LOADED_DF["CPU model"].unique().tolist():
        assert _get_cpu_model_as_int(cpu) > -2


def test_get_cpu_as_int():
    assert _get_cpu_as_int("4800u") == 4800
    assert _get_cpu_as_int("4800U") == 4800
    assert _get_cpu_as_int("4800h") == 4801
    assert _get_cpu_as_int("4800H") == 4801
    assert _get_cpu_as_int("4800hs") == 4802
    assert _get_cpu_as_int("4800HS") == 4802


def test_prepare_query_data():
    q = _prepare_query_data(["intel 12700H"])
    assert q[0]["pages"] > 500


def test_all_cpus_are_supported():
    for cpu_model in LOADED_DF["CPU model"]:
        if "Xeon" not in cpu_model:
            assert _get_cpu_model(cpu_model) is not None
