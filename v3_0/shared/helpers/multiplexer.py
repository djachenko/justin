from typing import Iterable

from v3_0.shared.helpers import util


class Multiplexable:
    def __call__(self, *args, **kwargs):
        pass


class Multiplexer:
    def __init__(self, items: Iterable[Multiplexable]) -> None:
        super().__init__()

        assert util.all_same_type(items)
        assert all(isinstance(item, Multiplexable) for item in items) or all(callable(item) for item in items)

        self.__items = items

    def __getattr__(self, name):
        children = [getattr(item, name) for item in self.__items]

        return Multiplexer.__build_from_items(children)

    @staticmethod
    def __build_from_items(items: Iterable):
        items = [item for item in items if item is not None]

        if not items:
            return None

        if all(map(util.is_iterable, items)):
            return util.flatten(items)
        elif all(isinstance(item, Multiplexable) for item in items) or \
                all(callable(item) for item in items):
            return Multiplexer(items)
        elif util.same(items):
            return next(iter(items))

        return None

    def __call__(self, *args, **kwargs):
        assert all(callable(item) for item in self.__items)

        results = [item(*args, **kwargs) for item in self.__items]

        return Multiplexer.__build_from_items(results)
