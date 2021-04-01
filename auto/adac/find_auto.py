# coding=utf-8
import json
import os
import re
from datetime import datetime
from hashlib import md5
from itertools import chain

import numpy as np
import pandas as pd
from common_utils import browser_decorator
from loguru import logger
from selenium.webdriver.common.by import By
from tqdm import tqdm
from utils.lists import flatten
from utils.misc import concurrent_map, tqdm_concurrent_map

TIMEOUT_WAIT_FOR = 15

DAYS_TO_EXPIRE = 5
RANGE_5 = range(0, 5)

ID_ACCEPT_COOKIES = (By.ID, "uc-btn-accept-banner")
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


def get_number(text):
    return int(re.findall(r"\d+", str(text))[0])


def _get_adac_model_urls(browser, url):
    browser.get(url)
    return [
        browser.get_attribute(e, "href")
        for e in browser.find_elements(CSS_MODEL_trim_level)
    ]


def _get_m_url(data):
    return get_models_urls(data["price"], min_price=data.get("min_price"))


@browser_decorator
def __get_trim_level_urls(url, browser=None):
    trim_level_urls = []
    browser.get(url)
    if browser.is_visible(CSS_ID_LOAD_ALL):
        browser.click(CSS_ID_LOAD_ALL)
        browser.wait_for_not_visible(ID_OVERLAY)

    trim_level_urls += [
        browser.get_attribute(e, "href")
        for e in browser.find_elements(CSS_MODEL_trim_level)
    ]

    return trim_level_urls


def _get_trim_level_urls(price):
    model_urls = _get_model_urls(price)
    trim_level_urls = concurrent_map(__get_trim_level_urls, model_urls)
    return flatten(trim_level_urls)


@browser_decorator
def _get_model_urls(price, browser=None):
    model_urls = []

    browser.get(
        "https://www.adac.de/infotestrat/autodatenbank/"
        "wunschauto/default.aspx?ComponentId=199515&SourcePageId=287152"
    )

    __accept_cookies(browser)

    browser.click(ID_PRICE_BOX_MAX)
    browser.type(ID_PRICE_BOX_MAX_INPUT, str(price))

    browser.click(A_AKTUAL)
    browser.wait_for_visible(ID_LOADING_IMAGE, timeout=TIMEOUT_WAIT_FOR)
    browser.wait_for_not_visible(ID_LOADING_IMAGE, timeout=TIMEOUT_WAIT_FOR)

    total_count = get_number(browser.get_text(CSS_TOTAL_COUNT))
    current_count = len(browser.find_elements(CSS_CAR_MODEL))
    while total_count != current_count:
        browser.wait_for_not_visible(ID_OVERLAY, timeout=TIMEOUT_WAIT_FOR)
        if browser.is_visible(CSS_LOAD_MORE):
            browser.click(CSS_LOAD_MORE)
        browser.wait_for_not_visible(ID_LOADING_IMAGE, timeout=TIMEOUT_WAIT_FOR)
        current_count = len(browser.find_elements(CSS_CAR_MODEL))

    model_urls = [
        browser.get_attribute(e, "href") for e in browser.find_elements(CSS_CAR_MODEL)
    ]

    return model_urls


@browser_decorator
def get_models_urls(
    price, min_price=None, min_kw=None, fuel=None, mark=None, browser=None
):
    url = "https://www.adac.de/infotestrat/autodatenbank/wunschauto/default.aspx?ComponentId=199515&SourcePageId=287152"

    browser.get(url)
    log_postfix = f" with price: {min_price} - {price}"
    logger.debug(f"Processing {url}" + log_postfix)

    __accept_cookies(browser)

    browser.click(ID_PRICE_BOX_MAX)
    browser.type(ID_PRICE_BOX_MAX_INPUT, str(price))

    if min_price:
        browser.click(ID_PRICE_BOX_MIN)
        browser.type(ID_PRICE_BOX_MIN_INPUT, str(min_price))

    if fuel:
        browser.click((By.CSS_SELECTOR, "[id*=labelMotorart]"))
        browser.click((By.XPATH, '//label[text()="{}"]'.format(fuel)))

    if min_kw:
        parent = browser.get_parent(ID_SLIDER_POWER_MIN)
        browser.click(parent)
        browser.type(browser.find_descendant(parent, CSS_INPUT), str(min_kw))

    if mark:
        browser.select_option_by_value_from_dropdown(CSS_ID_MARK, mark)
        browser.wait_for_visible(ID_LOADING_IMAGE, timeout=TIMEOUT_WAIT_FOR)
        browser.wait_for_not_visible(ID_OVERLAY, timeout=TIMEOUT_WAIT_FOR)

    browser.click(A_AKTUAL)
    browser.wait_for_visible(ID_LOADING_IMAGE, timeout=TIMEOUT_WAIT_FOR)
    browser.wait_for_not_visible(ID_LOADING_IMAGE, timeout=TIMEOUT_WAIT_FOR)

    total_count = get_number(browser.get_text(CSS_TOTAL_COUNT))
    current_count = len(browser.find_elements(CSS_CAR_MODEL))
    while total_count != current_count:
        browser.wait_for_not_visible(ID_OVERLAY, timeout=TIMEOUT_WAIT_FOR)
        if browser.is_visible(CSS_LOAD_MORE):
            browser.click(CSS_LOAD_MORE)
        browser.wait_for_not_visible(ID_LOADING_IMAGE, timeout=TIMEOUT_WAIT_FOR)
        current_count = len(browser.find_elements(CSS_CAR_MODEL))

    model_urls = [
        browser.get_attribute(e, "href") for e in browser.find_elements(CSS_CAR_MODEL)
    ]
    logger.debug(f"Found {len(model_urls)} models" + log_postfix)

    trim_level_urls = []
    for url in model_urls:
        browser.get(url)
        if browser.is_visible(CSS_ID_LOAD_ALL):
            browser.click(CSS_ID_LOAD_ALL)
            browser.wait_for_not_visible(ID_OVERLAY)
        trim_level_urls += [
            browser.get_attribute(e, "href")
            for e in browser.find_elements(CSS_MODEL_trim_level)
        ]

    logger.debug(f"Found {len(trim_level_urls)} trim levels" + log_postfix)
    return trim_level_urls


