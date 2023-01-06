from typing import Iterable

from justin_utils.singleton import Singleton

from justin.actions.stage.exceptions.check_failed_error import CheckFailedError
from justin.actions.stage.logic.base import Check, Problem
from justin.shared.models.photoset import Photoset


class ChecksRunner(Singleton):
    # noinspection PyMethodMayBeStatic
    def run_except(self, photoset: Photoset, checks: Iterable[Check]) -> None:
        for check in checks:
            check.rollback(photoset)

        for check in checks:
            print(f"Running {check.name} for {photoset.name}... ", end="")

            problems = check.get_problems(photoset)

            if not problems:
                print("passed")
            else:
                print("not passed")

                for problem in problems:
                    print(problem)

                if check.ask_for_extract():
                    check.extract(photoset)

                # todo: remove controlling flow with exception
                raise CheckFailedError(f"Failed {check.name}")

    # noinspection PyMethodMayBeStatic
    def run(self, photoset: Photoset, checks: Iterable[Check]) -> Iterable[Problem]:
        for check in checks:
            check.rollback(photoset)

        for check in checks:
            print(f"Running {check.name} for {photoset.name}... ", end="")

            problems = check.get_problems(photoset)

            if not problems:
                print("passed")
            else:
                print("not passed")

                for problem in problems:
                    print(problem)

                if check.ask_for_extract():
                    problems += check.extract(photoset)

                return problems

        return []
