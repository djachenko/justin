"""VKBrowser without Chrome: launch options, teardown and wiring into the schemas."""
import logging
import signal
from datetime import datetime
from types import SimpleNamespace

import pytest

from justin.browser import vk_browser
from justin.browser.shared.waiting import Wait
from justin.browser.vk_browser import VKBrowser


class FakeChrome:
    def __init__(self, options) -> None:
        self.options = options
        self.capabilities = {
            "browserVersion": "152",
        }


@pytest.fixture
def launched(monkeypatch):
    """Builds VKBrowser on a fake Chrome; the selenium log level it sets is put back."""
    monkeypatch.setattr(vk_browser.webdriver, "Chrome", FakeChrome)
    monkeypatch.setattr(VKBrowser, "_spawned_browser_pids", lambda self: [])

    selenium_logger = logging.getLogger("selenium")
    level = selenium_logger.level

    yield

    selenium_logger.setLevel(level)


def _bare_browser() -> VKBrowser:
    return VKBrowser.__new__(VKBrowser)


@pytest.mark.usefixtures("launched")
class TestHeadless:
    @pytest.mark.parametrize("headless,debug,expected", [
        (None, True, False),
        (None, False, True),
        (True, True, True),
        (False, False, False),
    ], ids=["debugger_shows_window", "plain_run_is_headless", "explicit_headless", "explicit_window"])
    def test_choice(self, monkeypatch, headless: bool | None, debug: bool, expected: bool) -> None:
        monkeypatch.setattr(vk_browser, "is_debug", lambda: debug)

        browser = VKBrowser(headless=headless)

        assert ("--headless=new" in browser.driver.options.arguments) == expected


class TestSpawnedBrowserPids:
    def test_children_of_chromedriver(self, monkeypatch) -> None:
        asked: list[list[str]] = []

        def run(args, **_):
            asked.append(args)
            return SimpleNamespace(stdout="12\n34\n")

        monkeypatch.setattr(vk_browser.subprocess, "run", run)

        browser = _bare_browser()
        browser._driver = SimpleNamespace(service=SimpleNamespace(process=SimpleNamespace(pid=7)))

        assert browser._spawned_browser_pids() == [12, 34]
        assert asked == [["pgrep", "-P", "7"]]


class TestExit:
    def test_leftovers_are_killed_when_quit_fails(self, monkeypatch) -> None:
        """A dead chromedriver fails quit() — exactly when Chrome is left orphaned."""
        killed: list[bool] = []

        def quit_() -> None:
            raise RuntimeError("chromedriver is gone")

        browser = _bare_browser()
        browser._driver = SimpleNamespace(quit=quit_)
        monkeypatch.setattr(browser, "_kill_leftovers", lambda: killed.append(True))

        with pytest.raises(RuntimeError):
            browser.__exit__(None, None, None)

        assert killed == [True]


class TestKillLeftoversEscalation:
    @pytest.fixture
    def sent(self, monkeypatch) -> list[tuple[int, int]]:
        sent: list[tuple[int, int]] = []
        monkeypatch.setattr(VKBrowser, "_signal", staticmethod(lambda pid, sig: sent.append((pid, sig))))
        monkeypatch.setattr(vk_browser.time, "sleep", lambda _: None)
        return sent

    def test_survivor_of_sigterm_gets_sigkill(self, monkeypatch, sent: list[tuple[int, int]]) -> None:
        monkeypatch.setattr(VKBrowser, "_is_alive", staticmethod(lambda pid: True))

        browser = _bare_browser()
        browser._browser_pids = [11]

        browser._kill_leftovers()

        assert sent == [(11, signal.SIGTERM), (11, signal.SIGKILL)]

    def test_sigterm_is_enough(self, monkeypatch, sent: list[tuple[int, int]]) -> None:
        monkeypatch.setattr(VKBrowser, "_is_alive", staticmethod(lambda pid: not sent))

        browser = _bare_browser()
        browser._browser_pids = [11]

        browser._kill_leftovers()

        assert sent == [(11, signal.SIGTERM)]

    def test_only_live_processes_are_signalled(self, monkeypatch, sent: list[tuple[int, int]]) -> None:
        monkeypatch.setattr(VKBrowser, "_is_alive", staticmethod(lambda pid: pid == 22 and not sent))

        browser = _bare_browser()
        browser._browser_pids = [11, 22]

        browser._kill_leftovers()

        assert sent == [(22, signal.SIGTERM)]


class TestNewWait:
    @pytest.mark.parametrize("timeout,expected", [
        (None, 30),
        (0, 0),
        (5, 5),
    ], ids=["default", "zero_is_honoured", "explicit"])
    def test_timeout(self, timeout: float | None, expected: float) -> None:
        browser = _bare_browser()
        browser._driver = SimpleNamespace()

        wait = browser.new_wait(timeout)

        assert isinstance(wait, Wait)
        assert wait._timeout == expected


class TestCreateEvent:
    def test_arguments_reach_the_wizard(self, monkeypatch) -> None:
        calls: list[dict] = []

        class FakeSchema:
            def __init__(self, step3) -> None:
                self.step3 = step3

            def __call__(self, settings, driver, wait) -> int:
                calls.append({
                    "settings": settings,
                    "headless": self.step3.headless,
                    "driver": driver,
                    "wait": wait,
                })
                return 111

        monkeypatch.setattr(vk_browser, "EventCreationSchema", FakeSchema)

        browser = _bare_browser()
        browser._driver = SimpleNamespace()
        browser._headless = False

        event_id = browser.create_event(
            title="Party",
            start_dt=datetime(2026, 3, 7, 12),
            end_dt=datetime(2026, 3, 7, 16),
            organiser_id=-42,
            is_closed=False,
        )

        [call] = calls
        step1 = call["settings"].step1

        assert event_id == 111
        assert (step1.title, step1.start_dt, step1.end_dt, step1.organiser_id, step1.is_closed) == \
            ("Party", datetime(2026, 3, 7, 12), datetime(2026, 3, 7, 16), -42, False)
        assert call["headless"] is False
        assert call["driver"] is browser._driver
        assert isinstance(call["wait"], Wait)
