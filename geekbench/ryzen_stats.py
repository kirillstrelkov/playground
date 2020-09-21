from common_utils import browser_decorator
from selenium.webdriver.common.by import By
from easelenium.browser import Browser
import os
import re
from pandas import DataFrame
from more_itertools.recipes import flatten
from utils.misc import concurrent_map, tqdm_concurrent_map
from tqdm import tqdm
from pprint import pprint
from loguru import logger
from time import sleep

URL = "https://browser.geekbench.com/v5/cpu/search?q="


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
    css_model = (By.CSS_SELECTOR, "a")
    css_cpu = (By.CSS_SELECTOR, ".list-col-model")
    css_platform = (By.CSS_SELECTOR, ".list-col-text")
    css_score = (By.CSS_SELECTOR, ".list-col-text-score")
    css_row = (By.CSS_SELECTOR, "div.list-col")
    browser.get(url)

    results = []

    for element in browser.find_elements(css_row):
        link_element = browser.find_descendant(element, css_model)
        href = browser.get_attribute(link_element, "href")
        model = link_element.text
        cpu = browser.find_element(css_cpu).text
        platform = [e.text for e in browser.find_descendants(element, css_platform)][-1]
        single, multi = [
            int(e.text) for e in browser.find_descendants(element, css_score)
        ]
        results.append(
            {
                Constant.MODEL: model,
                Constant.URL: href,
                Constant.CPU_MODEL: cpu,
                Constant.SINGLE_CORE_SCORE: single,
                Constant.MULTI_CORE_SCORE: multi,
                Constant.PLATFORM: platform,
            }
        )

    return results


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
    models = (
        "4300u,4450u,4500u,4600u,4650u,"
        "4600h,4600hs,4700u,4750u,4800u,4800h,4800hs,4900h,4900HS".split(",")
    )

    models = """4450u,4650u,4900HS""".split(",")

    query_data = __prepare_query_data(models)
    pprint(query_data)

    data = flatten(concurrent_map(__get_geekbench_results, query_data))
    DataFrame(data).to_excel(
        os.path.join(os.path.dirname(__file__), "result.xlsx"), index=False
    )


if __name__ == "__main__":
    __main()
