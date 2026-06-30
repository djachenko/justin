"""Schema for editing an existing VK event via ?act=edit."""
import time
from dataclasses import dataclass
from datetime import datetime

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_setup_settings import EventSetupSettings


def _clear_and_type(driver: WebDriver, el, value: str) -> None:
    driver.execute_script("arguments[0].value = ''", el)
    el.send_keys(value)
    time.sleep(0.3)


def _fill_date_field(driver: WebDriver, date_input_id: str, dt: datetime,
                     hour_idx: int = 0) -> None:
    """Fill VK date text input + adjacent hour/minute inputs.

    date_input_id: 'group_start_date_date_input' or 'group_finish_date_date_input'
    hour_idx: index into aria-label="Час" spinbuttons (0=start, 1=end)
    """
    date_el = driver.find_element(By.CSS_SELECTOR, f"[id='{date_input_id}']")
    driver.execute_script("arguments[0].click()", date_el)
    time.sleep(0.4)

    date_str = f"{dt.day:02d}.{dt.month:02d}.{dt.year}"
    driver.execute_script("arguments[0].value = ''", date_el)
    date_el.send_keys(date_str)
    date_el.send_keys(Keys.TAB)
    time.sleep(0.3)

    for aria_label, val, idx in [
        ("Час", f"{dt.hour:02d}", hour_idx),
        ("Минута", f"{dt.minute:02d}", hour_idx),
    ]:
        els = driver.find_elements(By.CSS_SELECTOR, f'[aria-label="{aria_label}"]')
        if idx < len(els):
            driver.execute_script("arguments[0].focus()", els[idx])
            els[idx].send_keys(val)
            time.sleep(0.2)


@dataclass(frozen=True)
class EventSetupSchema:
    _SETTINGS_URL_TMPL: str = "https://vk.com/event{event_id}?act=edit"

    def __call__(self, event_id: int, settings: EventSetupSettings,
                 driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(self._SETTINGS_URL_TMPL.format(event_id=event_id))
        self._wait_for_form(driver, wait)

        if settings.title is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='group_edit_name']")
            _clear_and_type(driver, el, settings.title)

        if settings.description is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='group_edit_desc']")
            _clear_and_type(driver, el, settings.description)

        if settings.website is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='group_website']")
            _clear_and_type(driver, el, settings.website)

        if settings.phone is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='group_edit_phone']")
            _clear_and_type(driver, el, settings.phone)

        if settings.email is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='event_mail']")
            _clear_and_type(driver, el, settings.email)

        if settings.city is not None:
            self._set_city(driver, settings.city)

        if settings.start_dt is not None:
            _fill_date_field(driver, "group_start_date_date_input", settings.start_dt, hour_idx=0)

        if settings.end_dt is not None:
            _fill_date_field(driver, "group_finish_date_date_input", settings.end_dt, hour_idx=1)

        self._save(driver, wait)

    @staticmethod
    def _wait_for_form(driver: WebDriver, wait: WebDriverWait) -> None:
        from selenium.common.exceptions import StaleElementReferenceException

        def content_ready(d) -> bool:
            try:
                skeletons = d.find_elements(By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
                if not any(el.is_displayed() for el in skeletons):
                    return True
                rm = d.find_elements(By.CSS_SELECTOR, "[data-testid='rightmenu']")
                return bool(rm and rm[0].is_displayed())
            except StaleElementReferenceException:
                return False

        wait.until(content_ready)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.0)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(0.3)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[id='group_edit_name']")))

    @staticmethod
    def _unnamed_inputs(driver: WebDriver) -> list:
        """Return visible text inputs without a known id, in DOM order.

        Observed order (stable across page loads):
          0 — category  (e.g. 'Circus')
          1 — organizer (e.g. 'Garik Dyachenko')
          2 — start hour
          3 — start minute
          4 — end hour
          5 — end minute
          6 — city      (e.g. 'Novosibirsk')
        """
        known_ids = {
            "group_edit_name", "group_edit_addr", "group_website",
            "group_edit_phone", "event_mail",
            "group_start_date_date_input", "group_finish_date_date_input",
        }
        return [
            el for el in driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if el.is_displayed() and el.get_attribute("id") not in known_ids
            and not (el.get_attribute("id") or "").startswith("search-")
        ]

    @staticmethod
    def _set_city(driver: WebDriver, city: str) -> None:
        unnamed = EventSetupSchema._unnamed_inputs(driver)
        if len(unnamed) >= 7:
            _clear_and_type(driver, unnamed[6], city)

    @staticmethod
    def _save(driver: WebDriver, wait: WebDriverWait) -> None:
        save_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.group_save")
        ))
        driver.execute_script("arguments[0].click()", save_btn)
        time.sleep(1.0)
