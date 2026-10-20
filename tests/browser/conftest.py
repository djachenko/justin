"""Shared by the tests that go to live VK.

The test event id is read by a fixture, not at module level. Markers are applied after
import, so reading the variable on import broke collection wherever there is no .env
(CI), and no -m could prevent that. A fixture runs only for tests that survived selection.

A live test called without the variable fails — as it should.
"""
import os

import pytest

from justin.browser.vk_browser import VKBrowser
from tests.browser.vk_page import forget_page

EVENT_ID_VAR = "VK_TEST_EVENT_ID"


@pytest.fixture(scope="module")
def event_id() -> int:
    return int(os.environ[EVENT_ID_VAR])


@pytest.fixture(scope="module")
def browser():
    forget_page()

    with VKBrowser() as opened:
        yield opened
