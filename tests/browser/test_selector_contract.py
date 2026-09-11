"""
Контракт селекторов: проверяет, что элементы, на которые опираются схемы,
всё ещё есть на живых страницах VK. Ничего не меняет — только читает.

Падение теста = VK переписал страницу, смотри имя теста и селектор.

Запуск: pytest -m integration tests/browser/test_selector_contract.py
(по умолчанию живые тесты отобраны маркером — см. addopts в pyproject.toml)
"""
from datetime import datetime

import pytest
from selenium.common.exceptions import TimeoutException

from justin.browser.event_creation.event_creation_schema import EventCreationSchema
from justin.browser.event_settings.event_settings_schema import _MESSAGES_OFF, _MESSAGES_ON, _MESSAGES_SELECT
from justin.browser.event_setup.event_setup_schema import (
    _ACCESS, _CITY, _SUBJECT, _fill_date_field, _visible_selectors,
)
from justin.browser.shared.custom_select import option_by_value
from justin.browser.shared.elements import by_css, by_testid, by_xpath, clickable, found, present, visible
from justin.browser.invite_link.invite_link_schema import (
    _CREATE_LINK_BUTTON, _LIFETIME, _MODAL, _MODAL_CREATE, _SELECT_HOLDER, _USES,
)
from justin.browser.invite_link.invite_link_settings import LinkLifetime, LinkUses
from justin.browser.shared.save_button import find_save_buttons
from justin.browser.sections.section_schema import (
    FilesSchema, MaterialsSchema, MusicSchema,
    PhotosSchema, PostsSchema, TopicsSchema, VideosSchema,
)
from justin.browser.vk_browser import VKBrowser
from tests.browser.vk_page import editing, modal, reading

PAGES = {
    "setup": (
        "https://vk.com/event{event_id}?act=edit",
        [
            "[id='group_edit_name']",
            "[id='group_edit_desc']",
            "[id='group_website']",
            "[id='group_edit_phone']",
            "[id='event_mail']",
        ],
    ),
    "sections": (
        "https://vk.com/event{event_id}/settings/sections",
        ["[data-testid='list_enabled']"],
    ),
    "cta": (
        "https://vk.com/event{event_id}/settings/cta",
        ["[data-testid='groups_edit_header_switch_label_cta'] input[type='checkbox']"],
    ),
    "messages": (
        "https://vk.com/event{event_id}/settings/messages",
        [
            "input[data-testid='settings_messages_enabled']",
            "select[data-testid='settings_messages_enabled']",
            "textarea[data-testid='settings_messages_first_message']",
        ],
    ),
    "addresses": (
        "https://vk.com/event{event_id}?act=addresses",
        ["[data-testid='groups_edit_g_addresses']"],
    ),
    "invites": (
        "https://vk.com/event{event_id}/settings/requests",
        [
            "[data-testid='settings-invitations-create-link-button']",
            "[data-testid='settings-invitations-by-link']",
        ],
    ),
    "extras": (
        "https://vk.com/event{event_id}/settings/extras",
        [
            "[data-testid='photo_recognize_enabled']",
            "[data-testid='clips_co_ownership_enabled']",
            "[data-testid='stories_replies_enabled']",
            "[data-testid='show_in_left_menu']",
        ],
    ),
}

_NAME_FIELD = by_css("[id='group_edit_name']")

SECTIONS = [
    PostsSchema("wall"),
    PhotosSchema("photos"),
    VideosSchema("videos"),
    TopicsSchema("discussions"),
    MusicSchema("audios"),
    FilesSchema("files"),
    MaterialsSchema("wiki"),
]



@pytest.mark.integration
@pytest.mark.parametrize("page", PAGES)
def test_page_selectors_present(browser: VKBrowser, event_id: int, page: str) -> None:
    url_tmpl, selectors = PAGES[page]
    missing: list[str] = []

    def all_present(driver) -> bool:
        missing[:] = [s for s in selectors if not driver.find_elements(*by_css(s))]
        return not missing

    with reading(browser, url_tmpl.format(event_id=event_id)) as wait:
        try:
            wait.until(all_present)
        except TimeoutException:
            pass

    assert not missing, f"[{page}] пропали селекторы: {missing}"


@pytest.mark.integration
def test_messages_select_values(browser: VKBrowser, event_id: int) -> None:
    """Схема выбирает сообщения по значению, а не по подписи — значения должны быть на месте."""
    with reading(browser, f"https://vk.com/event{event_id}/settings/messages"):
        native = browser.driver.find_element(*by_css(f"select[data-testid='{_MESSAGES_SELECT}']"))
        values = [option.get_attribute("value")
                  for option in native.find_elements(*by_css("option"))]

    assert sorted(values) == sorted([_MESSAGES_OFF, _MESSAGES_ON]), f"значения селекта: {values}"
    assert native.get_attribute("value") in values


