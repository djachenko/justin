"""Открытие страниц VK в тестах: переиспользование вкладки и пропуск при троттлинге.

Одна вкладка живёт весь модуль, поэтому загруженную страницу можно не перезагружать —
это главная экономия запросов к VK. Опасность одна: тест, который что-то на странице
поменял, оставляет её следующему. Отсюда три входа вместо флагов —

    reading  — только читает, берёт уже открытую;
    editing  — меняет и убрать за собой не может, страница остаётся грязной;
    modal    — открывает модалку и закрывает её на выходе, чем возвращает чистоту.

Чистота снимается на входе и возвращается только если блок дошёл до конца: упавший
тест не доходит до возврата, и страница честно остаётся грязной.
"""
import time
from contextlib import contextmanager

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from justin.browser.shared.elements import Locator, gone
from justin.browser.shared.page import content_rendered
from justin.browser.vk_browser import VKBrowser

WAIT = 10  # секунд: тесту хватает, а на задушенной VK не превращает прогон в минуты
_SHORT = 3

_state: dict = {"url": None, "dirty": True}


def forget_page() -> None:
    """Сбросить память о вкладке — для тестов, которые ходят мимо этого модуля."""
    _state.update(url=None, dirty=True)


@contextmanager
def reading(browser: VKBrowser, url: str):
    yield _load_if_stale(browser, url)


@contextmanager
def editing(browser: VKBrowser, url: str):
    wait = _load_if_stale(browser, url)
    _state["dirty"] = True

    yield wait


@contextmanager
def modal(browser: VKBrowser, url: str, inside_modal: Locator):
    """inside_modal — элемент внутри модалки: по его исчезновению видно, закрылась ли."""
    wait = _load_if_stale(browser, url)
    _state["dirty"] = True

    yield wait

    if _closed_by_escape(browser, inside_modal):
        _state["dirty"] = False


def _load_if_stale(browser: VKBrowser, url: str):
    wait = browser.new_wait(WAIT)

    if _state["url"] == url and not _state["dirty"]:
        return wait

    # Пока страница не загружена, память о вкладке недействительна: если загрузка
    # окажется заглушкой троттлинга, следующий тест не должен принять её за годную.
    forget_page()
    browser.driver.get(url)

    # Заголовок появляется не мгновенно — без ожидания проверка читает пустую строку.
    browser.new_wait(_SHORT).until(lambda d: d.title)

    if browser.is_throttled:
        pytest.skip(f"VK отдаёт {browser.ERROR_TITLE!r}: кулдаун после интенсивных прогонов "
                    f"либо страница действительно пропала — {url}")

    wait.until(content_rendered)
    time.sleep(0.5)

    _state.update(url=url, dirty=False)

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
