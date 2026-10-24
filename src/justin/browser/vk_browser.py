import logging
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.sections.section_settings import SectionsConfig
from justin.shared.run_mode import is_debug
from justin.browser.shared.waiting import Wait

from justin.browser.invite_link.invite_link_schema import InviteLinkSchema
from justin.browser.invite_link.invite_link_settings import InviteLinkSettings
from justin.browser.event_settings.event_settings_schema import EventSettingsSchema
from justin.browser.event_settings.event_settings_settings import EventSettingsSettings

from justin.browser.event_creation.event_creation_settings import EventCreationSettings, EventStep1Settings
from justin.browser.event_creation.event_creation_schema import EventCreationSchema, EventStep3Schema


class VKBrowser:
    _BROWSER_DATA_DIR = Path.home() / ".justin" / "browser_data"
    _BROWSER_VERSION = "152"
    _WINDOW_SIZE = "1440,900"
    _TIMEOUT = 0.5 * 60
    ERROR_TITLE = "Error"

    def __init__(self, headless: bool | None = None):
        """headless=None — decide by run mode: under a debugger the window is shown.

        A window is needed where the scenario itself counts on a human: nobody will solve
        a captcha for us. Such a caller passes headless=False, as setup-event --create does.
        """
        options = webdriver.ChromeOptions()
        options.browser_version = self._BROWSER_VERSION
        options.add_argument(f"--user-data-dir={self._BROWSER_DATA_DIR}")
        options.add_argument(f"--window-size={self._WINDOW_SIZE}")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")

        if headless is None:
            headless = not is_debug()

        if headless:
            options.add_argument("--headless=new")

        self._headless = headless

        logging.getLogger("selenium").setLevel(logging.DEBUG)

        print(f"Starting Chrome {self._BROWSER_VERSION}: first run downloads it, ~190 MB...")
        self._driver = webdriver.Chrome(options=options)
        print(f"Chrome {self._driver.capabilities['browserVersion']} started.")
        self._browser_pids = self._spawned_browser_pids()

    def _spawned_browser_pids(self) -> list[int]:
        """Chrome processes chromedriver just started — they outlive it if it dies."""
        driver_pid = self._driver.service.process.pid
        found = subprocess.run(["pgrep", "-P", str(driver_pid)],
                               capture_output=True, text=True).stdout

        return [int(line) for line in found.split()]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        try:
            self._driver.quit()
        finally:
            self._kill_leftovers()

    def _kill_leftovers(self) -> None:
        """quit() only asks chromedriver to close Chrome — a dead driver leaves it orphaned."""
        for signal_number in (signal.SIGTERM, signal.SIGKILL):
            alive = [pid for pid in self._browser_pids if self._is_alive(pid)]

            if not alive:
                return

            for pid in alive:
                self._signal(pid, signal_number)

            time.sleep(2)

    @staticmethod
    def _signal(pid: int, signal_number: int) -> None:
        """The process can exit between the liveness check and the signal — that is a win."""
        try:
            os.kill(pid, signal_number)
        except ProcessLookupError:
            pass

    @staticmethod
    def _is_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except OSError:
            return False

        return True

    @property
    def driver(self) -> webdriver.Chrome:
        return self._driver

    @property
    def is_throttled(self) -> bool:
        """After heavy runs VK serves a stub titled `Error` instead of the settings page:
        there is no form at all, and every wait runs into its timeout. The title is the
        only way to tell this apart from "the selector died".
        """
        return self._driver.title == self.ERROR_TITLE

    def new_wait(self, timeout: float | None = None) -> WebDriverWait:
        """Tests pass a shorter timeout: a throttled VK would otherwise cost half a minute
        per wait, and a suite of them takes minutes to report what one page already said."""
        if timeout is None:
            timeout = self._TIMEOUT

        return Wait(self._driver, timeout)

    def create_event(
        self,
        title: str,
        start_dt: datetime,
        end_dt: datetime | None = None,
        organiser_id: int | None = None,
        is_closed: bool = True,
    ) -> int:
        settings = EventCreationSettings(
            step1=EventStep1Settings(
                title=title,
                start_dt=start_dt,
                is_closed=is_closed,
                end_dt=end_dt,
                organiser_id=organiser_id,
            ),
        )

        schema = EventCreationSchema(step3=EventStep3Schema(headless=self._headless))

        return schema(settings, self._driver, self.new_wait())

    def apply_settings(self, event_id: int, settings: EventSettingsSettings) -> None:
        EventSettingsSchema()(event_id, settings, self._driver, self.new_wait())

    def set_sections(self, event_id: int, config: SectionsConfig | None = None) -> None:
        if config is None:
            config = SectionsConfig()

        self.apply_settings(event_id, EventSettingsSettings(sections=config))

    def create_invite_link(self, event_id: int, settings: InviteLinkSettings | None = None) -> str:
        if settings is None:
            settings = InviteLinkSettings()

        return InviteLinkSchema()(event_id, settings, self._driver, self.new_wait())
