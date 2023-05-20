from typing import Iterable

from justin.actions.stage.logic.base import Check, Problem
from justin.shared.models.photoset import Photoset


class ChecksRunner:
    # noinspection PyMethodMayBeStatic
    def run(self, photoset: Photoset, checks: Iterable[Check]) -> Iterable[Problem]:
        for check in checks:
            check.rollback(photoset)

        for check in checks:
            print(f"Running {check.name} for {photoset.name}... ", end="", flush=True)

            problems = check.get_problems(photoset)

            if not problems:
                print("passed")
            else:
                print("not passed:")

                for problem in problems:
                    print(problem)

                extract_problems = []

                if check.ask_for_extract():
                    extract_problems += check.extract(photoset)

                if extract_problems:
                    print("Extract failed:")

                    for problem in extract_problems:
                        print(problem)

                return problems + extract_problems

        return []
