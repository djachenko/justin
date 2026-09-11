"""Добивание Chrome, пережившего chromedriver. Без браузера — на обычных процессах."""
import subprocess
import time

from justin.browser.vk_browser import VKBrowser


def _dead_pid() -> int:
    process = subprocess.Popen(["sleep", "30"])
    process.kill()
    process.wait()

    return process.pid


def test_is_alive() -> None:
    process = subprocess.Popen(["sleep", "30"])

    try:
        assert VKBrowser._is_alive(process.pid)
    finally:
        process.kill()
        process.wait()

    assert not VKBrowser._is_alive(process.pid)


def test_kill_leftovers_kills_process() -> None:
    process = subprocess.Popen(["sleep", "30"])

    browser = VKBrowser.__new__(VKBrowser)
    browser._browser_pids = [process.pid]
    browser._kill_leftovers()

    process.wait(timeout=5)

    assert not VKBrowser._is_alive(process.pid)


def test_kill_leftovers_survives_process_that_died_meanwhile(monkeypatch) -> None:
    """Между проверкой и сигналом процесс может успеть выйти сам — это не ошибка."""
    monkeypatch.setattr(VKBrowser, "_is_alive", staticmethod(lambda pid: True))
    monkeypatch.setattr(time, "sleep", lambda _: None)

    browser = VKBrowser.__new__(VKBrowser)
    browser._browser_pids = [_dead_pid()]
    browser._kill_leftovers()
