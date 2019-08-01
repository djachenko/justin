from abc import ABC
from functools import lru_cache
from typing import TypeVar, Type

T = TypeVar('T', bound='Singleton')


class Singleton(ABC):
    @classmethod
    @lru_cache()
    def instance(cls: Type[T]) -> T:
        return cls()
