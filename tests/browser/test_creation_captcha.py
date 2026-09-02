"""Капча на создании события и глобальный тормоз пауз. Без браузера."""
import builtins

import pytest

from justin.browser.event_creation import event_creation_schema
from justin.browser.event_creation.event_creation_schema import _wait_for_captcha_if_needed
from justin.browser.shared import pacing


class FakeDriver:
    def __init__(self, url: str):
        self.current_url = url


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(event_creation_schema, "pause", lambda *_, **__: None)


def test_captcha_stops_for_a_human(monkeypatch) -> None:
    """Пока URL остался на странице создания, событие не создано — ждём человека."""
    asked = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": asked.append(prompt))

    _wait_for_captcha_if_needed(FakeDriver("https://vk.com/groups_create/"))

    assert len(asked) == 1


def test_no_captcha_on_event_url(monkeypatch) -> None:
    monkeypatch.setattr(builtins, "input", lambda prompt="": pytest.fail("спросил про капчу зря"))

    _wait_for_captcha_if_needed(FakeDriver("https://vk.com/event239367233"))


def test_pace_zero_skips_sleep(monkeypatch) -> None:
    """PACE = 0 — прогон без задержек; ручкой же можно и замедлить всё разом."""
    slept = []
    monkeypatch.setattr(pacing.time, "sleep", slept.append)

    monkeypatch.setattr(pacing, "PACE", 0)
    pacing.pause(1.0)

    monkeypatch.setattr(pacing, "PACE", 2.0)
    pacing.pause(1.0, jitter=0)

    assert slept == [2.0]
