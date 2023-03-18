import re
from typing import Optional
from urllib.parse import quote

from easelenium.browser import Browser
from pandas import DataFrame
from tqdm import tqdm
from utils.misc import concurrent_map, tqdm_concurrent_map

from common_utils import browser_decorator, get_number, get_numbers


class Constant:
    ADULT = "adult"
    CHILD = "child"
    ROAD_USERS = "road users"
    ASSIST = "assist"
    POINTS = "points"
    PERCENTAGE = "percentage"
    TOTAL_POINTS = "total_points"
    URL = "URL"
    NAME = "name"
    STARS = "stars"
    ID = "id"
    YEAR = "YEAR"


RAITINGS = [Constant.ADULT, Constant.CHILD, Constant.ROAD_USERS, Constant.ASSIST]


def get_points_key(property: str):
    return "_".join([property, Constant.POINTS])


def get_percent_key(property: str):
    return "_".join([property, Constant.PERCENTAGE])


def get_points_and_percentage(text: str):
    return [float(num) for num in re.findall(r"\d+\.?\d*", text)]


@browser_decorator
def get_raiting(url: str, browser: Browser = None):
    # hash is not supported in "https://www.euroncap.com/en/results/smart/#1/48000"
    splitter = "results"
    parts = url.split(splitter)
    parts[-1] = quote(parts[-1])
    url = splitter.join(parts)
    browser.open(url)

    texts = [
        e.get_attribute("innerHTML")
        for e in browser.find_elements(by_css=".details-title")
    ]
    data = {}
    for prop, (points, percent) in dict(
        zip(
            RAITINGS,
            [get_points_and_percentage(t) for t in texts],
        )
    ).items():
        data[get_points_key(prop)] = points
        data[get_percent_key(prop)] = percent

    data[Constant.TOTAL_POINTS] = sum([data[get_points_key(r)] for r in RAITINGS])
    data[Constant.URL] = url
    data[Constant.NAME] = browser.get_text(by_css="h1.car-name")
    data[Constant.STARS] = get_number(
        browser.get_attribute(by_css="div.stars img", attr="src")
    )
    data[Constant.ID] = get_numbers(url)[-1]
    data[Constant.YEAR] = get_number(browser.get_text(by_css=".introduction .year"))

    return data


@browser_decorator
def _get_urls(browser: Browser = None, name: Optional[str] = None):
    # URL contains 2017 - ...
    url = "https://www.euroncap.com/en/ratings-rewards/latest-safety-ratings/#?selectedMake=0&selectedMakeName=Select%20a%20make&selectedModel=0&selectedStar=&includeFullSafetyPackage=true&includeStandardSafetyPackage=true&selectedModelName=All&selectedProtocols=49446,45155,41776,40302,34803,30636,26061&selectedClasses=1202,1199,1201,1196,1205,1203,1198,1179,40250,1197,1204,1180,34736,44997&allClasses=true&allProtocols=false&allDriverAssistanceTechnologies=false&selectedDriverAssistanceTechnologies=&thirdRowFitment=false"
    browser.get(url)
    css_links = ".rating-table-body a"
    browser.wait_for_visible(by_css=css_links)
    urls = list(
        set(
            [
                e.get_attribute("href").lower()
                for e in browser.find_elements(by_css=css_links)
            ]
        )
    )
    if name:
        urls = [url for url in urls if name in url]

    return urls


def get_data(name: Optional[str] = None, progess: bool = False):
    urls = _get_urls(name=name)
    all_models = (tqdm_concurrent_map if progess else concurrent_map)(get_raiting, urls)

    return all_models


if __name__ == "__main__":
    df = (
        DataFrame(get_data(progess=True))
        .drop_duplicates([Constant.ID])
        .sort_values([Constant.TOTAL_POINTS], ascending=False)
    )
    df.to_excel("/tmp/euroncap.xlsx")
