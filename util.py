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


def join(selector, *sequences):
    enumerated_sequences = enumerate(sequences)

    merges = {}

    for sequence_number, sequence in enumerated_sequences:
        for item in sequence:
            key = selector(item)

            if key not in merges:
                merges[key] = {}

            merges[key][sequence_number] = item

    results = []

    for merge in merges.values():
        merge_list = [merge.get(i, None) for i in range(len(sequences))]

        results.append(merge_list)

    return results


T = TypeVar("T")
V = TypeVar("V")


def full_outer_join(seq1: Iterable[T], seq2: Iterable[V], sel1: Callable[[T], object],
                    sel2: Callable[[V], object] = None) -> Iterable[Tuple[T, V]]:
    if sel2 is None:
        sel2 = sel1

    sequences = [seq1, seq2]
    selectors = [sel1, sel2]
    indices = range(len(sequences))

    seq_sel_mapping = zip(indices, sequences, selectors)
    merges = {}

    for index, sequence, selector in seq_sel_mapping:
        for item in sequence:
            key = selector(item)

            if key not in merges:
                merges[key] = {index: [] for index in indices}

            merges[key][index].append(item)

    permutations = []

    for combination in merges.values():
        factors = combination.values()

        non_null_factors = []

        for factor in factors:
            if len(factor) == 0:
                non_null_factors.append([None])
            else:
                non_null_factors.append(factor)

        permutation = list(itertools.product(*non_null_factors))

        permutations.append(permutation)

    results = []

    for permutation in permutations:
        results += permutation

    return results


def inner_join(seq1: Iterable[T], seq2: Iterable[V], sel1: Callable[[T], object], sel2: Callable[[V], object] = None) \
        -> Iterable[Tuple[T, V]]:
    full_join = full_outer_join(seq1, seq2, sel1, sel2)

    inner = [i for i in full_join if all(i)]

    return inner


def left_join(seq1: Iterable[T], seq2: Iterable[V], sel1: Callable[[T], object], sel2: Callable[[V], object] = None) \
        -> Iterable[Tuple[T, V]]:
    full_join = full_outer_join(seq1, seq2, sel1, sel2)

    inner = [i for i in full_join if i[0]]

    return inner


def right_join(seq1: Iterable[T], seq2: Iterable[V], sel1: Callable[[T], object], sel2: Callable[[V], object] = None) \
        -> Iterable[Tuple[T, V]]:
    full_join = full_outer_join(seq1, seq2, sel1, sel2)

    inner = [i for i in full_join if i[1]]

    return inner


def split_by_predicates(seq: Iterable[T], *lambdas: Callable[[T], bool]) -> Iterable[Iterable[T]]:
    return list(map(lambda x: list(filter(x, seq)), lambdas))
