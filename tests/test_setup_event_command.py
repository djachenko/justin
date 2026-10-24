import json
from dataclasses import dataclass, fields
from datetime import date, datetime
from pathlib import Path

import pytest
from justkitten.filesystem import Folder
from typer.testing import CliRunner

from justin.browser.event_creation.event_creation_settings import Category
from justin.browser.event_settings.event_settings_settings import EventSettingsSettings
from justin.browser.sections.section_settings import MainSection, SectionsConfig
from justin.di.metafiles import setup_metafiles
from justin.shared.models.photoset import Photoset
from justin.typer import setup_event_command
from justin.shared.vk import VK_URL
from justin.typer.setup_event_command import SetupEventCommand

CLOSED_GROUP_ID = 42
MEETING_GROUP_ID = 43
URL_EVENT_ID = 1
CREATED_EVENT_ID = 7


class FakeGroup:
    def __init__(self, group_id: int) -> None:
        self.id = group_id


class FakePyvko:
    """Any url resolves to the --url event unless a test registers a group for it."""

    def __init__(self) -> None:
        self.groups: dict[str, FakeGroup] = {}

    def get(self, url: str) -> FakeGroup:
        return self.groups.get(url, FakeGroup(-URL_EVENT_ID))


class FakeContext:
    """pyvko keeps group ids negative, so the fakes do too."""

    def __init__(self) -> None:
        self.closed_group = FakeGroup(-CLOSED_GROUP_ID)
        self.meeting_group = FakeGroup(-MEETING_GROUP_ID)
        self.pyvko = FakePyvko()


class FakeBrowser:
    def __init__(self, headless: bool | None) -> None:
        self.headless = headless
        self.event_id: int | None = None
        self.settings: EventSettingsSettings | None = None
        self.created: dict | None = None

    def __enter__(self) -> "FakeBrowser":
        return self

    def __exit__(self, *_) -> None:
        pass

    def create_event(self, title: str, start_dt: datetime, end_dt: datetime | None = None,
                     organiser_id: int | None = None, is_closed: bool = True) -> int:
        self.created = {
            "title": title,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "organiser_id": organiser_id,
            "is_closed": is_closed,
        }

        return CREATED_EVENT_ID

    def apply_settings(self, event_id: int, settings: EventSettingsSettings) -> None:
        self.event_id = event_id
        self.settings = settings


class FakeFolder:
    def __init__(self, name: str, *subfolders: "FakeFolder") -> None:
        self.name = name
        self.subfolders = list(subfolders)


class FakePart:
    def __init__(self, closed: FakeFolder | None = None,
                 meeting: FakeFolder | None = None) -> None:
        self.closed = closed
        self.meeting = meeting


class FakePhotoset:
    def __init__(self, *parts: FakePart) -> None:
        self.name = "26.6.15.party"
        self.path = self.name
        self.parts = list(parts)


def closed_photoset(*names: str) -> FakePhotoset:
    return FakePhotoset(FakePart(closed=FakeFolder("closed", *(FakeFolder(name) for name in names))))


def meeting_photoset() -> FakePhotoset:
    return FakePhotoset(FakePart(meeting=FakeFolder("meeting")))


@pytest.fixture
def browsers(monkeypatch) -> list[FakeBrowser]:
    opened: list[FakeBrowser] = []

    def open_browser(headless: bool | None = None) -> FakeBrowser:
        browser = FakeBrowser(headless)
        opened.append(browser)

        return browser

    monkeypatch.setattr(setup_event_command, "VKBrowser", open_browser)

    return opened


@pytest.fixture
def metafiles(monkeypatch) -> dict[str, int]:
    """Folder name → group_id of its GroupMetafile; a test fills it before running."""
    stored: dict[str, int] = {}

    @dataclass
    class FakeMetafile:
        group_id: int

        @staticmethod
        def get(folder: FakeFolder) -> "FakeMetafile | None":
            if folder.name not in stored:
                return None

            return FakeMetafile(stored[folder.name])

        def save(self, folder: FakeFolder) -> None:
            stored[folder.name] = self.group_id

    monkeypatch.setattr(setup_event_command, "GroupMetafile", FakeMetafile)

    return stored


def _run(photoset: FakePhotoset, **kwargs) -> None:
    command = SetupEventCommand(FakeContext(), **kwargs)  # type: ignore[arg-type]

    command.run_for_photoset(photoset, {})  # type: ignore[arg-type]


def _applied(browsers: list[FakeBrowser]) -> EventSettingsSettings:
    [browser] = browsers

    assert browser.settings is not None

    return browser.settings


