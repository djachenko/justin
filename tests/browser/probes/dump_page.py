"""Дампер структуры страницы VK — с него начинается любой новый селектор.

Все разовые скрипты разведки делали одно и то же: открыть страницу, вывести
testid'ы, инпуты и кнопки, посмотреть глазами. Это они, сведённые в один вызов.

    VK_TEST_EVENT_ID=<id> python tests/browser/probes/dump_page.py requests
    ... dump_page.py 'https://vk.com/event{event_id}?act=edit' --inputs

Имена страниц берутся из PAGES контрактного теста, произвольный URL — тоже можно.
"""
import argparse
import os
import sys
import time

from selenium.webdriver.common.by import By

from justin.browser.vk_browser import VKBrowser

# Пункты хрома вокруг контента: левое меню, шапка, меню настроек — шум в любом дампе.
CHROME_PREFIXES = ("leftmenu", "rightmenu", "header", "top", "cs_menu", "desktop",
                   "community_settings", "search_top")

KNOWN_PAGES = {
    "edit": "https://vk.com/event{event_id}?act=edit",
    "sections": "https://vk.com/event{event_id}/settings/sections",
    "messages": "https://vk.com/event{event_id}/settings/messages",
    "members": "https://vk.com/event{event_id}/settings/members",
    "requests": "https://vk.com/event{event_id}/settings/requests",
    "extras": "https://vk.com/event{event_id}/settings/extras",
}


def dump_testids(driver) -> None:
    print("=== testids ===")

    for el in driver.find_elements(By.CSS_SELECTOR, "[data-testid]"):
        test_id = el.get_attribute("data-testid")

        if not el.is_displayed() or test_id.startswith(CHROME_PREFIXES):
            continue

        print("   ", test_id, "|", repr(el.text.strip()[:70]), "|", repr(el.get_attribute("value")))


def dump_inputs(driver) -> None:
    """Legacy-страницы держат значения в скрытых полях — видимых имён там нет."""
    print("=== inputs ===")

    for el in driver.find_elements(By.CSS_SELECTOR, "input, select, textarea"):
        print("   ", el.tag_name, repr(el.get_attribute("name")), repr(el.get_attribute("id")),
              repr(el.get_attribute("value")), "vis" if el.is_displayed() else "hid",
              repr(el.get_attribute("class"))[:50])


def dump_clickables(driver) -> None:
    print("=== buttons / links ===")

    for el in driver.find_elements(By.CSS_SELECTOR, "button, [role='button'], [role='tab'], a"):
        text = el.text.strip()

        if not el.is_displayed() or not text or len(text) > 40:
            continue

        print("   ", el.tag_name, repr(text), "|", el.get_attribute("data-testid"),
              "|", (el.get_attribute("href") or "")[-60:])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("page", help=f"one of {sorted(KNOWN_PAGES)} or a url template")
    parser.add_argument("--click", help="css of an element to click before dumping")
    parser.add_argument("--inputs", action="store_true", help="dump raw inputs too")
    parser.add_argument("--delay", type=float, default=6.0)
    args = parser.parse_args()

    event_id = os.environ.get("VK_TEST_EVENT_ID")

    if event_id is None:
        sys.exit("VK_TEST_EVENT_ID is not set")

    url = KNOWN_PAGES.get(args.page, args.page).format(event_id=event_id)

    with VKBrowser() as browser:
        driver = browser.driver
        driver.get(url)
        time.sleep(args.delay)

        if args.click:
            driver.find_element(By.CSS_SELECTOR, args.click).click()
            time.sleep(2.5)

        print("url:", driver.current_url, "| title:", repr(driver.title))
        dump_testids(driver)

        if args.inputs:
            dump_inputs(driver)

        dump_clickables(driver)


if __name__ == "__main__":
    main()
