import time
from dataclasses import dataclass, fields

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.section_settings import (
    SectionSettings,
)


@dataclass(frozen=True)
class Toggle:
    test_id: str

    def set_value(self, value: bool, driver: WebDriver, wait: WebDriverWait) -> None:
        el = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{self.test_id}"]')
        currently_enabled = el.get_attribute("aria-checked") != "false"

        if currently_enabled != value:
            driver.execute_script("arguments[0].click()", el)
            time.sleep(0.5)


@dataclass(frozen=True)
class Radio:
    def set_value(self, value: object, driver: WebDriver, wait: WebDriverWait) -> None:
        el = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{value.value}"]')  # type: ignore[union-attr]
        driver.execute_script("arguments[0].click()", el)
        time.sleep(0.3)


@dataclass(frozen=True)
class Dropdown:
    test_id: str

    def set_value(self, value: object, driver: WebDriver, wait: WebDriverWait) -> None:
        trigger = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{self.test_id}"]')
        driver.execute_script("arguments[0].click()", trigger)
        time.sleep(0.5)
        option_text = value.value  # type: ignore[union-attr]
        option = wait.until(lambda d: next(
            (el for el in d.find_elements(By.CSS_SELECTOR, "[data-testid='dropdownactionsheet-item']")
             if el.is_displayed() and option_text in el.text),
            None,
        ))
        driver.execute_script("arguments[0].click()", option)
        time.sleep(0.3)


@dataclass(frozen=True)
class SectionSchema:
    test_id: str
    enabled: Toggle
    _SECTION_PAUSE: float = 1.5

    def __call__(self, settings: SectionSettings, driver: WebDriver, wait: WebDriverWait) -> None:
        self._open(driver, wait)
        self.enabled.set_value(settings.enabled, driver, wait)
        if settings.enabled:
            for f in fields(settings):
                if f.name == "enabled":
                    continue
                getattr(self, f.name).set_value(getattr(settings, f.name), driver, wait)
        self._save(driver, wait)
        time.sleep(self._SECTION_PAUSE)

    def _open(self, driver: WebDriver, wait: WebDriverWait) -> None:
        item = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="{self.test_id}"]')))
        driver.execute_script("arguments[0].click()", item)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-testid="{self.enabled.test_id}"]')))
        time.sleep(0.5)

    def _save(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="form_modal_save"]')))
        driver.execute_script("arguments[0].click()", btn)
        time.sleep(0.5)


@dataclass(frozen=True)
class PostsSchema(SectionSchema):
    enabled: Toggle = Toggle("form_wall_enabled")
    publishing: Dropdown = Dropdown("form_wall_publishing_allowed")
    sharing_disabled: Toggle = Toggle("form_wall_sharing_disabled")


@dataclass(frozen=True)
class PhotosSchema(SectionSchema):
    enabled: Toggle = Toggle("form_photos_toggle")
    content_type: Radio = Radio()
    add_allowed: Radio = Radio()


@dataclass(frozen=True)
class VideosSchema(SectionSchema):
    enabled: Toggle = Toggle("form_videos_toggle")
    content_type: Radio = Radio()
    add_allowed: Radio = Radio()


@dataclass(frozen=True)
class TopicsSchema(SectionSchema):
    enabled: Toggle = Toggle("form_discussions_toggle")
    add_allowed: Radio = Radio()


@dataclass(frozen=True)
class MusicSchema(SectionSchema):
    enabled: Toggle = Toggle("form_audios_toggle")
    content_type: Radio = Radio()
    add_allowed: Radio = Radio()


@dataclass(frozen=True)
class FilesSchema(SectionSchema):
    enabled: Toggle = Toggle("form_files_toggle")
    add_allowed: Radio = Radio()


@dataclass(frozen=True)
class MaterialsSchema(SectionSchema):
    enabled: Toggle = Toggle("form_wiki_toggle")
    add_allowed: Radio = Radio()
