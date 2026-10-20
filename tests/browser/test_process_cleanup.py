"""Killing Chrome that outlived chromedriver. No browser — plain processes."""
import subprocess
import time

from justin.browser.vk_browser import VKBrowser


def _dead_pid() -> int:
    process = subprocess.Popen(["sleep", "30"])
    process.kill()
    process.wait()

    return process.pid


class TestIsAlive:
    def test_running_process_is_alive(self) -> None:
        process = subprocess.Popen(["sleep", "30"])

        try:
            assert VKBrowser._is_alive(process.pid)
        finally:
            process.kill()
            process.wait()

        assert not VKBrowser._is_alive(process.pid)


class TestKillLeftovers:
    def test_leftover_process_is_killed(self) -> None:
        process = subprocess.Popen(["sleep", "30"])

        browser = VKBrowser.__new__(VKBrowser)
        browser._browser_pids = [process.pid]

        browser._kill_leftovers()

        process.wait(timeout=5)

        assert not VKBrowser._is_alive(process.pid)

    def test_process_that_died_meanwhile_is_not_an_error(self, monkeypatch) -> None:
        monkeypatch.setattr(VKBrowser, "_is_alive", staticmethod(lambda pid: True))
        monkeypatch.setattr(time, "sleep", lambda _: None)

        browser = VKBrowser.__new__(VKBrowser)
        browser._browser_pids = [_dead_pid()]

        browser._kill_leftovers()
