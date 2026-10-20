"""Dumps the structure of a VK page — where every new selector starts.

Every one-off exploration script did the same thing: open the page, print testids, inputs
and buttons, then look at them. This is all of them folded into one call.

    VK_TEST_EVENT_ID=<id> python probes/dump_page.py requests
    ... dump_page.py 'https://vk.ru/event{event_id}?act=edit' --inputs

Page names come from PAGES of the contract test; an arbitrary url works too.
"""
import argparse
import os
import sys
import time

from justin.browser.shared.elements import by_css
from justin.browser.vk_browser import VKBrowser
from justin.shared.vk import VK_URL

# Chrome around the content: left menu, header, settings menu — noise in any dump.
CHROME_PREFIXES = ("leftmenu", "rightmenu", "header", "top", "cs_menu", "desktop",
                   "community_settings", "search_top")

KNOWN_PAGES = {
    "edit": VK_URL + "/event{event_id}?act=edit",
    "sections": VK_URL + "/event{event_id}/settings/sections",
    "messages": VK_URL + "/event{event_id}/settings/messages",
    "members": VK_URL + "/event{event_id}/settings/members",
    "requests": VK_URL + "/event{event_id}/settings/requests",
    "extras": VK_URL + "/event{event_id}/settings/extras",
}


def dump_testids(driver) -> None:
    print("=== testids ===")

    for el in driver.find_elements(*by_css("[data-testid]")):
        test_id = el.get_attribute("data-testid")

        if not el.is_displayed() or test_id.startswith(CHROME_PREFIXES):
            continue

        print("   ", test_id, "|", repr(el.text.strip()[:70]), "|", repr(el.get_attribute("value")))


def dump_inputs(driver) -> None:
    """Legacy pages keep values in hidden fields — there are no visible names there."""
    print("=== inputs ===")

    for el in driver.find_elements(*by_css("input, select, textarea")):
        print("   ", el.tag_name, repr(el.get_attribute("name")), repr(el.get_attribute("id")),
              repr(el.get_attribute("value")), _visibility(el),
              repr(el.get_attribute("class"))[:50])


def _visibility(element) -> str:
    if element.is_displayed():
        return "vis"

    return "hid"


def dump_clickables(driver) -> None:
    print("=== buttons / links ===")

    for el in driver.find_elements(*by_css("button, [role='button'], [role='tab'], a")):
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
            driver.find_element(*by_css(args.click)).click()
            time.sleep(2.5)

        print("url:", driver.current_url, "| title:", repr(driver.title))
        dump_testids(driver)

        if args.inputs:
            dump_inputs(driver)

        dump_clickables(driver)


if __name__ == "__main__":
    main()
