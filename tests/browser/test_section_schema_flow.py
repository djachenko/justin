"""What a section schema clicks, and in which order — on a fake page, no browser.

The live tests only check that nothing raised: Radio and Dropdown do not read back what
they picked, so a click that never happened passed silently. Here every click is logged.
"""
from typing import cast

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver

from justin.browser.sections import section_schema
from justin.browser.sections.section_schema import (
    FilesSchema,
    ListSwitchSchema,
    MaterialsSchema,
    MusicSchema,
    PhotosSchema,
    PostsSchema,
    SectionSchema,
    ServicesSchema,
    TopicsSchema,
    VideosSchema,
)
from justin.browser.sections.section_settings import (
    AddAllowed,
    FilesSettings,
    MaterialsSettings,
    MusicSettings,
    PhotosSettings,
    PostsPublishing,
    PostsSettings,
    SectionSettings,
    ServicesSettings,
    TopicsSettings,
    VideosSettings,
)
from tests.browser.fakes import fast_wait

pytestmark = pytest.mark.usefixtures("no_pauses")


def _data_testid_in(selector: str) -> str:
    return selector.removeprefix("[data-testid='").removesuffix("']")


class FakeElement:
    _FLIPPED = {"true": "false", "false": "true"}

    def __init__(self, page: "FakePage", name: str, checked: str | None = None, text: str = "") -> None:
        self.page = page
        self.name = name
        self.checked = checked
        self.text = text

    def get_attribute(self, name: str) -> str | None:
        if name == "aria-checked":
            return self.checked

        if name == "data-testid":
            return self.name

        return None

    def find_element(self, by, selector: str) -> "FakeElement":
        """The section cell holds a title span: the modal opens from it."""
        return FakeElement(self.page, f"{self.name}:title")

    def find_elements(self, by, selector: str) -> list["FakeElement"]:
        return []

    def is_displayed(self) -> bool:
        return True

    def click(self) -> None:
        self.page.log.append(self.name)

        if self.checked is not None and self.page.landing:
            self.checked = self._FLIPPED[self.checked]


class FakePage:
    """A driver over a flat set of testids; dropdown items are listed separately."""

    def __init__(self, switches: dict[str, str] | None = None, items: tuple[str, ...] = (),
                 landing: bool = True) -> None:
        self.log: list[str] = []
        self.landing = landing
        self.switches = {name: FakeElement(self, name, checked) for name, checked in (switches or {}).items()}
        self.items = [FakeElement(self, f"item:{text}", text=text) for text in items]

    def find_element(self, by, selector: str) -> FakeElement:
        name = _data_testid_in(selector)

        if name in self.switches:
            return self.switches[name]

        return FakeElement(self, name)

    def find_elements(self, by, selector: str) -> list[FakeElement]:
        if _data_testid_in(selector) == "dropdownactionsheet-item":
            return self.items

        return []

    def execute_script(self, script: str, element: FakeElement) -> None:
        element.click()


@pytest.fixture(autouse=True)
def no_state_timeout(monkeypatch) -> None:
    """The fake page answers a click at once: one look at the switch is enough."""
    monkeypatch.setattr(section_schema, "_STATE_TIMEOUT", 0)


def run(schema: SectionSchema | ListSwitchSchema, settings: SectionSettings, page: FakePage) -> list[str]:
    driver = cast(WebDriver, page)

    schema(settings, driver, fast_wait(driver))

    return page.log


class TestSectionCall:
    def test_order_open_enabled_fields_save(self) -> None:
        page = FakePage(
            switches={"form_wall_enabled": "false", "form_wall_sharing_disabled": "true"},
            items=("All followers", "Administrators and editors"),
        )

        log = run(PostsSchema("wall"), PostsSettings(enabled=True), page)

        assert log == [
            "wall:title",
            "form_wall_enabled",
            "form_wall_publishing_allowed",
            "item:Administrators and editors",
            "form_wall_sharing_disabled",
            "form_modal_save",
        ]

    def test_disabled_section_skips_fields(self) -> None:
        """With the section off its fields are gone from the DOM — touching them would time out."""
        page = FakePage(
            switches={"form_wall_enabled": "true", "form_wall_sharing_disabled": "true"},
            items=("All followers", "Administrators and editors"),
        )

        log = run(PostsSchema("wall"), PostsSettings(enabled=False), page)

        assert log == ["wall:title", "form_wall_enabled", "form_modal_save"]

    def test_saves_when_nothing_changed(self) -> None:
        page = FakePage(switches={"form_photos_toggle": "false"})

        log = run(PhotosSchema("photos"), PhotosSettings(enabled=False), page)

        assert log == ["photos:title", "form_modal_save"]


