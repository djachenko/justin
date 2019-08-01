import time
from typing import Iterable, TypeVar, Callable

T = TypeVar("T")
V = TypeVar("V")


def split_by_predicates(seq: Iterable[T], *lambdas: Callable[[T], bool]) -> Iterable[Iterable[T]]:
    return list(map(lambda x: list(filter(x, seq)), lambdas))


def ask_for_permission(question: str) -> bool:
    time.process_time()

    while True:
        answer_input = input(f"{question} y/n ")

        answer_input = answer_input.lower().strip()

        if answer_input in ["y", "n"]:
            answer = answer_input == "y"

            return answer


def measure_time(name=None):
    if name is None:
        name = "Execution"

    def decorator(func):
        def inner(*args, **kwargs):
            start = time.process_time()

            result = func(*args, **kwargs)

            end = time.process_time()

            passed = end - start

            print(f"{name} took {passed} s.")

            return result

        return inner

    return decorator
