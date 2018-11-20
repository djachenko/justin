from abc import abstractmethod
from pathlib import Path
from typing import Iterable

from v3_0.logic.check import Check
from v3_0.logic.filter import Filter
from v3_0.models.photoset import Photoset


class Stage:
    def __init__(
            self,
            path: Path,
            command: str = None,
            incoming_checks: Iterable[Check] = None,
            outcoming_checks: Iterable[Check] = None,
            preparation_hooks: Iterable[Filter] = None
    ):
        if incoming_checks is None:
            incoming_checks = []

        if outcoming_checks is None:
            outcoming_checks = []

        if preparation_hooks is None:
            preparation_hooks = []

        self.__name = path.stem
        self.__folder = path.name
        self.__path = path
        self.__command = command
        self.__incoming_checks = incoming_checks
        self.__outcoming_checks = outcoming_checks
        self.__preparation_hooks = preparation_hooks

    @property
    def folder(self) -> str:
        return self.__folder

    @property
    def path(self) -> Path:
        return self.__path

    @property
    def command(self) -> str:
        return self.__command

    @staticmethod
    def __run_checks(photoset: Photoset, checks: Iterable[Check]) -> bool:
        for check in checks:
            print(f"Running {check.name} for {photoset.name}... ", end="")

            result = check.check(photoset)

            if not result:
                print("not passed")

                if check.hookable:
                    while True:
                        answer_input = input("Extract not passed files? y/n")

                        answer_input = answer_input.lower()

                        if answer_input in ["y", "n"]:
                            answer = answer_input == "y"

                            break

                    if answer:
                        check.extract(photoset)

                return False
            else:
                print("passed")

        return True

    def able_to_come_out(self, photoset: Photoset) -> bool:
        print("Running outcoming checks")
        return self.__run_checks(photoset, self.__outcoming_checks)

    def able_to_come_in(self, photoset: Photoset) -> bool:
        print("Running incoming checks")
        return self.__run_checks(photoset, self.__incoming_checks)

    def prepare(self, photoset: Photoset):
        for hook in self.__preparation_hooks:
            hook.forward(photoset)

    def cleanup(self, photoset: Photoset):
        for hook in self.__preparation_hooks:
            hook.backwards(photoset)

    def transfer(self, photoset: Photoset):
        photoset.move(self.__path)
