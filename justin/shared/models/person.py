import json
from abc import abstractmethod
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import List, Iterable

from justin.shared.metafile import Json
from justin_utils.util import first
from pyvko.pyvko_main import Pyvko


@dataclass
class Person:
    folder: str
    name: str | None
    vk_id: int | None
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

    def __eq__(self, other):
        return isinstance(other, Person) and other.folder == self.folder

    @staticmethod
    def is_valid(person: 'Person', strict: bool = False) -> bool:
        if strict:
            return bool(person.folder and person.name and person.vk_id)
        else:
            return bool(person.folder)


class PeopleRegistry:
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

    def __contains__(self, name) -> bool:
        for person in self.__people:
            if person.folder == name:
                return True

        return False

    def __iter__(self):
        return iter(self.__people)

    def get_all_folders(self) -> List[str]:
        return [person.folder for person in self.__people]

    def get_by_folder(self, folder: str) -> Person | None:
        for person in self.__people:
            if person.folder == folder:
                return person

        return None

    def update_person(self, person: Person) -> None:
        assert Person.is_valid(person), "Person is invalid."

        try:
            existing_index = self.__people.index(person)

            self.__people[existing_index] = person
        except ValueError:
            collision = self.find_collision(person.folder)

            assert not collision, f"Folder prefixes collision with {collision.folder}"

            for existing_person in self.__people:
                assert person.vk_id is None or person.vk_id != existing_person.vk_id,\
                    f"Vk id {person.vk_id} is already registered"
                assert person.folder != existing_person.folder, "This folder is already registered"

            self.__people.append(person)

        self.save()

    @staticmethod
    def __build_prefixes(string: str, sep: str) -> Iterable[str]:

        prefixes = []

        split = string.split(sep)

        for i in range(1, len(split) + 1):
            prefixes.append(sep.join(split[:i]))

        return prefixes

    def find_collision(self, folder_name: str) -> Person | None:
        return first(self.__people, lambda p: folder_name in self.__build_prefixes(p.folder, "_"))

    def check_availability(self, folder_name: str) -> bool:
        return self.find_collision(folder_name) is None
