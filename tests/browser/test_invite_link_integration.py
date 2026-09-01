"""
Тесты, которые реально меняют событие: создают инвайт-ссылку и переключают доступ.
Оба помечены destructive — ссылка остаётся в списке, доступ возвращается на место.

Запуск: pytest -m destructive tests/browser/test_invite_link_integration.py
"""
import time

import pytest
from selenium.webdriver.common.by import By

from justin.browser.event_setup.schema import _ACCESS_VALUE, _CLOSED, _OPEN, _set_access
from justin.browser.invite_link.schema import _LINK_PREFIX
from justin.browser.shared.save_button import find_save_buttons
from justin.browser.vk_browser import VKBrowser
from tests.browser.vk_page import editing


def _edit_url(event_id: int) -> str:
    return f"https://vk.com/event{event_id}?act=edit"


@pytest.mark.destructive
def test_create_invite_link(browser: VKBrowser, event_id: int) -> None:
    link = browser.create_invite_link(event_id)

    assert _LINK_PREFIX in link, f"это не инвайт-ссылка: {link!r}"


def _open_edit(browser: VKBrowser, event_id: int):
    """Через тот же вход, что и контрактные тесты: он умеет распознавать кулдаун VK."""
    with editing(browser, _edit_url(event_id)) as wait:
        wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "[id='group_edit_name']"))
        time.sleep(1.0)

        return wait


def _saved_access(browser: VKBrowser) -> int:
    return int(browser.driver.find_element(
        By.CSS_SELECTOR, _ACCESS_VALUE).get_attribute("value"))


@pytest.mark.destructive
def test_access_survives_save(browser: VKBrowser, event_id: int) -> None:
    """Доступ проверяется только переключением: прочитать нужное значение мало —
    оно могло стоять и до нас. Именно так пряталось молчаливое игнорирование записи."""
    wait = _open_edit(browser, event_id)
    original = _saved_access(browser)

    try:
        for expected in (_OPEN, _CLOSED):
            _set_access(browser.driver, wait, is_closed=expected == _CLOSED)
            browser.driver.execute_script(
                "arguments[0].click()", next(iter(find_save_buttons(browser.driver))))
            time.sleep(3)

            wait = _open_edit(browser, event_id)

            assert _saved_access(browser) == expected, \
                f"доступ не сохранился: ожидали {expected}"
    finally:
        _set_access(browser.driver, wait, is_closed=original == _CLOSED)
        browser.driver.execute_script(
            "arguments[0].click()", next(iter(find_save_buttons(browser.driver))))
        time.sleep(3)
