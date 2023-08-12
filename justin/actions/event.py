from abc import abstractmethod
from argparse import Namespace, ArgumentParser
from dataclasses import dataclass
from datetime import date, time, datetime, timedelta
from typing import List

from justin.shared.context import Context
from justin.shared.metafile import MetaFolder, GroupMetafile
from justin.shared.models.photoset import Photoset
from justin_utils import util
from justin_utils.cli import Action, Parameter
from justin_utils.util import parse_date
from pyvko.aspects.events import Events, Event
from pyvko.aspects.groups import Group
from pyvko.entities.user import User


class CreateEventAction(Action):
    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(name="name"),
        ]

    def perform(self, args: Namespace, context: Context) -> Event:
        name = args.name

        # todo: split meeting and closed

        return CreateEventAction.__create_event(context.meeting_group, name)

    @staticmethod
    def __create_event(community: Events, name: str) -> Event:
        return community.create_event(name)


class SetupEventAction(Action):
    @dataclass
    class EventParams:
        destination: str
        event_name: str
        event_date: date
        owner: Events
        category: str | None = None

    def configure_subparser(self, subparser: ArgumentParser) -> None:
        action_group = subparser.add_mutually_exclusive_group(required=True)

        action_group.add_argument("--create", action="store_true")
        action_group.add_argument("--url")

        parameters_group = subparser.add_mutually_exclusive_group(required=True)

        parameters_group.add_argument("--manual", action="store_true")
        parameters_group.add_argument("--folder")

        super().configure_subparser(subparser)

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(name="--date", type=parse_date),
            Parameter(name="--title"),
            Parameter(name="--parent", default=None),
        ]

    @abstractmethod
    def perform(self, args: Namespace, context: Context) -> None:
        if args.manual:
            event_title = args.title or input("Enter event title: ")
            event_date = args.date or parse_date(input("Enter event date: "))

            if args.parent:
                event_parent = context.pyvko.get(args.parent)
            else:
                parent = util.ask_for_choice("Choose event parent:", [
                    "closed",
                    "meeting",
                ])

                if parent == "closed":
                    event_parent = context.closed_group
                elif parent == "meeting":
                    event_parent = context.meeting_group
                else:
                    assert False

        elif args.folder:
            paths = list(util.resolve_patterns(args.folder))

            assert len(paths) == 1

            path = paths[0]

            photoset = Photoset.from_path(path)

            def needs_event(folder: MetaFolder | None) -> bool:
                return folder is not None and not folder.has_metafile(GroupMetafile)

            if args.parent:
                event_parent = context.pyvko.get(args.parent)
            elif any(needs_event(part.closed) for part in photoset.parts):
                event_parent = context.closed_group
            elif any(needs_event(part.meeting) for part in photoset.parts):
                event_parent = context.meeting_group
            else:
                print(f"Unable to determine parent. {photoset.path}")

                return

            event_title = args.title or photoset.name

            year, month, day, _ = event_title.split(".", maxsplit=3)

            event_date = args.date or date(int(year) + 2000, int(month), int(day))

        else:
            assert False

        if args.create:
            event = context.pyvko.create_event(event_title)
        elif args.url:
            event = context.pyvko.get(args.url)
        else:
            assert False

        SetupEventAction.__setup_event(event, event_date, event_title, event_parent)

        print(f"Event is ready: {event.browser_url}")

    @staticmethod
    def __setup_event(event: Event, date_: date, name: str, parent: Group | User | None):
        event.name = name
        event.event_category = Event.Category.CIRCUS

        if parent:
            event.organiser = parent.id

        event.start_date = datetime.combine(date_, time(hour=12))
        event.end_date = event.start_date + timedelta(hours=4)

        for section in Event.Section:
            event.set_section_state(section, Event.SectionState.DISABLED)

        event.set_section_state(Event.Section.PHOTOS, Event.SectionState.LIMITED)
        event.set_section_state(Event.Section.WALL, Event.SectionState.LIMITED)
        event.set_section_state(Event.Section.MESSAGES, Event.SectionState.ENABLED)

        event.is_closed = True

        event.main_section = Event.Section.PHOTOS

        event.save()
