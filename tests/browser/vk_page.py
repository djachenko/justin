"""Opening VK pages in tests: tab reuse and skipping while throttled.

One tab lives for the whole module, so a loaded page need not be reloaded — that is the
main saving on requests to VK. The one danger: a test that changed something on the page
leaves it to the next one. Hence three entry points instead of flags —

    reading  — reads only, takes the page already open;
    editing  — changes it and cannot undo that, the page stays dirty;
    modal    — opens a modal and closes it on the way out, which restores cleanliness.

Cleanliness is dropped on entry and restored only if the block reached its end: a failing
test never reaches the restore, and the page honestly stays dirty.
"""
import time
from contextlib import contextmanager
from dataclasses import dataclass

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from justin.browser.shared.elements import Locator, gone
from justin.browser.shared.page import content_rendered
from justin.browser.vk_browser import VKBrowser

WAIT = 10  # seconds: enough for a test, and a throttled VK does not stretch the run
_SHORT = 3

@dataclass
class _Tab:
    url: str | None = None
    dirty: bool = True


_tab = _Tab()


def forget_page() -> None:
    """Forget the tab — for tests that open pages past this module."""
    _tab.url = None
    _tab.dirty = True


@contextmanager
def reading(browser: VKBrowser, url: str):
    yield _load_if_stale(browser, url)


@contextmanager
def editing(browser: VKBrowser, url: str):
    wait = _load_if_stale(browser, url)
    _tab.dirty = True

    yield wait


@contextmanager
def modal(browser: VKBrowser, url: str, inside_modal: Locator):
    """inside_modal is an element inside the modal: its disappearance means it closed."""
    wait = _load_if_stale(browser, url)
    _tab.dirty = True

    yield wait

    if _closed_by_escape(browser, inside_modal):
        _tab.dirty = False


def _load_if_stale(browser: VKBrowser, url: str):
    wait = browser.new_wait(WAIT)

    if _tab.url == url and not _tab.dirty:
        return wait

    # Until the page is loaded the memory of the tab is invalid: if the load turns out to
    # be a throttling stub, the next test must not take it for a good page.
    forget_page()
    browser.driver.get(url)

    # The title does not appear at once — without a wait the check reads an empty string.
    browser.new_wait(_SHORT).until(lambda d: d.title)

    if browser.is_throttled:
        pytest.skip(f"VK serves {browser.ERROR_TITLE!r}: a cooldown after heavy runs, "
                    f"or the page is really gone — {url}")

    wait.until(content_rendered)
    time.sleep(0.5)

    _tab.url = url
    _tab.dirty = False

    return wait


def _closed_by_escape(browser: VKBrowser, inside_modal: Locator) -> bool:
    ActionChains(browser.driver) \
        .send_keys(Keys.ESCAPE) \
        .perform()

    try:
        gone(browser.new_wait(_SHORT), inside_modal)
    except TimeoutException:
        return False

    return True
