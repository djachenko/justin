import json
from abc import abstractmethod
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import List

from justin.shared.metafile import Json
from justin_utils.util import flatten
from pyvko.entities.user import User
from pyvko.pyvko_main import Pyvko


@dataclass
class Person:
    vk_id: int
    name: str
    folder: str
    source: str
    register_date: date = date.today()

    @classmethod
    def from_json(cls, json_object: Json) -> 'Person':
        return Person(
            vk_id=json_object["vk_id"],
            name=json_object["name"],
            folder=json_object["folder"],
            source=json_object["source"],
            register_date=date.fromisoformat(json_object["date"])
        )

    @abstractmethod
    def as_json(self) -> Json:
        d = asdict(self)

        d["date"] = self.register_date.isoformat()

        return d


class PeopleRegister:

    def __init__(self, root: Path, category: str, pyvko: Pyvko):
        super().__init__()

        self.people = []
        self.pyvko: Pyvko = pyvko

        self.__root = root
        self.__category = category

    def __path(self) -> Path:
        return (self.__root / self.__category).with_suffix(".json")

    def read(self) -> None:
        if not self.__path().exists():
            return

        with self.__path().open() as people_json_file:
            people_json = json.load(people_json_file)

            self.people = [Person.from_json(person_json) for person_json in people_json]

    def save(self) -> None:
        with self.__path().open("w") as people_json_file:
            json.dump([person.as_json() for person in self.people], people_json_file, indent=4)

    def register(self, folder: Path):
        my_people_folder = folder / self.__category
        existing_names = {person.folder for person in self.people}

        source = folder.stem

        for my_person in my_people_folder.iterdir():
            if my_person.name in existing_names:
                continue

            url = input(f"Who is {my_person}? ")

            user: User = self.pyvko.get(url)

            assert user is User

            vk_id = user.id
            name = f"{user.first_name} {user.last_name}"

            person = Person(
                vk_id=vk_id,
                name=name,
                folder=my_person.stem,
                source=source,
            )

            self.people.append(person)

        self.save()

    def __contains__(self, item: Path) -> bool:
        for person in self.people:
            if person.folder == item.name:
                return True

        return False
