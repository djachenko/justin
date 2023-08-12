from abc import ABC
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Type

from justin.cms.base_cms import Entry, T, Registry, BaseCMS
from justin.shared.helpers.utils import Json
from justin_utils import util
from justin_utils.util import distinct, get_prefixes
from pyvko.aspects.groups import Group
from pyvko.entities.user import User
from pyvko.pyvko_main import Pyvko


@dataclass
class PersonEntry(Entry):
    folder: str
    name: str
    vk_id: int
    source: str
    register_date: date = date.today()

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        entry = super().from_json(json_object)

        entry.register_date = date.fromisoformat(json_object["register_date"])

        return entry

    def as_json(self) -> Json:
        json_object = super().as_json()

        json_object["register_date"] = self.register_date.isoformat()

        return json_object

    @staticmethod
    def is_valid(person: 'PersonEntry', strict: bool = False) -> bool:
        if strict:
            return bool(person.folder and person.name and person.vk_id)
        else:
            return bool(person.folder)


@dataclass
class PersonMigrationEntry(Entry):
    src: str
    dst: str


class FixPeopleMixin:
    @staticmethod
    def __fix_vk_id(person: PersonEntry, pyvko: Pyvko) -> PersonEntry | None:
        abort = None
        empty = ""

        options = []

        if person.vk_id is not None:
            options.insert(0, str(person.vk_id))

        choice = util.ask_for_choice_flagged(f"Who is {person.folder} in vk?", options)

        if choice == abort:
            return None
        elif choice == empty:
            person.vk_id = None
        else:
            user: User | Group = pyvko.get(choice)

            vk_id = user.id

            person.vk_id = vk_id

        return person

    @staticmethod
    def __fix_name(person: PersonEntry, pyvko: Pyvko) -> PersonEntry | None:
        if person.vk_id:
            user: User | Group = pyvko.get(person.vk_id)

            if isinstance(user, User):
                vk_name = f"{user.first_name} {user.last_name}"
            elif isinstance(user, Group):
                vk_name = user.name
            else:
                assert False
        else:
            vk_name = None

        existing_name = person.name
        abort = "abort"
        empty = "empty"

        options = [i for i in [vk_name, existing_name, abort, empty, ] if i]

        choice = util.ask_for_choice_with_other(f"What is {person.folder}'s name?", options)

        if choice == abort:
            return None
        elif choice == empty:
            person.name = None
        else:
            person.name = choice

        return person

    @staticmethod
    def __fix_source(person: PersonEntry) -> PersonEntry | None:
        cwd = Path.cwd().name

        abort = "abort"
        empty = "empty"

        options = distinct([i for i in [person.source, cwd, ] if i]) + [abort, empty, ]

        choice = util.ask_for_choice_with_other(f"Where is {person.folder} from?", options)

        if choice == abort:
            return None
        elif choice == empty:
            person.source = None
        else:
            person.source = choice

        return person

    @staticmethod
    def fix_person(person: PersonEntry, pyvko: Pyvko) -> PersonEntry | None:
        assert person.folder is not None

        person = FixPeopleMixin.__fix_vk_id(person, pyvko)

        if person is None:
            return None

        person = FixPeopleMixin.__fix_name(person, pyvko)

        if person is None:
            return None

        person = FixPeopleMixin.__fix_source(person)

        return person


class PeopleRegistry(Registry[PersonEntry, str]):
    def __init__(self, path: Path):
        super().__init__(path, PersonEntry, lambda x: x.folder)

    # prefix_postfix
    #

    def validate(self, entry: PersonEntry) -> bool:
        for person in self:
            if entry.folder in get_prefixes(person.folder, "_") or person.folder in get_prefixes(entry.folder, "_"):
                print(f"{entry.folder} collides with {person.folder}")

                return False

        return True

    def get_all_folders(self):
        return [person.folder for person in self]


class PeopleCMS(BaseCMS, ABC, FixPeopleMixin):
    @property
    @lru_cache()
    def people(self) -> Registry[PersonEntry, str]:
        return PeopleRegistry(self.root / "people.json")

    @property
    @lru_cache()
    def people_migrations(self) -> Registry[PersonMigrationEntry, str]:
        return Registry(self.root / "people_migrations.json", PersonMigrationEntry, lambda x: x.src)

    def register_person(self, path: Path, source: str, pyvko: Pyvko) -> None:
        if path.name.startswith("unknown"):
            return

        print(f"{path.name} {path.name in self.people}")

        if path.name in self.people:
            return

        entry = PersonEntry(
            folder=path.name,
            name=None,
            vk_id=None,
            source=source
        )

        entry = self.fix_person(entry, pyvko)

        if entry is None:
            return

        self.people.update(entry)
        self.people.save()

    def migrate_person(self, src: str, dst: str) -> None:
        assert src in self.people

        person = self.people.get(src)

        self.people.remove(src)

        person.folder = dst

        self.people.update(person)
        self.people.save()

        migration = PersonMigrationEntry(
            src=src,
            dst=dst
        )

        self.people_migrations.update(migration)
        self.people_migrations.save()

