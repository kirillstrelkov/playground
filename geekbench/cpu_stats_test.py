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
)


def test_single_row():
    result = _get_results("https://browser.geekbench.com/v5/cpu/search?page=1&q=4500u")[
        0
    ]
    assert result[Constant.SINGLE_CORE_SCORE] > 500
    assert result[Constant.MULTI_CORE_SCORE] > 3000
    assert "http" in result[Constant.URL]
    assert "4500U" in result[Constant.CPU_MODEL]
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
    df = pd.read_excel(os.path.join(os.path.dirname(__file__), "result.xlsx"))
    for cpu in df["CPU model"].unique().tolist():
        assert _get_cpu_model_as_int(cpu) > 0
