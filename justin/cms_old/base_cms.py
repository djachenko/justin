import json
from abc import abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Type, TypeVar, Generic, List, Callable, Hashable

from justin.shared.helpers.utils import fromdict, Json

T = TypeVar('T')


@dataclass
class Entry:
    @classmethod
    def from_dict(cls: Type[T], json_object: Json) -> T:
        return fromdict(json_object, cls)

    def as_dict(self) -> Json:
        return asdict(self)


E = TypeVar("E", bound=Entry)
K = TypeVar("K", bound=Hashable)


class Table_old(Generic[E, K]):
    __ENTRIES_KEY = "entries"

    def __init__(self, path: Path, type_: Type[E], key: Callable[[E], K] = None):
        self.__path = path
        self.__type = type_

        if key is None:
            key = lambda x: x

        self.key = key

        self.__entries = []

        self.read()

    @property
    def entries(self) -> List[E]:
        return self.__entries

    def validate(self, entry: E) -> bool:
        return True

    def __contains__(self, key: K) -> bool:
        for entry in self:
            if key == self.key(entry):
                return True

        return False

    def get(self, key: K) -> E | None:
        for entry in self:
            if self.key(entry) == key:
                return entry

        return None

    def __iter__(self):
        return iter(self.__entries)

    def read(self) -> None:
        if not self.__path.exists():
            return

        with self.__path.open() as entries_json_file:
            entries_json = json.load(entries_json_file)

            self.__entries = [self.__type.from_dict(person_json) for person_json in
                              entries_json[Table.__ENTRIES_KEY]]

    def save(self) -> None:
        self.__path.parent.mkdir(parents=True, exist_ok=True)

        if self.__path.exists():
            with self.__path.open() as entries_json_file:
                entries_json = json.load(entries_json_file)
        else:
            entries_json = {}

        entries_json[Table.__ENTRIES_KEY] = [entry.as_dict() for entry in self.__entries]

        with self.__path.open("w", encoding='utf8') as entries_json_file:
            json.dump(entries_json, entries_json_file, indent=4, ensure_ascii=False)
