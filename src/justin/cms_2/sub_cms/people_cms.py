from abc import abstractmethod
from typing import List

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase
from justin.cms_2.storage.sqlite.sqlite_entries import Person
from justin_utils.util import first


class PeopleCMS:
    @property
    @abstractmethod
    def db(self) -> SQLiteDatabase:
        pass

    def register_person(self, folder: str, name: str, vk_id: int | None) -> None:
        person = Person(
            folder=folder,
            name=name,
            vk_id=vk_id
        )

        with self.db.connect():
            self.db.update(person)

    def get_person(self, folder: str) -> Person | None:
        return first(
            self.__get_all_people(),
            lambda p: p.folder == folder
        )

    def get_all_folders(self) -> List[str]:
        return [entry.folder for entry in self.__get_all_people()]

    def __get_all_people(self) -> List[Person]:
        with self.db.connect():
            return self.db.get_entries(Person)

