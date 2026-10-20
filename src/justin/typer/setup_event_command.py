from datetime import date, time, datetime, timedelta
from pathlib import Path
from typing import Annotated, Iterable, List, Optional

import typer
from justin_utils import util
from justin_utils.filesystem import Folder
from justin_utils.util import first, parse_date
from pyvko.aspects.groups import Group
from typer import Typer, Argument

from justin.browser.event_creation.event_creation_settings import Category
from justin.browser.event_settings.event_settings_settings import EventSettingsSettings, MessagesSettings
from justin.browser.event_setup.event_setup_settings import EventSetupSettings
from justin.browser.sections.section_settings import (
    ArticlesSettings, ChatsSettings, ClipsSettings, FilesSettings, MainSection,
    MaterialsSettings, MomentsSettings, MusicSettings, PhotosSettings, PostsSettings,
    ProductsSettings, SectionsConfig, ServicesSettings, TopicsSettings, VideosSettings,
)
from justin.browser.vk_browser import VKBrowser
from justin.shared.context import Context
from justin.shared.metafiles.metafile import GroupMetafile
from justin.shared.models.photoset import Photoset
from justin.shared.vk import VK_URL
from justin.typer.base_commands.pattern_command import Extra, PatternCommand


class SetupEventCommand(PatternCommand):
    """Creates or configures a VK event — from a photoset or by hand.

    Parsing patterns, building the photoset and filtering out non-photosets is
    PatternCommand's job.
    """

    def __init__(
        self,
        context: Context,
        patterns: Iterable[Path] = (),
        create: bool = False,
        url: Optional[str] = None,
        manual: bool = False,
        date_: Optional[str] = None,
        title: Optional[str] = None,
        parent: Optional[str] = None,
    ):
        super().__init__(context, patterns)

        self.__create = create
        self.__url = url
        self.__manual = manual
        self.__date = self.__parsed_date(date_)
        self.__title = title
        self.__parent = parent

    @staticmethod
    def __parsed_date(date_: str | None) -> date | None:
        if not date_:
            return None

        return parse_date(date_)

    def run(self) -> None:
        if self.__manual:
            self.__setup(self.__manual_title(), self.__manual_date(), self.__manual_parent())

            return

        super().run()

    def run_for_photoset(self, photoset: Photoset, extra: Extra) -> None:
        candidates = self.__candidates(photoset)

        self.__check_unique_groups(candidates, photoset)

        folder, parent = self.__target(candidates, photoset)
        title = self.__title or photoset.name

        event_id = self.__setup(title, self.__date or self.__date_from_name(photoset.name), parent)

        if GroupMetafile.get(folder) is None:
            GroupMetafile(group_id=-event_id).save(folder)

    def __manual_title(self) -> str:
        return self.__title or input("Enter event title: ")

    def __manual_date(self) -> date:
        return self.__date or parse_date(input("Enter event date: "))

    def __manual_parent(self):
        if self.__parent:
            return self.context.pyvko.get(self.__parent)

        choice = util.ask_for_choice("Choose event parent:", ["closed", "meeting"])

        if choice == "closed":
            return self.context.closed_group

        if choice == "meeting":
            return self.context.meeting_group

        raise ValueError("Invalid parent")

    def __candidates(self, photoset: Photoset) -> list[tuple[Folder, Group]]:
        """Folders an event belongs to, in walk order: every closed/<name> has its own
        event, meeting has one. The parent comes from the kind of folder."""
        closed = [
            (name_folder, self.context.closed_group)
            for part in photoset.parts
            if part.closed is not None
            for name_folder in part.closed.subfolders
        ]
        meeting = [
            (part.meeting, self.context.meeting_group)
            for part in photoset.parts
            if part.meeting is not None
        ]

        return closed + meeting

    @staticmethod
    def __group_id(folder: Folder) -> int | None:
        metafile = GroupMetafile.get(folder)

        if metafile is None:
            return None

        return abs(metafile.group_id)

    def __check_unique_groups(self, candidates: list[tuple[Folder, Group]], photoset: Photoset) -> None:
        group_ids = [self.__group_id(folder) for folder, _ in candidates]
        linked = [group_id for group_id in group_ids if group_id is not None]

        if len(linked) != len(set(linked)):
            raise ValueError(f"Two folders are linked to the same event. {photoset.path}")

    def __target(self, candidates: list[tuple[Folder, Group]], photoset: Photoset) -> tuple[Folder, Group]:
        """The first folder linked to --url, else the first folder with no event yet —
        so a rerun picks up where the previous one stopped."""
        if self.__url:
            event_id = abs(self.context.pyvko.get(self.__url).id)
            linked = first(candidates, key=lambda candidate: self.__group_id(candidate[0]) == event_id)

            if linked is not None:
                return linked

        free = first(candidates, key=lambda candidate: self.__group_id(candidate[0]) is None)

        if free is None:
            raise ValueError(f"No folder left without an event. {photoset.path}")

        return free

    @staticmethod
    def __date_from_name(name: str) -> date:
        """Photosets are named YY.M.D.event_name — the event date comes from there."""
        year, month, day, _ = name.split(".", maxsplit=3)

        return date(int(year) + 2000, int(month), int(day))

    @staticmethod
    def __organiser_id(parent) -> int | None:
        if parent is None:
            return None

        return parent.id

    def __new_browser(self) -> VKBrowser:
        """Creation can run into a captcha, and a human solves it — the window must show."""
        if self.__create:
            return VKBrowser(headless=False)

        return VKBrowser()

    def __setup(self, title: str, event_date: date, parent) -> int:
        start_dt = datetime.combine(event_date, time(hour=12))
        end_dt = start_dt + timedelta(hours=4)
        organiser_id = self.__organiser_id(parent)

        with self.__new_browser() as browser:
            if self.__create:
                event_id = browser.create_event(
                    title=title,
                    start_dt=start_dt,
                    end_dt=end_dt,
                    organiser_id=organiser_id,
                    is_closed=True,
                )

                print(f"Event created: {VK_URL}/event{event_id} (id={event_id})")
            elif self.__url:
                event_id = abs(self.context.pyvko.get(self.__url).id)
            else:
                raise ValueError("Either --create or --url must be specified")

            browser.apply_settings(
                event_id, self._default_settings(title, organiser_id, start_dt, end_dt))

        print(f"Event is ready: {VK_URL}/event{event_id}")

        return event_id

    @staticmethod
    def _default_settings(title: str, organiser_id: int | None, start_dt: datetime, end_dt: datetime) -> EventSettingsSettings:
        return EventSettingsSettings(
            setup=EventSetupSettings(
                title=title,
                start_dt=start_dt,
                end_dt=end_dt,
                category=Category.CIRCUS,
                organiser_id=organiser_id,
                is_closed=True,
            ),
            messages=MessagesSettings(
                enabled=False
            ),
            sections=SectionsConfig(
                posts=PostsSettings(),
                photos=PhotosSettings(),
                videos=VideosSettings(),
                topics=TopicsSettings(enabled=False),
                music=MusicSettings(enabled=False),
                files=FilesSettings(enabled=False),
                materials=MaterialsSettings(enabled=False),
                services=ServicesSettings(enabled=False),
                chats=ChatsSettings(enabled=False),
                clips=ClipsSettings(enabled=False),
                articles=ArticlesSettings(enabled=False),
                moments=MomentsSettings(enabled=False),
                products=ProductsSettings(enabled=False),
                main_section=MainSection.PHOTOS,
            ),
        )


app = Typer()


@app.command()
def setup_event(
    context: Annotated[typer.Context, Argument()],
    pattern: Annotated[Optional[List[Path]], Argument()] = None,
    create: Annotated[bool, typer.Option("--create")] = False,
    url: Annotated[Optional[str], typer.Option("--url")] = None,
    manual: Annotated[bool, typer.Option("--manual")] = False,
    date_: Annotated[Optional[str], typer.Option("--date")] = None,
    title: Annotated[Optional[str], typer.Option("--title")] = None,
    parent: Annotated[Optional[str], typer.Option("--parent")] = None,
) -> None:
    if not create and not url:
        typer.echo("Either --create or --url must be specified", err=True)

        raise typer.Exit(1)

    SetupEventCommand(context.obj, pattern or [Path.cwd()], create, url, manual,
                      date_, title, parent).run()