@pytest.mark.usefixtures("metafiles")
class TestDate:
    def test_option_date_wins(self, browsers) -> None:
        _run(closed_photoset("anna"), url=f"{VK_URL}/event1", date_="1.7.26")

        assert _applied(browsers).setup.start_dt.date() == date(2026, 7, 1)

    def test_date_comes_from_the_name(self, browsers) -> None:
        _run(closed_photoset("anna"), url=f"{VK_URL}/event1")

        assert _applied(browsers).setup.start_dt.date() == date(2026, 6, 15)


@pytest.mark.usefixtures("metafiles")
class TestBrowser:
    def test_creation_keeps_the_window_visible(self, browsers) -> None:
        _run(closed_photoset("anna"), create=True)

        [browser] = browsers

        assert browser.headless is False
        assert browser.event_id == CREATED_EVENT_ID

    def test_setup_decides_by_run_mode(self, browsers) -> None:
        _run(closed_photoset("anna"), url=f"{VK_URL}/event1")

        [browser] = browsers

        assert browser.headless is None
        assert browser.event_id == URL_EVENT_ID


@pytest.mark.usefixtures("metafiles")
class TestParent:
    def test_closed_folder_is_organised_by_the_closed_group(self, browsers) -> None:
        _run(closed_photoset("anna"), url=f"{VK_URL}/event1")

        assert _applied(browsers).setup.organiser_id == -CLOSED_GROUP_ID

    def test_meeting_folder_is_organised_by_the_meeting_group(self, browsers) -> None:
        _run(meeting_photoset(), url=f"{VK_URL}/event1")

        assert _applied(browsers).setup.organiser_id == -MEETING_GROUP_ID


class TestUrl:
    def test_linked_folder_is_set_up_as_is(self, browsers, metafiles) -> None:
        metafiles["anna"] = -2
        metafiles["meeting"] = -URL_EVENT_ID
        photoset = FakePhotoset(
            FakePart(closed=FakeFolder("closed", FakeFolder("anna"), FakeFolder("bob")),
                     meeting=FakeFolder("meeting")),
        )

        _run(photoset, url=f"{VK_URL}/event1")

        assert _applied(browsers).setup.organiser_id == -MEETING_GROUP_ID
        assert "bob" not in metafiles

    def test_free_folder_gets_linked(self, browsers, metafiles) -> None:
        metafiles["anna"] = -2

        _run(closed_photoset("anna", "bob"), url=f"{VK_URL}/event1")

        assert metafiles["bob"] == -URL_EVENT_ID

    def test_no_linked_and_no_free_folder_raises(self, browsers, metafiles) -> None:
        metafiles["anna"] = -2

        with pytest.raises(ValueError):
            _run(closed_photoset("anna"), url=f"{VK_URL}/event1")

        assert browsers == []


class TestCreate:
    def test_first_free_folder_gets_the_event(self, browsers, metafiles) -> None:
        metafiles["anna"] = -2

        _run(closed_photoset("anna", "bob", "carl"), create=True)

        assert metafiles["bob"] == -CREATED_EVENT_ID
        assert "carl" not in metafiles

    def test_closed_goes_before_meeting(self, browsers, metafiles) -> None:
        photoset = FakePhotoset(
            FakePart(closed=FakeFolder("closed", FakeFolder("anna")), meeting=FakeFolder("meeting")),
        )

        _run(photoset, create=True)

        assert metafiles == {"anna": -CREATED_EVENT_ID}

    def test_no_free_folder_raises(self, browsers, metafiles) -> None:
        metafiles["anna"] = -2

        with pytest.raises(ValueError):
            _run(closed_photoset("anna"), create=True)

        assert browsers == []

    def test_photoset_without_parts_raises(self, browsers, metafiles) -> None:
        with pytest.raises(ValueError):
            _run(FakePhotoset(), create=True)

        assert browsers == []


class TestUniqueGroups:
    def test_two_folders_with_one_event_raise(self, browsers, metafiles) -> None:
        metafiles["anna"] = -2
        metafiles["bob"] = 2

        with pytest.raises(ValueError):
            _run(closed_photoset("anna", "bob", "carl"), create=True)

        assert browsers == []


@pytest.fixture
def real_metafiles() -> None:
    setup_metafiles()


def make_photoset(root: Path, *folders: str) -> Photoset:
    """Folder skips empty directories, so every folder gets a photo."""
    path = root / "26.6.15.party"

    for folder in ("", *folders):
        (path / folder).mkdir(parents=True, exist_ok=True)
        (path / folder / "1.jpg").touch()

    photoset = Photoset.from_folder(Folder(path))

    assert photoset is not None

    return photoset


