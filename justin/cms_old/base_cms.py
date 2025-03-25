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

