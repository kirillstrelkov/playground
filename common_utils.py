import traceback
from functools import wraps

from easelenium.browser import Browser
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


def get_browser(name="gc", headless=True):
    BROWSER_NAME = name

    if name == "gc":
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("window-size=1366,768")
        options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )
    else:
        options = None
    return Browser(BROWSER_NAME, options=options)


def browser_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        browser = None
        return_value = None
        try:
            browser = get_browser()

            kwargs["browser"] = browser
            value = func(*args, **kwargs)
            return_value = value
        except:
            try:
                if browser:
                    browser.save_screenshot()
            except:
                pass
            traceback.print_exc()
        finally:
            if browser:
                browser.quit()

        return return_value

    return wrapper
