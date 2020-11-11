import codecs
import json
import traceback

from easelenium.browser import Browser
from selenium.webdriver.common.by import By


def __main():
    css_link_to_country = (By.CSS_SELECTOR, "table.o_table tbody > tr a")

    youtube_iframe = (By.CSS_SELECTOR, ".vid_ratio iframe")

    browser = Browser("gc")

    contenders = {}
    try:
        browser.open("https://eurovisionworld.com/odds/eurovision")
        urls = [
            browser.get_attribute(e, "href")
            for e in browser.find_elements(css_link_to_country)
        ]
        for url in urls:
            browser.open(url)
            country = url.split("/")[-1]

            youtube_urls = []
            if browser.is_visible(youtube_iframe):
                youtube_url = browser.get_attribute(youtube_iframe, "src")
                print([country, youtube_url])
                youtube_urls.append(youtube_url)

            contenders[country] = youtube_urls
    except:
        traceback.print_stack()
    finally:
        browser.quit()

    with codecs.open("contenders.json", "wb", encoding="utf8") as f:
        json.dump(contenders, f)


if __name__ == "__main__":
    __main()
