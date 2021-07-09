# coding=utf-8
import json
import os
import re
from datetime import datetime
from hashlib import md5
from time import sleep

import numpy as np
import pandas as pd
from common_utils import browser_decorator
from easelenium.browser import Browser
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


def fix_german_number(text):
    return text.replace(".", "").replace(",", ".")


def get_number(text):
    return int(re.findall(r"\d+", str(text))[0])


def _get_m_url(data):
    return get_model_urls(data["price"], min_price=data.get("min_price"))


def __get_url_with_queries(
    browser: Browser,
    price: int,
    min_price=1000,
    min_kw=None,
    mark=None,
    new_cars_only=True,
):
    url = "https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/autosuche/"
    if new_cars_only:
        url += "?newCarsOnly=true"

    browser.get(url)

    __accept_cookies(browser)

    # add price to url

    min_supported_price = int(
        fix_german_number(
            browser.get_value(
                by_xpath="//*[@id='basePrice']/../..//*[@for='basePrice']",
                visible=False,
            )
        )
    )
    max_supported_price = int(
        fix_german_number(
            browser.get_value(
                by_xpath="//*[@id='basePrice']/../..//*[@for='basePrice-secondary']",
                visible=False,
            )
        )
    )
    assert min_supported_price <= min_price
    assert max_supported_price >= price
    url += f"&basePrice.min={min_price}&basePrice.max={price}"

    if min_kw:
        # add kW to url
        min_supported_kw = int(
            fix_german_number(
                browser.get_value(
                    by_xpath="//*[@id='powerInKW']/../..//*[@for='powerInKW']",
                    visible=False,
                )
            )
        )
        max_supported_kw = int(
            fix_german_number(
                browser.get_value(
                    by_xpath="//*[@id='powerInKW']/../..//*[@for='powerInKW-secondary']",
                    visible=False,
                )
            )
        )
        assert min_supported_kw <= min_kw <= max_supported_kw
        url += f"&powerInKW.min={min_kw}&powerInKW.max={max_supported_kw}"

    # add mark to url
    browser.get(url)
    if mark:
        browser.type(by_id="brand-input", text=mark)
        browser.click(by_css="#brand-suggestions > li")
        btn_search = "//main//button[contains(text(), 'anzeigen')]"
        browser.click(by_xpath=btn_search)
        browser.wait_for_visible(by_xpath=btn_search)

    return browser.get_current_url()


@browser_decorator
def get_model_urls(
    price,
    min_price=1000,
    min_kw=None,
    mark=None,
    new_cars_only=True,
    browser=None,
):
    log_postfix = f" with price: {min_price} - {price}"
    logger.debug(f"Processing {log_postfix}")
    url = __get_url_with_queries(browser, price, min_price, min_kw, mark, new_cars_only)
    logger.debug(f"Processing {url}")

    # find all cars/trim level
    model_urls = []

    model_href = "//main//a[contains(@href, 'autokatalog')]"

    load_more = "//button[text()='Weitere Ergebnisse']"
    while browser.is_visible(by_xpath=load_more):
        models_count = len(browser.find_elements(by_xpath=model_href))
        browser.click(by_xpath=load_more)
        browser.webdriver_wait(
            lambda driver: models_count
            < len(browser.find_elements(by_xpath=model_href)),
            timeout=10,
        )

    model_urls = [
        e.get_attribute("href") for e in browser.find_elements(by_xpath=model_href)
    ]

    # first is skipped because it is a search button
    model_urls = model_urls[1:]

    logger.debug(f"Found {len(model_urls)} " + log_postfix)
    return model_urls


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
def get_adac_data(url, browser=None):
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

    return pd.read_csv(path)


def __process_trim_url(data):
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
        price_step = 5000
        # splitting into chunks to multiprocessing - 5000...10000,10000...15000,...
        prices = [p for p in range(1000, price, price_step)]
        prices.append(price)
        chunks = [
            {"price": prices[i], "min_price": prices[i - 1]}
            for i in range(1, len(prices))
        ]
        urls = flatten(
            concurrent_map(
                _get_m_url,
                chunks,
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
