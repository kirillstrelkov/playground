from geekbench.ryzen_stats import (
    _get_results,
    Constant,
    _get_cpu_as_int,
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
