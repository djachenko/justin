from datetime import date, time, datetime, timedelta
from pathlib import Path
from typing import Annotated, Iterable, List, Optional

import typer
from justin_utils import util
from justin_utils.filesystem import Folder
from justin_utils.util import parse_date
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
from justin.shared.models.photoset import Photoset
from justin.typer.base_commands.pattern_command import Extra, PatternCommand


class SetupEventCommand(PatternCommand):
    """Создаёт или донастраивает событие VK — по фотосету либо вручную.

    Разбор паттернов, построение фотосета и отсев не-фотосетов делает PatternCommand.
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

        self.create = create
        self.url = url
        self.manual = manual
        self.date = parse_date(date_) if date_ else None
        self.title = title
        self.parent = parent

    def run(self) -> None:
        if self.manual:
            self.__setup(self.__manual_title(), self.__manual_date(), self.__manual_parent())

            return

        super().run()

    def run_for_photoset(self, photoset: Photoset, extra: Extra) -> None:
        parent = self.__photoset_parent(photoset)

        if parent is None:
            print(f"Unable to determine parent. {photoset.path}")

            return

        title = self.title or photoset.name

        self.__setup(title, self.date or self.__date_from_name(photoset.name), parent)

    def __manual_title(self) -> str:
        return self.title or input("Enter event title: ")

    def __manual_date(self) -> date:
        return self.date or parse_date(input("Enter event date: "))

    def __manual_parent(self):
        if self.parent:
            return self.context.pyvko.get(self.parent)

        choice = util.ask_for_choice("Choose event parent:", ["closed", "meeting"])

        if choice == "closed":
            return self.context.closed_group

        if choice == "meeting":
            return self.context.meeting_group

        raise ValueError("Invalid parent")

    def __photoset_parent(self, photoset: Photoset):
        def needs_event(folder: Folder | None) -> bool:
            return folder is not None  # and not GroupMetafile.has(folder)

        if self.parent:
            return self.context.pyvko.get(self.parent)

        if any(needs_event(part.closed) for part in photoset.parts):
            return self.context.closed_group

        if any(needs_event(part.meeting) for part in photoset.parts):
            return self.context.meeting_group

        return None

    @staticmethod
    def __date_from_name(name: str) -> date:
        """Фотосеты названы YY.M.D.event_name — дата события берётся оттуда."""
        year, month, day, _ = name.split(".", maxsplit=3)

        return date(int(year) + 2000, int(month), int(day))

    def __setup(self, title: str, event_date: date, parent) -> None:
        start_dt = datetime.combine(event_date, time(hour=12))
        end_dt = start_dt + timedelta(hours=4)
        organiser_id = parent.id if parent is not None else None

        with VKBrowser() as browser:
            if self.create:
                event_id = browser.create_event(
                    title=title,
                    start_dt=start_dt,
                    end_dt=end_dt,
                    organiser_id=organiser_id,
                    is_closed=True,
                )

                print(f"Event created: https://vk.com/event{event_id} (id={event_id})")
            elif self.url:
                event_id = abs(self.context.pyvko.get(self.url).id)
            else:
                raise ValueError("Either --create or --url must be specified")

            browser.apply_settings(
                event_id, self._default_settings(title, organiser_id, start_dt, end_dt))

        print(f"Event is ready: https://vk.com/event{event_id}")

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


if __name__ == "__main__":
    TEST_EVENT_ID = 239324394

    with VKBrowser() as browser:
        browser.apply_settings(TEST_EVENT_ID, EventSettingsSettings(
            messages=MessagesSettings(enabled=True),
            sections=SectionsConfig(
                posts=PostsSettings(),
                photos=PhotosSettings(),
            ),
        ))

    print(f"Done: https://vk.com/event{TEST_EVENT_ID}")
