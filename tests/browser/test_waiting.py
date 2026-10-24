"""Wait dumps the page on a timeout, and only under a debugger."""
from types import SimpleNamespace

import pytest
from selenium.common.exceptions import TimeoutException

from justin.browser.shared import waiting
from justin.browser.shared.waiting import Wait


@pytest.fixture
def explored(monkeypatch) -> list[object]:
    explored: list[object] = []

    class FakeExplorer:
        def __init__(self, driver) -> None:
            self.driver = driver

        def explore(self) -> None:
            explored.append(self.driver)

    monkeypatch.setattr(waiting, "PageExplorer", FakeExplorer)
    return explored


class TestWait:
    @pytest.mark.parametrize("debug,dumps", [
        (True, 1),
        (False, 0),
    ], ids=["debugger", "plain_run"])
    def test_timeout_dumps_under_debugger_only(self, monkeypatch, explored: list[object],
                                               debug: bool, dumps: int) -> None:
        monkeypatch.setattr(waiting, "is_debug", lambda: debug)
        driver = SimpleNamespace()

        with pytest.raises(TimeoutException):
            Wait(driver, timeout=0.05, poll_frequency=0.01).until(lambda _: False)

        assert explored == [driver] * dumps

    def test_success_dumps_nothing(self, monkeypatch, explored: list[object]) -> None:
        monkeypatch.setattr(waiting, "is_debug", lambda: True)

        result = Wait(SimpleNamespace(), timeout=0.05, poll_frequency=0.01).until(lambda _: "ready")

        assert result == "ready"
        assert explored == []
