import re
from dataclasses import fields

import pytest
from selenium.common.exceptions import NoSuchElementException

from justin.browser.event_settings import event_settings_schema
from justin.browser.event_settings.event_settings_schema import (
    _CONTENT_TABS, _SECTIONS, EventSettingsSchema, Reorder, _check_first,
    _set_custom_select, _set_main_section,
)
from justin.browser.event_settings.event_settings_settings import (
    AddressesSettings, CtaSettings, EventSettingsSettings, ExtrasSettings, MessagesSettings,
)
from justin.browser.sections.section_settings import MainSection, SectionsConfig
from tests.browser.fakes import fast_wait

EVENT_ID = 7


pytestmark = pytest.mark.usefixtures("no_pauses")


@pytest.fixture(autouse=True)
def short_state_timeout(monkeypatch):
    monkeypatch.setattr(event_settings_schema, "_STATE_TIMEOUT", 0.3)


class FakeDriver:
    """Elements are looked up by full css first, then by the testid inside it."""

    def __init__(self, elements: dict) -> None:
        self.elements = elements
        self.urls: list[str] = []
        self.clicks: list = []

    def get(self, url: str) -> None:
        self.urls.append(url)

    def find_element(self, by, css: str):
        if css in self.elements:
            return self.elements[css]

        testid = re.search(r"data-testid='([^']+)'", css)

        assert testid is not None

        return self.elements[testid[1]]

    def find_elements(self, by, css: str) -> list:
        return []

    def execute_script(self, script: str, element) -> None:
        self.clicks.append(element)

        element.click()


class FakeCheckbox:
    def __init__(self, selected: bool) -> None:
        self.selected = selected

    def is_selected(self) -> bool:
        return self.selected

    def click(self) -> None:
        self.selected = not self.selected


class FakeLabel:
    """A click on the wrapper does nothing — only the inner input toggles."""

    def __init__(self, selected: bool) -> None:
        self.checkbox = FakeCheckbox(selected)

    def find_element(self, by, css: str) -> FakeCheckbox:
        assert css == "input[type='checkbox']"

        return self.checkbox

    def click(self) -> None:
        pass


class FakeIdd:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def find_element(self, by, css: str) -> "FakeIddItem":
        return FakeIddItem(self, css.endswith("idd_item_1']"))

    def click(self) -> None:
        pass


class FakeIddItem:
    def __init__(self, idd: FakeIdd, value: bool) -> None:
        self.idd = idd
        self.value = value

    def click(self) -> None:
        self.idd.enabled = self.value


class FakeHidden:
    def __init__(self, idd: FakeIdd) -> None:
        self.idd = idd

    def get_attribute(self, name: str) -> str:
        return str(int(self.idd.enabled))


@pytest.fixture
def saves(monkeypatch) -> list[str]:
    calls: list[str] = []

    monkeypatch.setattr(event_settings_schema, "click_save", lambda driver, wait: calls.append("save"))
    monkeypatch.setattr(event_settings_schema, "click_save_if_present", lambda driver: calls.append("save_if_present"))

    return calls


@pytest.mark.parametrize("initial,wanted,clicks", [
    (False, False, 0),
    (False, True, 1),
    (True, False, 1),
    (True, True, 0),
])
class TestApplyCta:
    def test_state(self, initial, wanted, clicks) -> None:
        label = FakeLabel(initial)
        driver = FakeDriver({"groups_edit_header_switch_label_cta": label})

        EventSettingsSchema()(EVENT_ID, EventSettingsSettings(cta=CtaSettings(wanted)), driver, fast_wait(driver))

        assert label.checkbox.selected == wanted
        assert len(driver.clicks) == clicks
        assert driver.urls == ["https://vk.ru/event7/settings/cta"]


@pytest.mark.parametrize("initial,wanted,clicks", [
    (False, False, 0),
    (False, True, 2),
    (True, False, 2),
    (True, True, 0),
])
class TestApplyAddresses:
    def test_state(self, initial, wanted, clicks, saves) -> None:
        idd = FakeIdd(initial)
        driver = FakeDriver({
            "groups_edit_g_addresses": idd,
            "#groups_edit_g_addresses_input": FakeHidden(idd),
        })

        EventSettingsSchema()(EVENT_ID, EventSettingsSettings(addresses=AddressesSettings(wanted)), driver, fast_wait(driver))

        assert idd.enabled == wanted
        assert len(driver.clicks) == clicks  # the wrapper, then the item
        assert driver.urls == ["https://vk.ru/event7?act=addresses"]
        assert saves == ["save_if_present"]


