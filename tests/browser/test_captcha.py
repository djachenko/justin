import builtins

import pytest

from justin.browser.shared import captcha
from justin.browser.shared.captcha import CaptchaError, wait_for_captcha_if_needed
from justin.shared.vk import VK_URL

STUCK_ON = "/groups_create"


class FakeDriver:
    def __init__(self, url: str) -> None:
        self.current_url = url


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(captcha, "pause", lambda *_, **__: None)


class TestWithAWindow:
    def test_captcha_stops_for_a_human(self, monkeypatch) -> None:
        asked = []
        monkeypatch.setattr(builtins, "input", lambda prompt="": asked.append(prompt))

        wait_for_captcha_if_needed(FakeDriver(f"{VK_URL}/groups_create/"), STUCK_ON, headless=False)

        assert len(asked) == 1

    def test_no_captcha_when_action_went_through(self, monkeypatch) -> None:
        monkeypatch.setattr(builtins, "input",
                            lambda prompt="": pytest.fail("asked about a captcha for nothing"))

        wait_for_captcha_if_needed(FakeDriver(f"{VK_URL}/event111111111"), STUCK_ON, headless=False)


class TestHeadless:
    def test_captcha_raises(self, monkeypatch) -> None:
        monkeypatch.setattr(builtins, "input",
                            lambda prompt="": pytest.fail("waited for a human with no window"))

        driver = FakeDriver(f"{VK_URL}/groups_create/")

        with pytest.raises(CaptchaError, match="groups_create"):
            wait_for_captcha_if_needed(driver, STUCK_ON, headless=True)

    def test_no_captcha_passes(self) -> None:
        driver = FakeDriver(f"{VK_URL}/event1")

        wait_for_captcha_if_needed(driver, STUCK_ON, headless=True)
