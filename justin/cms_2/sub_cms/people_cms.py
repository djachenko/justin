from abc import abstractmethod

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase
from justin.cms_2.storage.sqlite.sqlite_entries import Person
from justin_utils.util import first


class PeopleCMS:
    @property
    @abstractmethod
    def db(self) -> SQLiteDatabase:
        pass

    def register_person(self, folder: str, name: str, vk_id: int) -> None:
        person = Person(
            folder=folder,
            name=name,
            vk_id=vk_id
        )

        with self.db.connect():
            self.db.update(person)

    def get_person(self, folder: str) -> Person | None:
        with self.db.connect():
            return first(
                self.db.get_entries(Person),
                lambda p: p.folder == folder
            )