EXTRAS = {
    "co_creatorship": "clips_co_ownership_enabled",
    "story_replies": "stories_replies_enabled",
    "show_in_left_menu": "show_in_left_menu",
}


class TestApplyExtras:
    @staticmethod
    def apply(settings: ExtrasSettings, initial: bool) -> dict[str, FakeLabel]:
        labels = {testid: FakeLabel(initial) for testid in EXTRAS.values()}
        driver = FakeDriver(labels)

        EventSettingsSchema()(EVENT_ID, EventSettingsSettings(extras=settings), driver, fast_wait(driver))

        assert driver.urls == ["https://vk.ru/event7/settings/extras"]

        return labels

    @pytest.mark.parametrize("field,testid", EXTRAS.items())
    @pytest.mark.parametrize("wanted", [False, True])
    def test_field_goes_to_its_checkbox(self, field, testid, wanted, saves) -> None:
        labels = self.apply(ExtrasSettings(**{field: wanted}), initial=not wanted)

        changed = {key for key, label in labels.items() if label.checkbox.selected == wanted}

        assert changed == {testid}
        assert saves == ["save_if_present"]

    def test_none_leaves_everything_alone(self, saves) -> None:
        labels = self.apply(ExtrasSettings(), initial=True)

        assert all(label.checkbox.selected for label in labels.values())


class FakeNative:
    def __init__(self, value: str) -> None:
        self.value = value

    def get_attribute(self, name: str) -> str:
        return self.value


class TestSetCustomSelect:
    @staticmethod
    def run(monkeypatch, current: str, wanted: str, lands: bool = True) -> list:
        native = FakeNative(current)
        holder = "holder"
        driver = FakeDriver({"select[data-testid='m']": native, "input[data-testid='m']": holder})
        calls: list = []

        def fake_set(driver, wait, el, value) -> None:
            calls.append((el, value))

            if lands:
                native.value = value

        monkeypatch.setattr(event_settings_schema, "set_custom_select", fake_set)

        _set_custom_select(driver, fast_wait(driver), "m", wanted)

        return calls

    def test_already_set_value_is_skipped(self, monkeypatch) -> None:
        assert not self.run(monkeypatch, "1", "1")

    def test_value_is_applied_through_the_holder(self, monkeypatch) -> None:
        assert self.run(monkeypatch, "0", "1") == [("holder", "1")]

    def test_native_select_that_did_not_follow_raises(self, monkeypatch) -> None:
        with pytest.raises(ValueError):
            self.run(monkeypatch, "0", "1", lands=False)


class FakeTextarea:
    def __init__(self, log: list) -> None:
        self.log = log

    def clear(self) -> None:
        self.log.append("clear")


class TestApplyMessages:
    @pytest.fixture
    def log(self, monkeypatch) -> list:
        log: list = []

        monkeypatch.setattr(event_settings_schema, "_set_custom_select",
                            lambda driver, wait, testid, value: log.append(("select", testid, value)))
        monkeypatch.setattr(event_settings_schema, "type_into", lambda el, text: log.append(("type", text)))
        monkeypatch.setattr(event_settings_schema, "click_save", lambda driver, wait: log.append("save"))

        return log

    @pytest.mark.parametrize("enabled,value", [(False, "0"), (True, "1")])
    def test_enabled_is_the_select_value(self, enabled, value, log) -> None:
        driver = FakeDriver({})

        EventSettingsSchema()(EVENT_ID, EventSettingsSettings(messages=MessagesSettings(enabled)), driver, fast_wait(driver))

        assert log == [("select", "settings_messages_enabled", value), "save"]
        assert driver.urls == ["https://vk.ru/event7/settings/messages"]

    def test_first_message_replaces_the_text_before_saving(self, log) -> None:
        driver = FakeDriver({})
        driver.elements["settings_messages_first_message"] = FakeTextarea(log)

        EventSettingsSchema()(
            EVENT_ID, EventSettingsSettings(messages=MessagesSettings(first_message="hi")), driver, fast_wait(driver),
        )

        assert log[1:] == ["clear", ("type", "hi"), "save"]


