"""Each-choice sets for parametrizing live tests."""
from itertools import cycle
from typing import Any


def each_choice(*options: list[Any]) -> list[tuple]:
    """A set where every value of every field appears at least once.

    A cartesian product checks combinations, while browser tests need values: each value
    is a separate selector on the page. The set is as long as the longest list, shorter
    ones are cycled. 2 x 3 x 2 = 12 collapses into 3.

    This is each-choice coverage, not pairwise: pairs of values are not guaranteed.

    The order inside a tuple is the order of the arguments; argnames must match it.
    """
    if not options or any(not values for values in options):
        raise ValueError("each_choice needs a non-empty list per field")

    length = max(len(values) for values in options)
    wheels = [cycle(values) for values in options]

    return [tuple(next(wheel) for wheel in wheels) for _ in range(length)]