def read_meta(root: Path, folder: str) -> dict:
    return json.loads((root / "26.6.15.party" / folder / "_meta.json").read_text())


def write_meta(root: Path, folder: str, content: dict) -> None:
    (root / "26.6.15.party" / folder / "_meta.json").write_text(json.dumps(content))


@pytest.mark.usefixtures("real_metafiles")
class TestRealMetafiles:
    def test_created_event_is_written_as_negative_group_id(self, browsers, tmp_path: Path) -> None:
        photoset = make_photoset(tmp_path, "closed/anna")

        _run(photoset, create=True)

        assert read_meta(tmp_path, "closed/anna") == {"group": {"group_id": -CREATED_EVENT_ID}}

    def test_linking_keeps_other_metafiles_of_the_folder(self, browsers, tmp_path: Path) -> None:
        photoset = make_photoset(tmp_path, "meeting")
        write_meta(tmp_path, "meeting", {"person": {"comments": []}})

        _run(photoset, url=f"{VK_URL}/event1")

        assert read_meta(tmp_path, "meeting") == {
            "person": {"comments": []},
            "group": {"group_id": -URL_EVENT_ID},
        }

    def test_reruns_walk_the_free_folders_one_by_one(self, browsers, monkeypatch, tmp_path: Path) -> None:
        created = iter([11, 12])
        monkeypatch.setattr(FakeBrowser, "create_event", lambda self, **_: next(created))
        photoset = make_photoset(tmp_path, "closed/anna", "meeting")

        _run(photoset, create=True)
        _run(photoset, create=True)

        assert read_meta(tmp_path, "closed/anna") == {"group": {"group_id": -11}}
        assert read_meta(tmp_path, "meeting") == {"group": {"group_id": -12}}

        with pytest.raises(ValueError):
            _run(photoset, create=True)

    def test_url_finds_a_folder_linked_with_a_positive_id(self, browsers, tmp_path: Path) -> None:
        """A metafile may keep the id positive: the sign migration only covers the old flat
        format, so matching ignores the sign and the file stays as is."""
        photoset = make_photoset(tmp_path, "closed/anna", "meeting")
        write_meta(tmp_path, "meeting", {"group": {"group_id": URL_EVENT_ID}})

        _run(photoset, url=f"{VK_URL}/event1")

        assert _applied(browsers).setup.organiser_id == -MEETING_GROUP_ID
        assert read_meta(tmp_path, "meeting") == {"group": {"group_id": URL_EVENT_ID}}
        assert not (tmp_path / "26.6.15.party" / "closed/anna" / "_meta.json").exists()

    def test_same_event_with_both_signs_is_a_duplicate(self, browsers, tmp_path: Path) -> None:
        photoset = make_photoset(tmp_path, "closed/anna", "closed/bob", "meeting")
        write_meta(tmp_path, "closed/anna", {"group": {"group_id": 2}})
        write_meta(tmp_path, "closed/bob", {"group": {"group_id": -2}})

        with pytest.raises(ValueError):
            _run(photoset, create=True)

        assert browsers == []


def _created(browsers: list[FakeBrowser]) -> dict:
    [browser] = browsers

    assert browser.created is not None

    return browser.created


@pytest.mark.usefixtures("metafiles")
class TestCreatedEvent:
    def test_event_runs_four_hours_from_noon_and_is_closed(self, browsers) -> None:
        _run(closed_photoset("anna"), create=True)

        assert _created(browsers) == {
            "title": "26.6.15.party",
            "start_dt": datetime(2026, 6, 15, 12),
            "end_dt": datetime(2026, 6, 15, 16),
            "organiser_id": -CLOSED_GROUP_ID,
            "is_closed": True,
        }

    def test_title_option_overrides_the_photoset_name(self, browsers) -> None:
        _run(closed_photoset("anna"), create=True, title="Party")

        assert _created(browsers)["title"] == "Party"
        assert _applied(browsers).setup.title == "Party"


