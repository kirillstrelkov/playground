# coding=utf-8
import json
import os
import re
import time
from datetime import datetime
from hashlib import md5
from time import sleep

import numpy as np
import pandas as pd
from easelenium.browser import Browser
from loguru import logger
from selenium.webdriver.common.by import By
from tqdm import tqdm
from utils.lists import flatten
from utils.misc import concurrent_map, tqdm_concurrent_map

from common_utils import browser_decorator

TIMEOUT_WAIT_FOR = 15

DAYS_TO_EXPIRE = 5
RANGE_5 = range(0, 5)

ID_ACCEPT_COOKIES = (By.ID, "cmpwrapper")
ID_LOADING_IMAGE = (By.ID, "progressImage")
ID_OVERLAY = (By.ID, "overlay")
ID_PRICE_BOX_MIN = (By.CSS_SELECTOR, "[id*=Preis] .box-min")
ID_PRICE_BOX_MIN_INPUT = (By.CSS_SELECTOR, "[id*=Preis] .box-min input")
ID_PRICE_BOX_MAX = (By.CSS_SELECTOR, "[id*=Preis] .box-max")
ID_PRICE_BOX_MAX_INPUT = (By.CSS_SELECTOR, "[id*=Preis] .box-max input")
ID_SLIDER_POWER_MIN = (By.CSS_SELECTOR, "[id*=sliderLeistung-min]")
CSS_INPUT = (By.CSS_SELECTOR, "input")
A_AKTUAL = (By.XPATH, "//a[contains(text(), 'Aktualisieren')]")
CSS_CAR_MODEL = (By.CSS_SELECTOR, "a[class*=box-serie]")
CSS_TOTAL_COUNT = (By.CSS_SELECTOR, ".box-count")
CSS_LOAD_MORE = (By.CSS_SELECTOR, "a[id*=linkMore]")
CSS_MODEL_trim_level = (By.CSS_SELECTOR, "[id*=car_db_select_hits] tr .box-center a")
CSS_ID_MARK = (By.CSS_SELECTOR, "[id*='DropDownHersteller']")
CSS_ID_LOAD_ALL = (By.CSS_SELECTOR, "[id*='LinkAlleLaden']")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def fix_german_number(text):
    return text.replace(".", "").replace(",", ".")


def _get_m_url(data):
    return get_model_urls(data["price"], min_price=data.get("min_price"))


def _open_url(browser, url):
    browser.get(url)
    __accept_cookies(browser)


def __get_url_with_queries(
    browser: Browser,
    price: int,
    min_price=1000,
    mark=None,
    new_cars_only=True,
):
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/autosuche/"
    if new_cars_only:
        url += "?newCarsOnly=true"

    _open_url(browser, url)

    # add price to url
    browser.click(by_css="[for='basePrice']")

    min_supported_price = int(
        fix_german_number(
            browser.get_value(by_css="#basePrice-container input[name='basePrice']")
        )
    )
    max_supported_price = int(
        fix_german_number(
            browser.get_value(by_css="#basePrice-secondary-container input")
        )
    )
    assert min_supported_price <= min_price
    assert max_supported_price >= price
    url += f"&basePrice.min={min_price}&basePrice.max={price}"

    # add mark to url
    _open_url(browser, url)
    if mark:
        browser.type(by_id="brand-input", text=mark)
        browser.click(by_css="#brand-suggestions > li")
        btn_search = "//main//button[contains(text(), 'anzeigen')]"
        browser.click(by_xpath=btn_search)
        browser.wait_for_visible(by_xpath=btn_search)

    return browser.get_current_url()