class TestSectionTables:
    """The pairs are spelled out on purpose: a swapped testid applies settings to the wrong tab."""

    def test_content_tabs(self) -> None:
        assert [(name, type(schema).__name__, schema.test_id) for name, schema in _CONTENT_TABS] == [
            ("posts", "PostsSchema", "content_tabs_wall_cell"),
            ("photos", "PhotosSchema", "content_tabs_photos_cell"),
            ("videos", "VideosSchema", "content_tabs_videos_cell"),
            ("topics", "TopicsSchema", "content_tabs_discussions_cell"),
            ("music", "MusicSchema", "content_tabs_audios_cell"),
            ("services", "ServicesSchema", "content_tabs_services_cell"),
            ("products", "ListSwitchSchema", "content_tabs_market_switch"),
            ("clips", "ListSwitchSchema", "content_tabs_short_videos_switch"),
        ]

    def test_sections(self) -> None:
        assert [(name, type(schema).__name__, schema.test_id) for name, schema in _SECTIONS] == [
            ("files", "FilesSchema", "files"),
            ("materials", "MaterialsSchema", "wiki"),
            ("chats", "ListSwitchSchema", "chats_switch"),
            ("articles", "ListSwitchSchema", "articles_switch"),
            ("moments", "ListSwitchSchema", "narratives_switch"),
        ]

    def test_every_config_field_has_exactly_one_schema(self) -> None:
        names = [name for name, _ in _CONTENT_TABS + _SECTIONS]

        assert sorted(names + ["main_section"]) == sorted(field.name for field in fields(SectionsConfig))


LABELS = {"wall": "Posts", "photos": "Photos", "videos": "Videos"}


class ReorderPage:
    """Content tabs: reorder mode, a pending order, and the order that survived the save."""

    def __init__(self, saved: list[str], toggle_enabled: bool = True,
                 drag_lands: bool = True, movable: list[str] | None = None) -> None:
        self.saved = saved
        self.order = list(saved)
        self.movable = movable or saved
        self.toggle_enabled = toggle_enabled
        self.drag_lands = drag_lands
        self.reorder = False
        self.dialog = False
        self.drags: list[int] = []


class FakeCell:
    def __init__(self, label: str) -> None:
        if label:
            self.text = f"{label}\n3 items"
        else:
            self.text = ""


class FakeToggle:
    def __init__(self, page: ReorderPage) -> None:
        self.page = page

    def is_enabled(self) -> bool:
        return self.page.toggle_enabled

    def click(self) -> None:
        if self.page.reorder:
            self.page.dialog = True

        self.page.reorder = not self.page.reorder


class FakeConfirm:
    def __init__(self, page: ReorderPage, commits: bool) -> None:
        self.page = page
        self.commits = commits

    def click(self) -> None:
        if self.commits:
            self.page.saved = list(self.page.order)

        self.page.dialog = False


class FakeDialog:
    """A hidden dialog stays in the DOM too; confirming it saves nothing."""

    def __init__(self, page: ReorderPage, displayed: bool) -> None:
        self.page = page
        self.displayed = displayed

    def is_displayed(self) -> bool:
        return self.displayed

    def find_element(self, by, css: str) -> FakeConfirm:
        assert css == "[data-testid='form_modal_save']"

        return FakeConfirm(self.page, self.displayed)


