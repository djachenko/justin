"""Капча: VK иногда отвечает ею на действие, и пройти её может только человек."""
from selenium.webdriver.chrome.webdriver import WebDriver

from justin.browser.shared.pacing import PAGE_SETTLE, pause


def wait_for_captcha_if_needed(driver: WebDriver, stuck_on: str) -> None:
    """Дождаться человека, если действие не увело со страницы.

    stuck_on — хвост адреса, на котором мы остаёмся, когда действие не прошло:
    у капчи нет своего признака, зато видно, что переход не случился.
    """
    pause(PAGE_SETTLE)

    if not driver.current_url.rstrip("/").endswith(stuck_on):
        return

    input("Капча! Реши её в браузере и нажми Enter здесь, когда готово: ")
