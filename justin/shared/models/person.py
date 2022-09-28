import json
from abc import abstractmethod
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import List

from justin.shared.filesystem import FolderTree
from justin.shared.metafile import Json
from pyvko.entities.user import User
from pyvko.pyvko_main import Pyvko


@dataclass
class Person:
    folder: str
    name: str
    vk_id: int
    source: str
    register_date: date = date.today()

    @classmethod
    def from_json(cls, json_object: Json) -> 'Person':
        register_date: date | None = None

        if json_object["register_date"]:
            register_date = date.fromisoformat(json_object["register_date"])

        return Person(
            folder=json_object["folder"],
            name=json_object["name"],
            vk_id=json_object["vk_id"],
            source=json_object["source"],
            register_date=register_date
        )

    @abstractmethod
    def as_json(self) -> Json:
        d = asdict(self)

        d["register_date"] = self.register_date.isoformat()

        return d

    @staticmethod
    def is_valid(person: 'Person') -> bool:
        return bool(person.folder and person.name and person.vk_id and person.source)


class PeopleRegister:
    def __init__(self, root: Path, category: str, pyvko: Pyvko | None = None):
        super().__init__()

        self.__people: List[Person] = []
        self.__pyvko: Pyvko = pyvko

        self.__root = root
        self.__category = category

        self.read()

    def __path(self) -> Path:
        return (self.__root / self.__category).with_suffix(".json")

    def read(self) -> None:
        if not self.__path().exists():
            return

        with self.__path().open() as people_json_file:
            people_json = json.load(people_json_file)

            self.__people = [Person.from_json(person_json) for person_json in people_json]

    def save(self) -> None:
        with self.__path().open("w", encoding='utf8') as people_json_file:
            json.dump([person.as_json() for person in self.__people], people_json_file, indent=4, ensure_ascii=False)

    def register(self, folder: Path):
        assert self.__pyvko is not None

        my_people_folder = folder / self.__category

        if not my_people_folder.exists():
            return

        tree = FolderTree(my_people_folder)

        source = folder.name

        for my_person in tree.subtrees:
            if my_person.name in self:
                continue

            url = input(f"Who is {my_person.name}? ")

            if url == "-":
                continue

            user: User = self.__pyvko.get(url)

            assert isinstance(user, User)

            vk_id = user.id
            name = f"{user.first_name} {user.last_name}"

            person = Person(
                vk_id=vk_id,
                name=name,
                folder=my_person.stem,
                source=source,
            )

            self.__register(person)

    def __register(self, person: Person) -> None:
        assert Person.is_valid(person)

        for existing_person in self.__people:
            assert person.vk_id != existing_person.vk_id
            assert person.folder != existing_person.folder

            # todo: prefixes

        self.__people.append(person)

        self.save()

    def __contains__(self, name) -> bool:
        for person in self.__people:
            if person.folder == name:
                return True

        return False

    def get_all_folders(self) -> List[str]:
        return [person.folder for person in self.__people]

    def get_by_folder(self, folder: str) -> Person | None:
        for person in self.__people:
            if person.folder == folder:
                return person

        return None

    def fix_person(self, folder: str) -> None:
        person = self.get_by_folder(folder)
        self.__people.remove(person)

        person.vk_id = input(f"Enter {folder}'s vk_id (current {person.vk_id}):") or person.vk_id
        person.name = input(f"Enter {folder}'s name (current {person.name}):") or person.name

        self.__register(person)