class ReorderDriver:
    def __init__(self, page: ReorderPage) -> None:
        self.page = page
        self.urls: list[str] = []

    def get(self, url: str) -> None:
        self.urls.append(url)
        self.page.order = list(self.page.saved)
        self.page.reorder = False
        self.page.dialog = False

    def find_element(self, by, css: str):
        if css == Reorder.TOGGLE[1]:
            return FakeToggle(self.page)

        if css == Reorder.LIST[1]:
            assert self.page.reorder

            return "list"

        value = re.fullmatch(r"\[data-testid='content_tabs_(\w+)_cell'\]", css)

        assert value is not None

        return FakeCell(LABELS[value[1]])

    def find_elements(self, by, css: str) -> list:
        if css == Reorder.TAB_CELLS[1]:
            # A tab that cannot be moved may stand first outside reorder mode.
            return [FakeCell("Info")] + [FakeCell(label) for label in self.page.order]

        if self.page.dialog:
            return [FakeDialog(self.page, displayed=False), FakeDialog(self.page, displayed=True)]

        return []

    def execute_script(self, script: str, element) -> list[FakeCell]:
        movable = [label for label in self.page.order if label in self.page.movable]

        return [FakeCell("")] + [FakeCell(label) for label in movable]


class TestCheckFirst:
    def test_first_passes(self) -> None:
        _check_first(["Photos", "Posts"], "Photos", "after drag")

    def test_other_first_raises_with_stage(self) -> None:
        with pytest.raises(ValueError, match="after save"):
            _check_first(["Posts", "Photos"], "Photos", "after save")


class TestSetMainSection:
    @pytest.fixture(autouse=True)
    def fake_drag(self, monkeypatch) -> None:
        def drag(driver: ReorderDriver, cell: FakeCell, position: int) -> None:
            page = driver.page
            label = cell.text.splitlines()[0]

            page.drags.append(position)

            if page.drag_lands:
                page.order.remove(label)
                page.order.insert(0, label)

        monkeypatch.setattr(event_settings_schema, "_drag_to_top", drag)

    @staticmethod
    def run(page: ReorderPage, section: MainSection = MainSection.PHOTOS) -> ReorderDriver:
        driver = ReorderDriver(page)

        _set_main_section(driver, fast_wait(driver), EVENT_ID, section)

        return driver

    def test_tab_is_dragged_and_saved_first(self) -> None:
        page = ReorderPage(["Posts", "Videos", "Photos"])

        driver = self.run(page)

        assert page.saved == ["Photos", "Posts", "Videos"]
        assert page.drags == [2]
        assert driver.urls == ["https://vk.ru/event7/settings/content_tabs"] * 2

    def test_tab_already_first_is_not_dragged(self) -> None:
        page = ReorderPage(["Photos", "Posts"])

        self.run(page)

        assert page.drags == []
        assert page.saved == ["Photos", "Posts"]

    def test_drag_that_did_not_land_raises(self) -> None:
        with pytest.raises(ValueError, match="after drag"):
            self.run(ReorderPage(["Posts", "Photos"], drag_lands=False))

    def test_order_lost_on_save_raises(self, monkeypatch) -> None:
        """Without confirming the warning dialog the order rolls back."""
        monkeypatch.setattr(event_settings_schema, "_confirm_reorder", lambda driver: None)

        with pytest.raises(ValueError, match="after save"):
            self.run(ReorderPage(["Posts", "Photos"]))

    def test_tab_missing_from_reorder_list_raises(self) -> None:
        with pytest.raises(NoSuchElementException):
            self.run(ReorderPage(["Posts", "Photos"], movable=["Posts", "Videos"]))

    def test_disabled_reorder_leaves_the_page_alone(self) -> None:
        page = ReorderPage(["Posts", "Photos"], toggle_enabled=False)

        driver = self.run(page)

        assert not page.reorder
        assert page.saved == ["Posts", "Photos"]
        assert driver.urls == ["https://vk.ru/event7/settings/content_tabs"]


class TestApplySectionsMain:
    @pytest.mark.parametrize("section,applied", [
        (None, []),
        (MainSection.PHOTOS, [MainSection.PHOTOS]),
    ])
    def test_main_section_is_applied_only_when_set(self, section, applied, monkeypatch) -> None:
        calls: list = []

        monkeypatch.setattr(event_settings_schema, "_set_main_section",
                            lambda driver, wait, event_id, value: calls.append(value))

        driver = FakeDriver({})

        EventSettingsSchema()(
            EVENT_ID, EventSettingsSettings(sections=SectionsConfig(main_section=section)), driver, fast_wait(driver),
        )

        assert calls == applied
        assert driver.urls == []