@browser_decorator
def get_model_urls(
    price=None,
    min_price=1000,
    mark=None,
    new_cars_only=True,
    url=None,
    browser=None,
):
    log_postfix = ""
    if not url:
        log_postfix = f" with price: {min_price} - {price}"
        logger.debug(f"Processing {log_postfix}")
        url = __get_url_with_queries(browser, price, min_price, mark, new_cars_only)
    else:
        _open_url(browser, url)

    logger.debug(f"Processing {url}")

    css_model_link = "tbody a"
    max_page = max(
        [1]
        + [
            int(e.text)
            for e in browser.find_elements(by_css='[data-testid="pagination"] a')
            if e.text
        ]
    )

    model_urls = []
    for page_index in range(1, max_page + 1):
        _open_url(browser, f"{url}&pageNumber={page_index}")
        if max_page > 1:
            browser.wait_for_present(by_css=css_model_link)
        else:
            sleep(1)

        model_urls += [
            e.get_attribute("href")
            for e in browser.find_elements(by_css=css_model_link)
        ]

    logger.debug(f"Found {len(model_urls)} " + log_postfix)
    return model_urls


def __accept_cookies(browser):
    browser.wait_for_present(ID_ACCEPT_COOKIES)
    # remove content
    browser.execute_js(
        f"return document.getElementById('{ID_ACCEPT_COOKIES[1]}').remove();"
    )
    # browser.click(ID_ACCEPT_COOKIES)
    browser.wait_for_not_present(ID_ACCEPT_COOKIES)


def __get_cost_data(browser):
    css_tab = (By.CSS_SELECTOR, "a[href*='#kosten']")

    if not browser.is_visible(css_tab):
        return {}

    browser.click(css_tab)

    cells = [
        browser.get_text(e)
        for e in browser.find_elements(by_css="[title='Laufende Kosten'] td")
    ]
    data = dict(zip(cells[::2], cells[1::2]))

    css_additional = (By.CSS_SELECTOR, "[title='Laufende Kosten'] main div > p")
    additional = [browser.get_text(p) for p in browser.find_elements(css_additional)]
    data.update(dict(zip(additional[::2], additional[1::2])))
    data["Kosten"] = browser.get_text(
        (By.CSS_SELECTOR, "[title='Laufende Kosten'] thead > tr")
    )

    return data


def __get_tech_data(browser):
    css_tab_tech = (By.CSS_SELECTOR, "a[href*='#tech']")

    browser.click(css_tab_tech)

    cells = [
        browser.get_text(e)
        for e in browser.find_elements(by_css="[title='Technische Daten'] td")
    ]
    data = dict(zip(cells[::2], cells[1::2]))

    text = browser.get_attribute(
        by_css="[title='Technische Daten'] main div picture source",
        attr="srcset",
    )
    matches = re.findall("http.*?.jpg", text)
    data["image"] = matches[-1] if matches else None

    return data


@browser_decorator
def get_adac_data(url, browser=None):
    _open_url(browser, url)
    url = browser.get_current_url()

    model_data = {
        "name": re.sub(r"\s+", " ", browser.get_text(by_css="div h1")),
        "url": url,
        "id": re.findall(r"/(\d+)", url)[-1],
        "processed date": datetime.now(),
    }

    stats = {}

    stats.update(__get_tech_data(browser))
    stats.update(__get_cost_data(browser))

    checksum = md5(json.dumps(stats, sort_keys=True).encode("utf8")).hexdigest()
    stats["checksum"] = checksum

    model_data.update(stats)

    return model_data


def __get_data_for_trim_processing(url, df_old_data=None):
    if df_old_data is not None:
        ids = df_old_data["id"].unique()
        processed_ids = set(df_old_data["id"].unique())
        assert len(ids) == len(processed_ids)

        checksums = df_old_data["checksum"].unique()
        processed_checksums = set(df_old_data["checksum"].unique())
        assert len(checksums) == len(processed_checksums)

        processed_date = df_old_data[df_old_data["id"] == __get_id(url)][
            "processed date"
        ]
    else:
        checksums = []
        processed_ids = set()
        processed_checksums = set()
        processed_date = datetime.now()

    return {
        "url": url,
        "ids": processed_ids,
        "checksums": checksums,
        "processed date": pd.to_datetime(processed_date),
    }


