import itertools
from typing import Callable, Iterable, Tuple, TypeVar, List

T = TypeVar("T")
V = TypeVar("V")


def full_outer(seq1: Iterable[T], seq2: Iterable[V], on: Callable[[T, V], bool]) -> List[Tuple[T, V]]:
    sequences = [seq1, seq2]

    inclusion_mapping = [{e: False for e in seq} for seq in [seq1, seq2]]

    result = itertools.product(*sequences)

    def unwrapper(t):
        return on(*t)

    result = list(filter(unwrapper, result))

    for joining in result:
        for i, element in enumerate(joining):
            inclusion_mapping[i][element] = True

    for i in range(len(sequences)):
        for element, state in inclusion_mapping[i].items():
            if not state:
                pre_tuple = [None for _ in sequences]

                pre_tuple[i] = element

                joining = tuple(pre_tuple)

                result.append(joining)

    # noinspection PyTypeChecker
    return result


def inner(seq1: Iterable[T], seq2: Iterable[V], on: Callable[[T, V], bool]) -> Iterable[Tuple[T, V]]:
    full_join = full_outer(seq1, seq2, on)

    result = [i for i in full_join if all(i)]

    return result


def left(seq1: Iterable[T], seq2: Iterable[V], on: Callable[[T, V], bool]) -> Iterable[Tuple[T, V]]:
    full_join = full_outer(seq1, seq2, on)

    result = [i for i in full_join if i[0]]

    return result


def right(seq1: Iterable[T], seq2: Iterable[V], on: Callable[[T, V], bool]) -> Iterable[Tuple[T, V]]:
    full_join = full_outer(seq1, seq2, on)

    result = [i for i in full_join if i[1]]

    return result
