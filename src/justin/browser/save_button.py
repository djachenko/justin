"""VK dropped the .group_save class — the save button is now matched by its label."""
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

SAVE_LABELS = {"save", "сохранить"}


def find_save_buttons(driver: WebDriver) -> list[WebElement]:
    return [
        el for el in driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
        if el.is_displayed() and el.text.strip().lower() in SAVE_LABELS
    ]
