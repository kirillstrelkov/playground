import math

import numpy as np
from easelenium.browser import Browser
from loguru import logger
from utils.misc import concurrent_map, tqdm_concurrent_map

from auto.adac.find_auto import fix_german_number, get_number, get_numbers
from common_utils import browser_decorator

# chrome_options = webdriver.ChromeOptions()
# prefs = {"profile.managed_default_content_settings.images": 2}
# chrome_options.add_experimental_option("prefs", prefs)


@browser_decorator
def get_data_from_mobile(url: str, browser: Browser = None):
    css_result = "[data-testid='result-list-headline']"

    pages = 1
    browser.get(url)
    found = get_number(browser.get_text(by_css=css_result).replace(".", ""))
    logger.info("Found: {}", found)
    pages = int(math.ceil(found / 20.0))
    logger.info("Pages: {}", pages)

    tmp_data = concurrent_map(
        get_data_from_mobile_page,
        [url + "&pageNumber={}".format(i) for i in range(1, pages + 1)],
    )
    data = []
    uniq_ids = set()
    for d1 in tmp_data:
        for d in d1:
            d_id = get_number(d["url"])
            if d_id not in uniq_ids:
                uniq_ids.add(d_id)
                data.append(d)
            else:
                logger.warning("Duplicate: {}", d_id)

    logger.info("Loaded: {}", len(data))
    return data


def _get_extra_data(text: str, text_part: str):
    found = [part for part in text.split(",") if text_part in part]
    return found[0].strip() if found else None


@browser_decorator
def get_data_from_mobile_page(url: str, browser: Browser = None):
    css_header = ".headline-block .h3"
    css_reg_mil_pow = "[data-testid='regMilPow']"

    css_price = ".price-block .h3:not(.u-text-red)"
    css_e_url = "a.result-item"
    data = []
    browser.get(url)

    for css_result in [
        ".cBox-body.cBox-body--eyeCatcher",
        ".cBox-body.cBox-body--resultitem",
    ]:
        for r in browser.find_elements(by_css=css_result):
            mobile_name = browser.get_text(
                browser.find_descendant(parent=r, by_css=css_header)
            )
            mobile_url = browser.get_attribute(
                browser.find_descendant(parent=r, by_css=css_e_url), "href"
            )
            t_reg_mil_pow = browser.get_text(
                browser.find_descendant(parent=r, by_css=css_reg_mil_pow)
            )
            t_price = browser.get_text(
                browser.find_descendant(parent=r, by_css=css_price)
            ).replace(".", "")

            power_s = _get_extra_data(t_reg_mil_pow, "kW")
            power = get_number(power_s) if power_s else np.nan

            milage_s = _get_extra_data(t_reg_mil_pow, "km")
            milage = get_number(fix_german_number(milage_s)) if milage_s else np.nan

            date_s = _get_extra_data(t_reg_mil_pow, "EZ")
            if date_s:
                month, year = get_numbers(date_s)
                reg_date = year + round(month / 13.0, 2)
            else:
                reg_date = np.nan

            data.append(
                {
                    "name": mobile_name,
                    "url": mobile_url,
                    # "reg_mil_pow": t_reg_mil_pow,
                    "reg_date": reg_date,
                    "power": power,
                    "milage": milage,
                    "price": get_number(t_price),
                }
            )

    return data