class TestDefaultsAreClicked:
    """setup-event leaves these at their defaults; each_choice only ever sets non-defaults
    together with enabled=False, so no live test clicks them."""

    @pytest.mark.parametrize("schema,settings,toggle", [
        (PhotosSchema("photos"), PhotosSettings(enabled=True), "form_photos_toggle"),
        (VideosSchema("videos"), VideosSettings(enabled=True), "form_videos_toggle"),
        (TopicsSchema("discussions"), TopicsSettings(enabled=True), "form_discussions_toggle"),
        (MusicSchema("audios"), MusicSettings(enabled=True), "form_audios_toggle"),
        (FilesSchema("files"), FilesSettings(enabled=True), "form_files_toggle"),
        (MaterialsSchema("wiki"), MaterialsSettings(enabled=True), "form_wiki_toggle"),
    ], ids=["photos", "videos", "topics", "music", "files", "materials"])
    def test_add_allowed_radio(self, schema: SectionSchema, settings: SectionSettings, toggle: str) -> None:
        assert settings.add_allowed is AddAllowed.ADMINS_AND_EDITORS

        log = run(schema, settings, FakePage(switches={toggle: "true"}))

        assert "admins_and_editors" in log

    def test_posts_publishing_and_sharing(self) -> None:
        settings = PostsSettings(enabled=True)

        assert settings.publishing is PostsPublishing.ADMINS_AND_EDITORS
        assert settings.sharing_disabled is False

        page = FakePage(
            switches={"form_wall_enabled": "true", "form_wall_sharing_disabled": "true"},
            items=("All followers", "Administrators and editors"),
        )

        log = run(PostsSchema("wall"), settings, page)

        assert "item:Administrators and editors" in log
        assert "item:All followers" not in log
        assert page.switches["form_wall_sharing_disabled"].checked == "false"

    def test_dropdown_without_matching_item_times_out(self) -> None:
        page = FakePage(switches={"form_wall_enabled": "true"}, items=("All followers",))

        with pytest.raises(TimeoutException):
            run(PostsSchema("wall"), PostsSettings(enabled=True), page)


class TestServices:
    @pytest.mark.parametrize("before,enabled", [("false", True), ("true", False)])
    def test_toggle_flips_and_saves(self, before: str, enabled: bool) -> None:
        page = FakePage(switches={"form_services_enabled": before})

        log = run(ServicesSchema("content_tabs_services_cell"), ServicesSettings(enabled=enabled), page)

        assert log == ["content_tabs_services_cell:title", "form_services_enabled", "form_modal_save"]
        assert page.switches["form_services_enabled"].checked == str(enabled).lower()


class TestListSwitch:
    """No modal and no save: the switch in the list is the whole interaction."""

    @pytest.mark.parametrize("before,enabled", [("false", True), ("true", False)])
    def test_flips(self, before: str, enabled: bool) -> None:
        page = FakePage(switches={"chats_switch": before})

        log = run(ListSwitchSchema("chats_switch"), SectionSettings(enabled=enabled), page)

        assert log == ["chats_switch"]
        assert page.switches["chats_switch"].checked == str(enabled).lower()

    @pytest.mark.parametrize("state,enabled", [("true", True), ("false", False)])
    def test_already_set_is_skipped(self, state: str, enabled: bool) -> None:
        page = FakePage(switches={"chats_switch": state})

        assert run(ListSwitchSchema("chats_switch"), SectionSettings(enabled=enabled), page) == []

    def test_click_that_did_not_land_raises(self) -> None:
        page = FakePage(switches={"chats_switch": "false"}, landing=False)

        with pytest.raises(ValueError):
            run(ListSwitchSchema("chats_switch"), SectionSettings(enabled=True), page)

    def test_unknown_state_raises(self) -> None:
        page = FakePage()

        with pytest.raises(NoSuchElementException):
            run(ListSwitchSchema("chats_switch"), SectionSettings(enabled=True), page)
