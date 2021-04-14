import re
import traceback

from auto.adac.best_car.find_best_car import _is_model_name
from common_utils import browser_decorator
from numpy import mean
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

CSS_SEARCH_INPUT = (By.CSS_SELECTOR, "input.search__input")
CSS_SEARCH_BTN = (By.CSS_SELECTOR, "button.js-search-submit")
CSS_MORE_REVIEWS = (By.CSS_SELECTOR, "button.js-show-more-reviews")
CSS_PRODUCT_BLOCK = (By.CSS_SELECTOR, ".product__block")
CSS_PRODUCT_LINK = (By.CSS_SELECTOR, ".product-view-link")
CSS_TITLE = (By.CSS_SELECTOR, ".product__title")
CSS_REVIEW_TITLE = (By.CSS_SELECTOR, ".review__title")
CSS_PAGE_TITLE = (By.CSS_SELECTOR, ".page-title__name")
CSS_NR_TESTS = (By.CSS_SELECTOR, ".badge__bottom")


def _find_possibile_blocks(browser, query):
    blocks = []

    e_blocks = browser.find_elements(CSS_PRODUCT_BLOCK)
    for i, e_block in enumerate(e_blocks):
        text = browser.get_text(e_block)
        title = browser.get_text(browser.find_descendant(e_block, CSS_TITLE))
        match = re.search(r"\((\d+)\)", title)
        if (
            "ohne Endnote" not in browser.get_text(e_block)
            and match
            and _is_model_name(title, query)
        ):
            url = browser.get_attribute(
                browser.find_elements(CSS_PRODUCT_LINK)[i], "href"
            )

            year = int(match.group(1))

            blocks.append({"url": url, "title": title, "year": year, "text": text})

    return sorted(blocks, key=lambda x: (-len(x["title"]), x["year"]), reverse=True)


@browser_decorator
def find_score(query, browser=None):
    data = {
        "query": query,
        "name": "",
        "scores": [],
        "average": 0,
    }

    browser.get("https://www.testberichte.de/")

    css_cookie_frame = (By.CSS_SELECTOR, "[title='SP Consent Message']")
    css_accept_cookies = (
        By.XPATH,
        "(//button[contains(text(), 'Zustimmen')])[2]",
    )

    browser.wait_for_visible(css_cookie_frame)
    browser.switch_to_frame(css_cookie_frame)
    browser.click(css_accept_cookies)
    browser.switch_to_default_content()

    browser.type(CSS_SEARCH_INPUT, query + "\n")

    for block in _find_possibile_blocks(browser, query):
        browser.get(block["url"])

        browser.wait_for_visible(CSS_TITLE)
        if browser.is_visible(CSS_MORE_REVIEWS):
            browser.click(CSS_MORE_REVIEWS)

        raitings = [
            browser.get_text(e) for e in browser.find_elements(CSS_REVIEW_TITLE)
        ]
        raitings = [r for r in raitings if "Punkten" in r and "," not in r]

        if len(raitings) == 0:
            continue

        data["name"] = browser.get_text(CSS_PAGE_TITLE)
        for raiting in raitings:
            numbers = re.findall(r"\d+", raiting[: raiting.index("Punkten")])
            assert len(numbers) == 2
            data["scores"].append({"score": int(numbers[0]), "total": int(numbers[1])})

        if data["scores"]:
            data["average"] = mean(
                [d["score"] / float(d["total"]) for d in data["scores"]]
            )

        return data

    return data


if __name__ == "__main__":
    # cars = "Peugeot 208,opel corsa,hyundai ioniq hybrid plugin,kia xceed,kia ceed,ford focus,vw golf,seat leon,skoda octavia,toyota corolla,opel grandland x,subaru impreza,renault captur,renault clio,Peugeot 2008,ford puma,ford fiesta,Peugeot 3008,skoda karoq,skoda kodiaq,kia sportage,vw t roc,vw tiguan,subaru outback,hyundai tucson,seat ateca,vw t-cross,Mercedes A,Mercedes B,audi a1,audi a3,Bmw 1,honda civic,Toyota rav4,Peugeot 508,Opel insignia, tesla model 3, ford kuga".split(
    cars = "seat leon,vw golf".split(",")
    for car in cars:
        d = find_score(car + " 2021")
        if d:
            print(f"{d['query']},{d['name']},{d['average']}")
        else:
            print("Not data for {car}")