def __save_models_and_trims(df_new, path):
    if os.path.exists(path):
        df = pd.read_csv(path)
        # TODO: set index to id and update instead of appen + reset_index !
        # TODO: remove/update rows if data is too old
        df = pd.concat([df, df_new])
    else:
        df = df_new
    df.to_csv(path, index=False)


def __get_id(url):
    new_url = "autokatalog/marken-modelle" in url
    if new_url:
        return int(re.findall(r"\d+", url)[-1])
    else:
        return int(re.search(r"mid=(\d+)", url).group(1))


def __save_iteratively(urls, path):
    # TODO: remove/update rows if data is too old
    if os.path.exists(path):
        df_old_data = pd.read_csv(path)
    else:
        df_old_data = None

    for url in tqdm(urls):
        adac_data = __process_trim_url(__get_data_for_trim_processing(url, df_old_data))

        if not adac_data:
            continue

        __save_models_and_trims(pd.DataFrame([adac_data]), path)

    return pd.read_csv(path) if urls else pd.DataFrame()


def __process_trim_url(data):
    # TODO: tenacity retry if failed

    url = data["url"]
    processed_checksums = data["checksums"]

    model_id = __get_id(url)

    is_processed_id = model_id in data["ids"]
    if is_processed_id:
        processed_date = data["processed date"].iloc[0]
        is_too_old = (
            np.datetime64(datetime.now()) - processed_date
        ).days > DAYS_TO_EXPIRE
        if is_too_old:
            logger.warning(f"{model_id} updated long time ago")
        else:
            logger.debug(f"SKIPPED: {model_id} already processed")
            return None

    try:
        adac_data = get_adac_data(url)
    except Exception as e:
        logger.error(f"Failed to get data from {url}")
        logger.exception(e)
        adac_data = None

    if adac_data is None:
        logger.debug(f"SKIPPED: {model_id} failed to get data")
        return None

    if adac_data["checksum"] in processed_checksums:
        logger.debug(f"SKIPPED: {model_id} same checksum")
        return None

    logger.debug(f"Adding {model_id} {adac_data['name']}")
    return adac_data


def __save_parallel(urls, path):
    if os.path.exists(path):
        df_old_data = pd.read_csv(path)
    else:
        df_old_data = None

    data = tqdm_concurrent_map(
        __process_trim_url,
        [__get_data_for_trim_processing(url, df_old_data) for url in urls],
    )
    df = pd.DataFrame([d for d in data if d])

    __save_models_and_trims(df, path)

    return df


def find_auto(price, output_path, json_path, override_model_urls=False, parallel=False):
    if os.path.exists(json_path) and not override_model_urls:
        with open(json_path, mode="r") as f:
            urls = json.load(f)
    else:
        price_step = 5000
        # splitting into chunks to multiprocessing - 5000...10000,10000...15000,...
        prices = [p for p in range(1000, price, price_step)]
        prices.append(price)
        chunks = [
            {"price": prices[i], "min_price": prices[i - 1]}
            for i in range(1, len(prices))
        ]
        if parallel:
            urls = flatten(
                concurrent_map(
                    _get_m_url,
                    chunks,
                )
            )
        else:
            urls = flatten([_get_m_url(chunk) for chunk in chunks])
        with open(json_path, mode="w") as f:
            json.dump(urls, f)

    logger.info("Total models with different trim levels: {}".format(len(urls)))

    if parallel:
        df = __save_parallel(urls, output_path)
    else:
        df = __save_iteratively(urls, output_path)

    return df


if __name__ == "__main__":
    adac_path = os.path.join(os.path.dirname(__file__), "adac.csv")
    urls_path = os.path.join(os.path.dirname(__file__), "adac_urls.json")

    find_auto(65000, adac_path, urls_path, override_model_urls=True, parallel=True)
