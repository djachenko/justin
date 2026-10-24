"""Captcha: VK answers an action with one every so often, and only a human can pass it."""
from selenium.webdriver.chrome.webdriver import WebDriver

from justin.browser.shared.pacing import PAGE_SETTLE, pause


class CaptchaError(Exception):
    """A captcha showed up where nobody can solve it."""


def wait_for_captcha_if_needed(driver: WebDriver, stuck_on: str, headless: bool) -> None:
    """Wait for a human if the action did not take the browser off the page.

    stuck_on is the tail of the url the browser stays on when the action did not go
    through: a captcha has no marker of its own, but a missing navigation shows.
    """
    pause(PAGE_SETTLE)

    if not driver.current_url.rstrip("/").endswith(stuck_on):
        return

    if headless:
        raise CaptchaError(f"Captcha at {driver.current_url} with no window — nobody can solve it")

    input("Captcha! Solve it in the browser and press Enter here when done: ")
