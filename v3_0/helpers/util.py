from typing import Iterable, TypeVar, Callable


def names_by_extension(entries, extension):
    extension = "." + extension

    return [entry.name.rsplit(".", 1)[0] for entry in entries if entry.name.lower().endswith(extension)]


def names_without_extension(names):
    return [stem(name) for name in names]


def stem(name):
    return name.rsplit(".", 1)[0]


T = TypeVar("T")
V = TypeVar("V")


def split_by_predicates(seq: Iterable[T], *lambdas: Callable[[T], bool]) -> Iterable[Iterable[T]]:
    return list(map(lambda x: list(filter(x, seq)), lambdas))


def ask_for_permission(question: str) -> bool:
    while True:
        answer_input = input(f"{question} y/n ")

        answer_input = answer_input.lower().strip()

        if answer_input in ["y", "n"]:
            answer = answer_input == "y"

            return answer