def __accept_cookies(browser):
    browser.wait_for_visible(ID_ACCEPT_COOKIES)
    browser.click(ID_ACCEPT_COOKIES)
    browser.wait_for_not_visible(ID_ACCEPT_COOKIES)


def __get_cost_data(browser):
    css_tab = (By.CSS_SELECTOR, "a[href*='#kosten']")

    if not browser.is_visible(css_tab):
        return {}

    browser.click(css_tab)

    css_td = (By.CSS_SELECTOR, "td")
    css_tr = (By.CSS_SELECTOR, "tr")
    data = {
        tuple([browser.get_text(td) for td in browser.find_descendants(row, css_td)])
        for row in browser.find_elements(css_tr)
        if browser.is_visible(row)
    }
    data = dict({t for t in data if len(t) > 1})

    css_additional = (By.CSS_SELECTOR, "main div > p")
    additional = [browser.get_text(p) for p in browser.find_elements(css_additional)]
    data.update(dict(zip(additional[::2], additional[1::2])))
    data["Kosten"] = browser.get_text((By.CSS_SELECTOR, "thead > tr"))

    return data


def __get_tech_data(browser):
    css_tab_tech = (By.CSS_SELECTOR, "a[href*='#tech']")

    browser.click(css_tab_tech)

    css_td = (By.CSS_SELECTOR, "td")
    css_tr = (By.CSS_SELECTOR, "tr")
    data = {
        tuple([browser.get_text(td) for td in browser.find_descendants(row, css_td)])
        for row in browser.find_elements(css_tr)
        if browser.is_visible(row)
    }
    data = {t for t in data if len(t) > 1}

    return dict(data)


@browser_decorator
def _get_adac_data(url, browser=None):
    browser.get(url)
    url = browser.get_current_url()

    __accept_cookies(browser)

    css_model_name = (By.CSS_SELECTOR, "div h1")
    css_image = (By.CSS_SELECTOR, "main div > img")

    possible_images = browser.get_attribute(css_image, "srcset")

    model_data = {
        "name": re.sub(r"\s+", " ", browser.get_text(css_model_name)),
        "url": url,
        "id": re.findall(r"/(\d+)", url)[-1],
        "image": possible_images.split(",")[-1].split(" ")[-2],
        "processed date": datetime.now(),
    }

    stats = {}

    stats.update(__get_tech_data(browser))
    stats.update(__get_cost_data(browser))

    checksum = md5(json.dumps(stats, sort_keys=True).encode("utf8")).hexdigest()
    stats["checksum"] = checksum

    model_data.update(stats)

    return model_data


def get_adac_data(url):
    adac_data = _get_adac_data(url)
    # TODO: refactor
    if adac_data:
        return adac_data
    return None


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


def __save_models_and_trims(df__new, path):
    if os.path.exists(path):
        df = pd.read_csv(path)
        # TODO: set index to id and update instead of appen + reset_index !
        # TODO: remove/update rows if data is too old
        df = df.append(df__new)
    else:
        df = df__new
    df.to_csv(path, index=False)


def __get_id(url):
    # TODO: add new url support
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

    return pd.read_csv(path)


def __process_trim_url(data):
    url = data["url"]
    processed_checksums = data["checksums"]

    model_id = __get_id(url)

    is_processed_id = model_id in data["ids"]
    if is_processed_id:
        processed_date = data["processed date"]
        is_too_old = (
            (np.datetime64(datetime.now()) - processed_date).days > DAYS_TO_EXPIRE
        ).all()
        if is_too_old:
            logger.warning(f"{model_id} updated long time ago")
        else:
            logger.debug(f"SKIPPED: {model_id} already processed")
            return None

    try:
        adac_data = get_adac_data(url)
    except:
        logger.warning(f"Failed to get data from {url}")
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
        price_step = min_price = 5000
        # splitting into chunks to multiprocessing - 5000...10000,10000...15000,...
        urls = flatten(
            concurrent_map(
                _get_m_url,
                [
                    {"price": p, "min_price": p - 5000}
                    for p in chain(range(min_price, price, price_step), [price])
                ],
            )
        )
        with open(json_path, mode="w") as f:
            # Add my Subaru
            # TODO: fix Wertverlust, ADAC - Klassenübliche Ausstattung
            urls.append(
                "https://www.adac.de/infotestrat/autodatenbank/wunschauto/detail.aspx?mid=283761"
            )
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

    find_auto(50000, adac_path, urls_path, override_model_urls=True, parallel=True)
