from datetime import date, time, datetime, timedelta
from typing import Annotated, Optional

import typer
from justin_utils import util
from justin_utils.util import parse_date
from typer import Typer, Argument

from justin.browser.vk_browser import VKBrowser
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.metafiles.metafile import GroupMetafile
from justin.shared.models.photoset import Photoset


class SetupEventCommand:
    def __init__(
        self,
        context: Context,
        create: bool = False,
        url: Optional[str] = None,
        manual: bool = False,
        folder: Optional[str] = None,
        date_: str | None = None,
        title: Optional[str] = None,
        parent: Optional[str] = None,
    ):
        if date_:
            date_ = parse_date(date_)

        self.context = context
        self.create = create
        self.url = url
        self.manual = manual
        self.folder = folder
        self.date_ = date_
        self.title = title
        self.parent = parent

    def run(self) -> None:
        if self.manual:
            event_title = self.title or input("Enter event title: ")
            event_date = self.date_ or parse_date(input("Enter event date: "))

            if self.parent:
                event_parent = self.context.pyvko.get(self.parent)
            else:
                parent = util.ask_for_choice("Choose event parent:", ["closed", "meeting"])

                if parent == "closed":
                    event_parent = self.context.closed_group
                elif parent == "meeting":
                    event_parent = self.context.meeting_group
                else:
                    raise ValueError("Invalid parent")

        elif self.folder:
            paths = list(util.resolve_patterns(self.folder))

            if len(paths) != 1:
                raise ValueError("Folder pattern must match exactly one path")

            path = paths[0]
            photoset = Photoset.from_path(path)

            def needs_event(folder: Folder | None) -> bool:
                return folder is not None and not GroupMetafile.has(folder)

            if self.parent:
                event_parent = self.context.pyvko.get(self.parent)
            elif any(needs_event(part.closed) for part in photoset.parts):
                event_parent = self.context.closed_group
            elif any(needs_event(part.meeting) for part in photoset.parts):
                event_parent = self.context.meeting_group
            else:
                print(f"Unable to determine parent. {photoset.path}")
                return

            event_title = self.title or photoset.name

            year, month, day, _ = event_title.split(".", maxsplit=3)

            event_date = self.date_ or date(int(year) + 2000, int(month), int(day))

        else:
            raise ValueError("Either --manual or --folder must be specified")

        start_dt = datetime.combine(event_date, time(hour=12))
        end_dt = start_dt + timedelta(hours=4)

        organiser_id = event_parent.id if event_parent is not None else None

        with VKBrowser() as browser:
            if self.create:
                event_id = browser.create_event(
                    title=event_title,
                    start_dt=start_dt,
                    end_dt=end_dt,
                    organiser_id=organiser_id,
                    is_closed=True,
                )
            elif self.url:
                event = self.context.pyvko.get(self.url)
                event_id = abs(event.id)
            else:
                raise ValueError("Either --create or --url must be specified")

            self.context.pyvko.new_api.groups.setSettings(
                group_id=event_id,
                messages=1,
            )

            # Set sections: wall=LIMITED, main_section=PHOTOS
            browser.set_sections(event_id)

        print(f"Event is ready: https://vk.com/event{event_id}")


app = Typer()


@app.command()
def setup_event(
    context: Annotated[typer.Context, Argument()],
    create: Annotated[bool, typer.Option("--create")] = False,
    url: Annotated[Optional[str], typer.Option("--url")] = None,
    manual: Annotated[bool, typer.Option("--manual")] = False,
    folder: Annotated[Optional[str], typer.Option("--folder")] = None,
    date_: Annotated[str | None, typer.Option("--date")] = None,
    title: Annotated[Optional[str], typer.Option("--title")] = None,
    parent: Annotated[Optional[str], typer.Option("--parent")] = None,
) -> None:
    if not create and not url:
        typer.echo("Either --create or --url must be specified", err=True)
        raise typer.Exit(1)

    if not manual and not folder:
        typer.echo("Either --manual or --folder must be specified", err=True)
        raise typer.Exit(1)

    SetupEventCommand(context.obj, create, url, manual, folder, date_, title, parent).run()
