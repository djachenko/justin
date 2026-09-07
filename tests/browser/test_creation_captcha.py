"""Капча и глобальный тормоз пауз. Без браузера."""
import builtins

import pytest

from justin.browser.shared import captcha, pacing
from justin.browser.shared.captcha import wait_for_captcha_if_needed

STUCK_ON = "/groups_create"


class FakeDriver:
    def __init__(self, url: str):
        self.current_url = url


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(captcha, "pause", lambda *_, **__: None)


def test_captcha_stops_for_a_human(monkeypatch) -> None:
    """Пока адрес остался тем же, действие не прошло — ждём человека."""
    asked = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": asked.append(prompt))

    wait_for_captcha_if_needed(FakeDriver("https://vk.com/groups_create/"), STUCK_ON)

    assert len(asked) == 1


def test_no_captcha_when_action_went_through(monkeypatch) -> None:
    monkeypatch.setattr(builtins, "input", lambda prompt="": pytest.fail("спросил про капчу зря"))

    wait_for_captcha_if_needed(FakeDriver("https://vk.com/event239367233"), STUCK_ON)


def test_pace_zero_skips_sleep(monkeypatch) -> None:
    """PACE = 0 — прогон без задержек; ручкой же можно и замедлить всё разом."""
    slept = []
    monkeypatch.setattr(pacing.time, "sleep", slept.append)

    monkeypatch.setattr(pacing, "PACE", 0)
    pacing.pause(1.0)

    monkeypatch.setattr(pacing, "PACE", 2.0)
    pacing.pause(1.0, spread=0)

    assert slept == [2.0]


def test_pauses_are_not_identical() -> None:
    """Одинаковые по смыслу паузы всё равно разной длины."""
    drawn = [pacing.varied(1.0) for _ in range(5)]

    assert len(set(drawn)) == len(drawn)


def test_deviation_scales_with_the_value() -> None:
    """Половина от переданного: 0.4 отклоняется на 0.2, 2.0 — на 1.0."""
    short = [pacing.varied(0.4, spread=0.5) for _ in range(200)]
    long = [pacing.varied(2.0, spread=0.5) for _ in range(200)]

    assert all(0.2 <= value <= 0.6 for value in short)
    assert all(1.0 <= value <= 3.0 for value in long)


def test_zero_spread_keeps_the_value() -> None:
    assert pacing.varied(0.3, spread=0) == 0.3
