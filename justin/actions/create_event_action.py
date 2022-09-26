from abc import abstractmethod
from argparse import Namespace
from dataclasses import dataclass
from datetime import date, time, datetime, timedelta
from typing import List

from justin_utils.cli import Action, Context, Parameter
from justin_utils.util import parse_date
from pyvko.entities.user import User
from pyvko.aspects.events import Events, Event
from pyvko.aspects.groups import Group


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

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(name="event_id"),
            Parameter(name="date", type=parse_date),
            Parameter(name="name"),
            Parameter(name="--parent", default=None),
        ]

    @abstractmethod
    def perform(self, args: Namespace, context: Context) -> None:
        event_id = args.event_id
        event = context.pyvko.get(event_id)

        date_: date = args.date
        name: str = args.name
        parent_id: str | None = args.parent

        parent: Group | User | None = None

        if parent_id:
            parent = context.pyvko.get(parent_id)

        SetupEventAction.__setup_event(event, date_, name, parent)

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
