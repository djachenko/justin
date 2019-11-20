import glob
import time
from pathlib import Path
from typing import Iterable, TypeVar, Callable, Dict, Any, List, Generator

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


def ask_for_choice(question: str, options: List[Path]) -> Path:
    print(question)

    for index, option in enumerate(options):
        print(f"{index}. {option}")

    while True:
        answer = input("Enter chosen index: ")

        try:
            option_index = int(answer)

            if 0 <= option_index < len(options):
                return options[option_index]

        except ValueError:
            pass


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


def concat_dictionaries(*dictionaries: Dict[T, Any]) -> Dict[T, Any]:
    result = {}

    for dictionary in dictionaries:
        keys = dictionary.keys()

        assert len(set(keys).intersection(result.keys())) == 0

        result.update(dictionary)

    return result


def resolve_patterns(patterns: List[str]) -> Generator[Path, None, None]:
    for pattern in patterns:
        for str_path in glob.iglob(pattern):
            path = Path(str_path).absolute()

            yield path
