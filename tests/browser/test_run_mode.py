"""Режим запуска: под отладчиком браузер видим и дампит страницу, в проде — нет."""
import sys

from justin.browser.shared.run_mode import is_debug


def test_debug_detected_by_tracer(monkeypatch) -> None:
    monkeypatch.setattr(sys, "gettrace", lambda: object())

    assert is_debug()


def test_debug_detected_by_pydevd(monkeypatch) -> None:
    """PyCharm грузит pydevd даже там, где трассировщик не выставлен."""
    monkeypatch.setattr(sys, "gettrace", lambda: None)
    monkeypatch.setitem(sys.modules, "pydevd", object())

    assert is_debug()


def test_plain_run_is_not_debug(monkeypatch) -> None:
    monkeypatch.setattr(sys, "gettrace", lambda: None)
    monkeypatch.delitem(sys.modules, "pydevd", raising=False)

    assert not is_debug()
