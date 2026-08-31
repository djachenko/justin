"""Общее для тестов, ходящих в живой VK.

Id тестового события читается фикстурой, а не на уровне модуля. Разница принципиальная:
отбор по маркерам происходит **после** импорта, поэтому чтение переменной на импорте
роняло сборку тестов там, где `.env` нет (CI), и никакой `-m` этому помешать не мог.
Фикстура же выполняется только у тех тестов, которые отбор пережили.

Если переменной нет, а живой тест позвали — падаем, так и надо.
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
