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
from justin.browser.shared.run_mode import is_debug

from justin.browser.invite_link.invite_link_schema import InviteLinkSchema
from justin.browser.invite_link.invite_link_settings import InviteLinkSettings
from justin.browser.event_settings.event_settings_schema import EventSettingsSchema
from justin.browser.event_settings.event_settings_settings import EventSettingsSettings
from justin.browser.explorers.settings_explorer import SettingsExplorer
from justin.browser.explorers.event_edit_explorer import EventEditExplorer

from justin.browser.event_creation.event_creation_settings import EventCreationSettings, EventStep1Settings
from justin.browser.event_creation.event_creation_schema import EventCreationSchema


class VKBrowser:
    _BROWSER_DATA_DIR = Path.home() / ".justin" / "browser_data"
    _TIMEOUT = 0.5 * 60
    ERROR_TITLE = "Error"

    def __init__(self, headless: bool | None = None):
        """headless=None — решать по режиму запуска: под отладчиком окно видно.

        Окно нужно там, где на человека рассчитывает сам сценарий: капчу за нас
        никто не решит. Поэтому create_event поднимает браузер видимым.
        """
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={self._BROWSER_DATA_DIR}")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")

        if headless is None:
            headless = not is_debug()

        if headless:
            options.add_argument("--headless=new")

        logging.getLogger("selenium").setLevel(logging.DEBUG)

        self._driver = webdriver.Chrome(options=options)
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
        """После интенсивных прогонов VK отдаёт вместо страницы настроек заглушку с
        заголовком `Error`: формы нет вовсе, и любое ожидание упирается в таймаут.
        Отличить это от «селектор умер» можно только по заголовку.
        """
        return self._driver.title == self.ERROR_TITLE

    def new_wait(self, timeout: float | None = None) -> WebDriverWait:
        """Tests pass a shorter timeout: a throttled VK would otherwise cost half a minute
        per wait, and a suite of them takes minutes to report what one page already said."""
        return WebDriverWait(self._driver, timeout or self._TIMEOUT)

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

        return EventCreationSchema()(settings, self._driver, self.new_wait())

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

    def explore_sections(self, event_id: int, out_dir: Path | None = None) -> None:
        target = out_dir or Path(f"explore_output_{event_id}")

        SettingsExplorer(self._driver, event_id, target).run()

    def explore_edit(self, event_id: int, out_dir: Path | None = None) -> None:
        target = out_dir or Path(f"explore_edit_{event_id}")

        EventEditExplorer(self._driver, event_id, target).run()




