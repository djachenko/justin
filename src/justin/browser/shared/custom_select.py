"""VKUI CustomSelect: a readonly input backed by a hidden native select."""
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.shared.elements import by_css, found
from justin.browser.shared.pacing import AFTER_ACTION, pause


def option_by_value(value: str) -> str:
    """Option labels are localised — VKUI puts the value into the option id instead."""
    return f"[role='option'][id$='-{value}']"


def set_custom_select(driver: WebDriver, wait: WebDriverWait, holder, value: str) -> None:
    """Open the select, pick the option carrying value and check the input took its label."""
    driver.execute_script("arguments[0].click()", holder)

    option = found(
        wait,
        lambda d: next(
            (el for el in d.find_elements(*by_css(option_by_value(value))) if el.is_displayed()),
            None
        )
    )

    label = option.text.strip()

    option.click()

    pause(AFTER_ACTION)

    shown = holder.get_attribute("value").strip()

    if shown != label:
        raise ValueError(f"Option not applied: select shows {shown!r}, expected {label!r}")
