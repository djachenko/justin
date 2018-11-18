from typing import List, Iterable, TypeVar, Callable, Tuple

import itertools


def names_by_extension(entries, extension):
    extension = "." + extension

    return [entry.name.rsplit(".", 1)[0] for entry in entries if entry.name.lower().endswith(extension)]


def names_without_extension(names):
    return [name_without_extension(name) for name in names]


def name_without_extension(name):
    return name.rsplit(".", 1)[0]


def map_names(seq1, seq2):
    x = zip(seq1, names_without_extension(seq1))
    y = zip(seq2, names_without_extension(seq2))

    res = []

    for i in x:
        for j in y:
            if i[1] == j[1]:
                res.append((i[0], j[0]))

                break

        res.append((i[0], None))

    return res


T = TypeVar("T")
V = TypeVar("V")


def inner_join(seq1: Iterable[T], seq2: Iterable[V], sel1: Callable[[T], object], sel2: Callable[[V], object] = None) \
        -> Iterable[Tuple[T, V]]:
    print("USE JOINS")

    assert False


def left_join(seq1: Iterable[T], seq2: Iterable[V], sel1: Callable[[T], object], sel2: Callable[[V], object] = None) \
        -> Iterable[Tuple[T, V]]:
    print("USE JOINS")

    assert False


def right_join(seq1: Iterable[T], seq2: Iterable[V], sel1: Callable[[T], object], sel2: Callable[[V], object] = None) \
        -> Iterable[Tuple[T, V]]:
    print("USE JOINS")

    assert False


def split_by_predicates(seq: Iterable[T], *lambdas: Callable[[T], bool]) -> Iterable[Iterable[T]]:
    return list(map(lambda x: list(filter(x, seq)), lambdas))
