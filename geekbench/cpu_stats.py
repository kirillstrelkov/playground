import os
import re
from pprint import pprint

from common_utils import browser_decorator
from easelenium.browser import Browser
from loguru import logger
from more_itertools.recipes import flatten
from pandas import DataFrame
from selenium.webdriver.common.by import By
from tqdm import tqdm
from utils.misc import concurrent_map

URL = "https://browser.geekbench.com/v5/cpu/search?q="

INTEL_REGEXP = re.compile(r".*i(\d+)-(\d+\w+).*", re.IGNORECASE)
AMD_REGEXP = re.compile(r".*ryzen (\d+) (\d+\w+).*", re.IGNORECASE)


def _get_cpu_model(cpu):
    if "amd" in cpu.lower():
        regexp = AMD_REGEXP
    else:
        regexp = INTEL_REGEXP
    return regexp.match(cpu).group(2)


def _get_cpu_model_as_int(cpu):
    return int(re.findall(r"\d+", _get_cpu_model(cpu))[0])


class Constant(object):
    SINGLE_CORE_SCORE = "Single-Core Score"
    MULTI_CORE_SCORE = "Multi-Core Score"
    PLATFORM = "Platform"
    MODEL = "Model"
    CPU_MODEL = "CPU model"
    URL = "url"


def _get_cpu_as_int(cpu):
    _, base, suffix = re.split(r"(\d+)", cpu.lower())
    return int(base) + {"u": 0, "h": 1, "hs": 2}[suffix]


@browser_decorator
def _get_results(url: str, browser: Browser = None):
    browser.get(url)

    models = [e.text for e in browser.find_elements(by_css="div.list-col a")]
    hrefs = [
        browser.get_attribute(e, "href")
        for e in browser.find_elements(by_css="div.list-col a")
    ]
    # remove user text and links
    bad_indecies = {i for i, h in enumerate(hrefs) if "user" in h}
    models = [m for i, m in enumerate(models) if i not in bad_indecies]
    hrefs = [h for i, h in enumerate(hrefs) if i not in bad_indecies]

    cpus = [
        e.text for e in browser.find_elements(by_css="div.list-col .list-col-model")
    ]
    scores = [
        int(e.text)
        for e in browser.find_elements(by_css="div.list-col .list-col-text-score")
    ]
    singles = scores[::2]
    multies = scores[1::2]
    platforms = [
        e.text for e in browser.find_elements(by_css="div.list-col .list-col-text")
    ][1::2]

    return [
        {
            Constant.MODEL: model,
            Constant.URL: href,
            Constant.CPU_MODEL: cpu,
            Constant.SINGLE_CORE_SCORE: single,
            Constant.MULTI_CORE_SCORE: multi,
            Constant.PLATFORM: platform,
        }
        for model, href, cpu, single, multi, platform in zip(
            models, hrefs, cpus, singles, multies, platforms
        )
    ]


@browser_decorator
def __prepare_query_data(queries: [], browser: Browser = None):
    css_btn_next = (By.CSS_SELECTOR, ".page-link")

    data = []

    for query in queries:
        query = query.strip()
        browser.get(URL + query)

        if browser.find_elements(css_btn_next):
            pages = int(browser.find_elements(css_btn_next)[-2].text)
        else:
            pages = 1
        data.append({"query": query, "pages": pages})

    return data


def __get_geekbench_results(query_data: dict):
    query = query_data["query"]
    pages = query_data["pages"]

    results = []
    for page in tqdm(range(1, pages + 1)):
        results += _get_results(URL + query + f"&page={page}")
        if page == pages:
            logger.debug(f"{query} {page} {len(results)}")

    return results


def __main():
    ryzen_models = "Ryzen 5 6600U,Ryzen 5 6600H,Ryzen 5 6600HS,Ryzen 7 6800U,Ryzen 7 6800H,Ryzen 7 6800HS,Ryzen 9 6900HS,Ryzen 9 6900HX,Ryzen 9 6980HS,Ryzen 9 6980HX".split(
        ","
    )
    ryzen_models = [
        "ryzen " + m if "ryzen" not in m.lower() else m for m in ryzen_models
    ]
    intel_models = "12950HX,12900HX,12850HX,12800HX,12650HX,12600HX,12450HX,12900HK,12900H,12800H,12700H,12650H,12600H,12500H,12450H,1280P,1270P,1260P,1250P,1240P,1220P,1265U,1260U,1255U,1250U,1245U,1240U,1235U,1230U,1215U,1210U".split(
        ","
    )
    intel_models = [
        "intel " + m if "intel" not in m.lower() else m for m in intel_models
    ]

    models = ryzen_models + intel_models
    query_data = __prepare_query_data(models)
    pprint(query_data)

    data = flatten(concurrent_map(__get_geekbench_results, query_data))
    DataFrame(data).to_excel(
        os.path.join(os.path.dirname(__file__), "result.xlsx"), index=False
    )


if __name__ == "__main__":
    __main()
