from pathlib import Path
from typing import List, Iterable

from v3_0.actions.stage.logic.base.check import Check
from v3_0.actions.stage.logic.base.extractor import Extractor
from v3_0.shared.models.photoset import Photoset


class Stage:
    def __init__(
            self,
            path: Path,
            command: str = None,
            incoming_checks: List[Check] = None,
            outcoming_checks: List[Check] = None,
            preparation_hooks: List[Extractor] = None
    ):
        if incoming_checks is None:
            incoming_checks = []

        if outcoming_checks is None:
            outcoming_checks = []

        if preparation_hooks is None:
            preparation_hooks = []

        self.__path = Path("..") / path
        self.__command = command
        self.__incoming_checks = incoming_checks
        self.__outcoming_checks = outcoming_checks
        self.__preparation_hooks = preparation_hooks

    @property
    def name(self):
        return self.__path.suffix.strip(".")

    @property
    def folder(self) -> str:
        return self.__path.name

    @property
    def command(self) -> str:
        return self.__command

    @property
    def incoming_checks(self) -> List[Check]:
        return self.__incoming_checks

    @property
    def outcoming_checks(self) -> List[Check]:
        return self.__outcoming_checks

    def __str__(self) -> str:
        return "Stage: " + self.name

    @staticmethod
    def __run_checks(photoset: Photoset, checks: Iterable[Check]) -> bool:
        for check in checks:
            print(f"Running {check.name} for {photoset.name}... ", end="")

            result = check.is_good(photoset)

            if result:
                print("passed")
            else:
                print("not passed")

                if check.ask_for_extract():
                    check.extract(photoset)

                return False

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
        photoset.move(photoset.path.parent / self.__path)