@pytest.mark.usefixtures("metafiles")
class TestDefaultSettings:
    @pytest.fixture
    def settings(self, browsers) -> EventSettingsSettings:
        _run(closed_photoset("anna"), url=f"{VK_URL}/event1")

        return _applied(browsers)

    def test_setup_repeats_the_created_event(self, settings) -> None:
        assert settings.setup is not None
        assert settings.setup.title == "26.6.15.party"
        assert settings.setup.start_dt == datetime(2026, 6, 15, 12)
        assert settings.setup.end_dt == datetime(2026, 6, 15, 16)
        assert settings.setup.organiser_id == -CLOSED_GROUP_ID
        assert settings.setup.is_closed is True
        assert settings.setup.category == Category.CIRCUS

    def test_messages_are_off(self, settings) -> None:
        assert settings.messages is not None
        assert settings.messages.enabled is False

    def test_photos_lead_the_page(self, settings) -> None:
        assert settings.sections is not None
        assert settings.sections.main_section == MainSection.PHOTOS

    def test_only_posts_photos_and_videos_stay_on(self, settings) -> None:
        """Every section is set explicitly — None would leave whatever VK had."""
        assert settings.sections is not None

        enabled = {
            field.name: getattr(settings.sections, field.name).enabled
            for field in fields(SectionsConfig)
            if field.name != "main_section"
        }

        assert enabled == {
            "posts": True,
            "photos": True,
            "videos": True,
            "topics": False,
            "music": False,
            "files": False,
            "materials": False,
            "services": False,
            "chats": False,
            "clips": False,
            "articles": False,
            "moments": False,
            "products": False,
        }


@pytest.fixture
def answers(monkeypatch) -> list[str]:
    """Typed answers to input(), in order; a test fills it before running."""
    typed: list[str] = []

    monkeypatch.setattr("builtins.input", lambda _: typed.pop(0))

    return typed


@pytest.fixture
def choice(monkeypatch) -> list[str]:
    """The parent picked from the menu; empty means the menu must not be shown."""
    picked: list[str] = []

    monkeypatch.setattr(setup_event_command.util, "ask_for_choice", lambda *_: picked.pop())

    return picked


def _run_manual(context: FakeContext | None = None, **kwargs) -> None:
    command = SetupEventCommand(context or FakeContext(), manual=True, **kwargs)  # type: ignore[arg-type]

    command.run()


class TestManual:
    @pytest.mark.parametrize(("picked", "organiser_id"), [
        ("closed", -CLOSED_GROUP_ID),
        ("meeting", -MEETING_GROUP_ID),
    ])
    def test_asks_title_date_and_parent(self, browsers, answers, choice, picked, organiser_id) -> None:
        answers.extend(["Party", "2.8.26"])
        choice.append(picked)

        _run_manual(create=True)

        assert _created(browsers) == {
            "title": "Party",
            "start_dt": datetime(2026, 8, 2, 12),
            "end_dt": datetime(2026, 8, 2, 16),
            "organiser_id": organiser_id,
            "is_closed": True,
        }

    def test_options_skip_the_questions(self, browsers, answers, choice) -> None:
        context = FakeContext()
        context.pyvko.groups[f"{VK_URL}/club99"] = FakeGroup(-99)

        _run_manual(context, create=True, title="Party", date_="1.7.26", parent=f"{VK_URL}/club99")

        assert _created(browsers)["title"] == "Party"
        assert _created(browsers)["start_dt"] == datetime(2026, 7, 1, 12)
        assert _created(browsers)["organiser_id"] == -99

    def test_unknown_parent_raises(self, browsers, choice) -> None:
        choice.append("other")

        with pytest.raises(ValueError):
            _run_manual(create=True, title="Party", date_="1.7.26")

        assert browsers == []

    def test_no_folder_is_linked(self, browsers, metafiles, choice) -> None:
        choice.append("closed")

        _run_manual(create=True, title="Party", date_="1.7.26")

        assert metafiles == {}


class TestModeRequired:
    def test_setup_without_create_or_url_raises(self, browsers, choice) -> None:
        choice.append("closed")

        with pytest.raises(ValueError, match="Either --create or --url"):
            _run_manual(title="Party", date_="1.7.26")

    def test_cli_exits_before_doing_anything(self, monkeypatch) -> None:
        constructed: list[object] = []
        monkeypatch.setattr(setup_event_command, "SetupEventCommand", lambda *args: constructed.append(args))

        result = CliRunner().invoke(setup_event_command.app, [])

        assert result.exit_code == 1
        assert "Either --create or --url" in result.output
        assert constructed == []


class TestLinkBeforeSettings:
    def test_failed_settings_keep_the_link(self, browsers, metafiles, monkeypatch) -> None:
        """Otherwise a rerun with --create would make a second event for the folder."""
        def fail(*_) -> None:
            raise RuntimeError("settings page broke")

        monkeypatch.setattr(FakeBrowser, "apply_settings", fail)

        with pytest.raises(RuntimeError):
            _run(closed_photoset("anna"), create=True)

        assert metafiles == {"anna": -CREATED_EVENT_ID}
