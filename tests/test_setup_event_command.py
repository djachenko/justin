import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest
from justin_utils.filesystem import Folder

from justin.browser.event_settings.event_settings_settings import EventSettingsSettings
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
    def get(self, url: str) -> FakeGroup:
        return FakeGroup(-URL_EVENT_ID)


class FakeContext:
    closed_group = FakeGroup(CLOSED_GROUP_ID)
    meeting_group = FakeGroup(MEETING_GROUP_ID)
    pyvko = FakePyvko()


class FakeBrowser:
    def __init__(self, headless: bool | None) -> None:
        self.headless = headless
        self.event_id: int | None = None
        self.settings: EventSettingsSettings | None = None

    def __enter__(self) -> "FakeBrowser":
        return self

    def __exit__(self, *_) -> None:
        pass

    def create_event(self, **_) -> int:
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

        assert _applied(browsers).setup.organiser_id == CLOSED_GROUP_ID

    def test_meeting_folder_is_organised_by_the_meeting_group(self, browsers) -> None:
        _run(meeting_photoset(), url=f"{VK_URL}/event1")

        assert _applied(browsers).setup.organiser_id == MEETING_GROUP_ID


class TestUrl:
    def test_linked_folder_is_set_up_as_is(self, browsers, metafiles) -> None:
        metafiles["anna"] = -2
        metafiles["meeting"] = -URL_EVENT_ID
        photoset = FakePhotoset(
            FakePart(closed=FakeFolder("closed", FakeFolder("anna"), FakeFolder("bob")),
                     meeting=FakeFolder("meeting")),
        )

        _run(photoset, url=f"{VK_URL}/event1")

        assert _applied(browsers).setup.organiser_id == MEETING_GROUP_ID
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

        assert _applied(browsers).setup.organiser_id == MEETING_GROUP_ID
        assert read_meta(tmp_path, "meeting") == {"group": {"group_id": URL_EVENT_ID}}
        assert not (tmp_path / "26.6.15.party" / "closed/anna" / "_meta.json").exists()

    def test_same_event_with_both_signs_is_a_duplicate(self, browsers, tmp_path: Path) -> None:
        photoset = make_photoset(tmp_path, "closed/anna", "closed/bob", "meeting")
        write_meta(tmp_path, "closed/anna", {"group": {"group_id": 2}})
        write_meta(tmp_path, "closed/bob", {"group": {"group_id": -2}})

        with pytest.raises(ValueError):
            _run(photoset, create=True)

        assert browsers == []
