from abc import abstractmethod
from dataclasses import asdict, dataclass
from typing import TypeVar, Generic, List, Callable, Hashable, Type

from justin.shared.helpers.utils import fromdict, Json

T = TypeVar("T")


@dataclass
class Entry:
    @classmethod
    def from_dict(cls: Type[T], json_object: Json) -> T:
        return fromdict(json_object, cls)

    def as_dict(self) -> Json:
        return asdict(self)


E = TypeVar("E", bound=Entry)
K = TypeVar("K", bound=Hashable)


class Table(Generic[E, K]):
    def __init__(self, type_: Type[E], key: Callable[[E], K] = None):
        super().__init__()

        if key is None:
            key = lambda x: x

        self.key = key
        self.type = type_

        self.entries: List[E] = []

    def update(self, entry: E) -> None:
        entry_key = self.key(entry)

        for i, e in enumerate(self.entries):
            if self.key(e) == entry_key:
                self.entries[i] = entry

                return

        self.entries.append(entry)

    def get(self, key: K) -> E | None:
        for entry in self:
            if self.key(entry) == key:
                return entry

        return None

    def remove(self, key: K) -> None:
        for entry in self:
            if key == self.key(entry):
                self.entries.remove(entry)

                return

    def __iter__(self):
        return iter(self.entries)

    @abstractmethod
    def load(self) -> None:
        pass

    @abstractmethod
    def save(self) -> None:
        pass
