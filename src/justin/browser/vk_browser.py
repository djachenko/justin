import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.page_explorer import PageExplorer
from justin.browser.section_settings import (
    FilesSettings, MaterialsSettings, MusicSettings,
    PhotosSettings, PostsSettings, SectionsConfig,
    TopicsSettings, VideosSettings, PostsPublishing,
)


class VKBrowser:
    _BROWSER_DATA_DIR = Path.home() / ".justin" / "browser_data"
    _WIZARD_IFRAME_CSS = "#react_rootcommunity_create iframe"
    _TIMEOUT = 0.5 * 60
    _PACE = 1.0  # global pause multiplier: 0 = no delays, 1 = normal, 2 = slow

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={self._BROWSER_DATA_DIR}")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")

        logging.getLogger("selenium").setLevel(logging.DEBUG)
        self._driver = webdriver.Chrome(options=options)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._driver.quit()

    def _pause(self, jitter: float = 0.5) -> None:
        if self._PACE > 0:
            time.sleep(self._PACE * random.uniform(1 - jitter, 1 + jitter))

    def _wait(self, wait: WebDriverWait, condition: Callable, label: str = "") -> Any:
        try:
            return wait.until(condition)
        except TimeoutException:
            PageExplorer(self._driver).explore()
            raise

    def create_event(
        self,
        title: str,
        start_dt: datetime,
        end_dt: datetime | None = None,
        organiser_id: int | None = None,
        is_closed: bool = True,
    ) -> int:
        driver = self._driver
        wait = WebDriverWait(driver, self._TIMEOUT)

        driver.get("https://vk.com/groups/my_events?w=groups_create_new_event")

        iframe = self._wait(wait, EC.presence_of_element_located((By.CSS_SELECTOR, self._WIZARD_IFRAME_CSS)))
        driver.switch_to.frame(iframe)

        # --- Step 1 ---

        title_input = self._wait(wait, EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="title_input"]')))
        ActionChains(driver).click(title_input).send_keys(title).perform()
        self._pause()

        if is_closed:
            select_el = driver.find_element(By.CSS_SELECTOR, '[name="access"]')
            driver.execute_script("arguments[0].click()", select_el)
            time.sleep(0.5)
            closed_option = driver.find_element(By.CSS_SELECTOR, '[role="option"][value="1"]')
            driver.execute_script("arguments[0].click()", closed_option)
            self._pause()

        self._fill_date_input(driver, start_dt)
        self._pause()

        if end_dt is not None:
            end_date_btn = self._wait(wait, EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Enter end date')]")))
            driver.execute_script("arguments[0].click()", end_date_btn)
            self._pause()
            self._fill_date_input_nth(driver, end_dt, n=1)
            self._pause()

        if organiser_id is not None:
            self._set_select_value(driver, "eventGroupId", str(abs(organiser_id)))
            self._pause()

        continue_btn = self._wait(wait, EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="done_button"]')))
        continue_btn.click()
        self._pause()

        # --- Step 2: category ---

        circus_btn = self._wait(wait, EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-name="Circus"]')))
        driver.execute_script("arguments[0].click()", circus_btn)
        self._pause()

        create_btn = self._wait(wait, EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Create event' and not(@disabled)]")
        ))
        create_btn.click()
        self._pause()

        go_to_community_btn = self._wait(wait, EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="go_to_community"]')))
        go_to_community_btn.click()

        driver.switch_to.default_content()

        self._wait_for_captcha_if_needed(driver)

        self._wait(wait, lambda d: re.search(r'(?:event|club)\d+', d.current_url) is not None)

        return self._parse_event_id(driver.current_url)

    @staticmethod
    def _fill_date_input(driver, dt: datetime) -> None:
        VKBrowser._fill_date_input_nth(driver, dt, n=0)

    @staticmethod
    def _fill_date_input_nth(driver, dt: datetime, n: int) -> None:
        parts = [
            ("День", str(dt.day).zfill(2)),
            ("Месяц", str(dt.month).zfill(2)),
            ("Год", str(dt.year)),
            ("Час", str(dt.hour).zfill(2)),
            ("Минута", str(dt.minute).zfill(2)),
        ]
        for aria_label, value in parts:
            spinbuttons = driver.find_elements(By.CSS_SELECTOR, f'[aria-label="{aria_label}"]')
            spinbutton = spinbuttons[n]
            driver.execute_script("arguments[0].focus()", spinbutton)
            spinbutton.send_keys(value)

    @staticmethod
    def _set_select_value(driver, name: str, value: str) -> None:
        driver.execute_script("""
            var select = document.querySelector('[name="' + arguments[0] + '"]');
            var setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
            setter.call(select, arguments[1]);
            select.dispatchEvent(new Event('change', {bubbles: true}));
        """, name, value)

    @staticmethod
    def _wait_for_captcha_if_needed(driver) -> None:
        time.sleep(2)
        if driver.current_url.rstrip("/").endswith("/groups_create"):
            input("Капча! Реши её в браузере и нажми Enter здесь, когда готово: ")

    def explore_sections(self, event_id: int, out_dir: Path | None = None) -> None:
        from justin.browser.settings_explorer import SettingsExplorer
        target = out_dir or Path(f"explore_output_{event_id}")
        SettingsExplorer(self._driver, event_id, target).run()

    _USE_SCHEMA = True

    def set_sections(self, event_id: int, config: "SectionsConfig | None" = None) -> None:
        if config is None:
            config = SectionsConfig()

        driver = self._driver
        wait = WebDriverWait(driver, self._TIMEOUT)
        driver.get(f"https://vk.com/event{event_id}/settings/sections")
        self._wait(wait, EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="list_enabled"]')))

        if self._USE_SCHEMA:
            self._set_sections_schema(driver, wait, config)
        else:
            self._set_sections_legacy(driver, wait, config)

    def _set_sections_schema(self, driver, wait, config: "SectionsConfig") -> None:
        from justin.browser.section_schema import (
            FilesSchema, MaterialsSchema, MusicSchema,
            PhotosSchema, PostsSchema, TopicsSchema, VideosSchema,
        )
        if config.posts is not None:
            PostsSchema("wall")(config.posts, driver, wait)
        if config.photos is not None:
            PhotosSchema("photos")(config.photos, driver, wait)
        if config.videos is not None:
            VideosSchema("videos")(config.videos, driver, wait)
        if config.topics is not None:
            TopicsSchema("discussions")(config.topics, driver, wait)
        if config.music is not None:
            MusicSchema("audios")(config.music, driver, wait)
        if config.files is not None:
            FilesSchema("files")(config.files, driver, wait)
        if config.materials is not None:
            MaterialsSchema("wiki")(config.materials, driver, wait)

    def _set_sections_legacy(self, driver, wait, config: "SectionsConfig") -> None:
        if config.posts is not None:
            self._configure_posts(driver, wait, config.posts)
        if config.photos is not None:
            self._configure_photos(driver, wait, config.photos)
        if config.videos is not None:
            self._configure_videos(driver, wait, config.videos)
        if config.topics is not None:
            self._configure_topics(driver, wait, config.topics)
        if config.music is not None:
            self._configure_music(driver, wait, config.music)
        if config.files is not None:
            self._configure_files(driver, wait, config.files)
        if config.materials is not None:
            self._configure_materials(driver, wait, config.materials)

    def _open_section(self, driver, wait, section_testid: str, modal_testid: str) -> None:
        item = self._wait(wait, EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="{section_testid}"]')))
        driver.execute_script("arguments[0].click()", item)
        self._wait(wait, EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-testid="{modal_testid}"]')))
        self._pause()

    def _set_toggle(self, driver, testid: str, enabled: bool) -> None:
        el = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{testid}"]')
        # aria-checked=None или "true" = включено, "false" = выключено
        currently_enabled = el.get_attribute("aria-checked") != "false"
        if currently_enabled != enabled:
            driver.execute_script("arguments[0].click()", el)
            self._pause()

    def _set_radio(self, driver, testid: str) -> None:
        el = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{testid}"]')
        driver.execute_script("arguments[0].click()", el)
        self._pause()

    def _select_dropdown(self, driver, wait, trigger_testid: str, option_text: str) -> None:
        trigger = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{trigger_testid}"]')
        driver.execute_script("arguments[0].click()", trigger)
        self._pause()
        option = self._wait(wait, lambda d: next(
            (el for el in d.find_elements(By.CSS_SELECTOR, "[data-testid='dropdownactionsheet-item']")
             if el.is_displayed() and option_text in el.text),
            None
        ))
        driver.execute_script("arguments[0].click()", option)
        self._pause()

    def _modal_save(self, driver, wait) -> None:
        save_btn = self._wait(wait, EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="form_modal_save"]')))
        driver.execute_script("arguments[0].click()", save_btn)
        self._pause()

    def _configure_posts(self, driver, wait, s: "PostsSettings") -> None:
        self._open_section(driver, wait, "wall", "form_wall_enabled")
        self._set_toggle(driver, "form_wall_enabled", s.enabled)
        if s.enabled:
            self._select_dropdown(driver, wait, "form_wall_publishing_allowed", s.publishing.value)
            self._set_toggle(driver, "form_wall_sharing_disabled", s.sharing_disabled)
        self._modal_save(driver, wait)

    def _configure_photos(self, driver, wait, s: "PhotosSettings") -> None:
        self._open_section(driver, wait, "photos", "form_photos_toggle")
        self._set_toggle(driver, "form_photos_toggle", s.enabled)
        if s.enabled:
            self._set_radio(driver, s.content_type.value)
            self._set_radio(driver, s.add_allowed.value)
        self._modal_save(driver, wait)

    def _configure_videos(self, driver, wait, s: "VideosSettings") -> None:
        self._open_section(driver, wait, "videos", "form_videos_toggle")
        self._set_toggle(driver, "form_videos_toggle", s.enabled)
        if s.enabled:
            self._set_radio(driver, s.content_type.value)
            self._set_radio(driver, s.add_allowed.value)
        self._modal_save(driver, wait)

    def _configure_topics(self, driver, wait, s: "TopicsSettings") -> None:
        self._open_section(driver, wait, "discussions", "form_discussions_toggle")
        self._set_toggle(driver, "form_discussions_toggle", s.enabled)
        if s.enabled:
            self._set_radio(driver, s.add_allowed.value)
        self._modal_save(driver, wait)

    def _configure_music(self, driver, wait, s: "MusicSettings") -> None:
        self._open_section(driver, wait, "audios", "form_audios_toggle")
        self._set_toggle(driver, "form_audios_toggle", s.enabled)
        if s.enabled:
            self._set_radio(driver, s.content_type.value)
            self._set_radio(driver, s.add_allowed.value)
        self._modal_save(driver, wait)

    def _configure_files(self, driver, wait, s: "FilesSettings") -> None:
        self._open_section(driver, wait, "files", "form_files_toggle")
        self._set_toggle(driver, "form_files_toggle", s.enabled)
        if s.enabled:
            self._set_radio(driver, s.add_allowed.value)
        self._modal_save(driver, wait)

    def _configure_materials(self, driver, wait, s: "MaterialsSettings") -> None:
        self._open_section(driver, wait, "wiki", "form_wiki_toggle")
        self._set_toggle(driver, "form_wiki_toggle", s.enabled)
        if s.enabled:
            self._set_radio(driver, s.add_allowed.value)
        self._modal_save(driver, wait)

    @staticmethod
    def _parse_event_id(url: str) -> int:
        match = re.search(r'(?:event|club)(\d+)', url)
        if not match:
            raise ValueError(f"Could not parse event ID from URL: {url}")
        return int(match.group(1))