@pytest.mark.integration
@pytest.mark.parametrize("position,hidden", [
    (_SUBJECT, "group_category_0"),
    (_CITY, "sel_groups_edit_city"),
], ids=["category", "city"])
def test_selector_positions(browser: VKBrowser, event_id: int, position: int, hidden: str) -> None:
    """Категория и город берутся по номеру среди одинаковых виджетов — проверяем,
    что по этому номеру лежит именно тот виджет, к которому привязано скрытое поле."""
    with reading(browser, PAGES["setup"][0].format(event_id=event_id)) as wait:
        present(wait, _NAME_FIELD)

        widget = browser.driver.find_element(*by_css(f"input[name='{hidden}']")).find_element(
            *by_xpath("ancestor::*[contains(@class, 'selector')][1]"))

        at_position = _visible_selectors(browser.driver)[position]

    assert at_position in widget.find_elements(*by_css(".selector_input")), \
        f"на позиции {position} не виджет поля {hidden!r}"


@pytest.mark.integration
@pytest.mark.parametrize("page", ["setup", "messages", "addresses"])
def test_save_button_present(browser: VKBrowser, event_id: int, page: str) -> None:
    """Страницы, которые схемы сохраняют явной кнопкой."""
    url_tmpl, _ = PAGES[page]

    with reading(browser, url_tmpl.format(event_id=event_id)) as wait:
        wait.until(lambda d: find_save_buttons(d))


@pytest.mark.integration
@pytest.mark.parametrize("section", SECTIONS, ids=lambda s: s.test_id)
def test_section_modal_selectors(browser: VKBrowser, event_id: int, section) -> None:
    """Открывает модалку секции и проверяет тоггл и кнопку сохранения. Не сохраняет."""
    toggle = by_testid(section.enabled.test_id)
    url = f"https://vk.com/event{event_id}/settings/sections"

    with modal(browser, url, inside_modal=toggle) as wait:
        item = clickable(wait, by_testid(section.test_id))

        browser.driver.execute_script("arguments[0].click()", item)

        present(wait, toggle)
        present(wait, by_testid("form_modal_save"))


@pytest.mark.integration
@pytest.mark.parametrize("dt", [
    datetime(2027, 2, 3, 9, 5),      # другой год вперёд
    datetime(2025, 12, 28, 20, 0),   # год назад
])
def test_date_field_is_filled(browser: VKBrowser, event_id: int, dt: datetime) -> None:
    """Дата и время проставляются через datepicker. Не сохраняет — перезагрузка всё откатит."""
    with editing(browser, PAGES["setup"][0].format(event_id=event_id)) as wait:
        present(wait, _NAME_FIELD)

        _fill_date_field(browser.driver, wait, "group_start_date_date_input", dt)

        shown = browser.driver.find_element(
            *by_css("[id='group_start_date_date_input']")).get_attribute("value")

    assert str(dt.day) in shown and str(dt.year) in shown, f"поле показывает {shown!r}"


@pytest.mark.integration
def test_access_dropdown_has_both_options(browser: VKBrowser, event_id: int) -> None:
    """Доступ выбирается по позиции: 0 — открытое, 1 — закрытое. Не сохраняет."""
    with editing(browser, PAGES["setup"][0].format(event_id=event_id)) as wait:
        present(wait, _NAME_FIELD)

        browser.driver.find_element(*by_css(_ACCESS)).click()

        items = found(wait, lambda d: [el for el in d.find_elements(
            *by_css(f"{_ACCESS} .idd_item")) if el.is_displayed()] or None)

    assert len(items) == 2, f"в выпадашке доступа {len(items)} пунктов: {[i.text for i in items]}"


@pytest.mark.integration
@pytest.mark.parametrize("position,options", [
    (_LIFETIME, list(LinkLifetime)),
    (_USES, list(LinkUses)),
], ids=["lifetime", "uses"])
def test_invite_modal_options(browser: VKBrowser, event_id: int, position: int, options: list) -> None:
    """Каждый вариант из настроек ссылки существует в модалке. Ссылку не создаёт."""
    url = PAGES["invites"][0].format(event_id=event_id)

    with modal(browser, url, inside_modal=_MODAL) as wait:
        clickable(wait, _CREATE_LINK_BUTTON).click()

        dialog = visible(wait, _MODAL)
        dialog.find_element(*_MODAL_CREATE)

        holder = dialog.find_elements(*_SELECT_HOLDER)[position]

        browser.driver.execute_script("arguments[0].click()", holder)

        found(wait, lambda d: d.find_elements(*by_css("[role='option']")))

        missing = [option.name for option in options
                   if not [el for el in browser.driver.find_elements(
                       *by_css(option_by_value(option.value))) if el.is_displayed()]]

    assert not missing, f"пропали варианты: {missing}"


@pytest.mark.integration
def test_event_creation_wizard_opens(browser: VKBrowser) -> None:
    """Визард создания события отдаёт iframe, в котором работает схема. Событие не создаётся."""
    with editing(browser, EventCreationSchema._URL) as wait:
        present(wait, by_css(EventCreationSchema._IFRAME_CSS))
