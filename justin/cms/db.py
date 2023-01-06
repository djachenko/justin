from abc import abstractmethod
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Type, TypeVar, Any, List, Callable

from justin.shared.helpers.utils import fromdict

T = TypeVar("T", bound="DBEntry")


@dataclass
class DBEntry:
    @classmethod
    @lru_cache()
    def type(cls) -> str:
        return cls.__name__

    @classmethod
    def from_dict(cls: Type[T], csv_dict) -> T:
        return fromdict(csv_dict, cls)

    @property
    @abstractmethod
    def key(self) -> Any:
        pass

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def as_dict(self):
        return asdict(self)


class Database:
    @abstractmethod
    def get(self, type_: Type[T]) -> List[T]:
        pass

    @abstractmethod
    def update(self, *entries: T, comparator: Callable[[T, T], bool] = lambda a, b: a == b) -> None:
        pass
