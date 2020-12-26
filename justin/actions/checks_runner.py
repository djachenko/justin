from typing import Iterable

from justin_utils.singleton import Singleton

from justin.actions.named.stage.exceptions.check_failed_error import CheckFailedError
from justin.actions.named.stage.logic.base.check import Check
from justin.shared.models.photoset import Photoset


class ChecksRunner(Singleton):
    # noinspection PyMethodMayBeStatic
    def run(self, photoset: Photoset, checks: Iterable[Check]):
        for check in checks:
            print(f"Running {check.name} for {photoset.name}... ", end="")

            result = check.is_good(photoset)

            if result:
                print("passed")
            else:
                print("not passed")

                if check.ask_for_extract():
                    check.extract(photoset)

                raise CheckFailedError(f"Failed {check.name}")
