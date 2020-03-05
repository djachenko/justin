from typing import Iterable

from v3_0.actions.named.stage.exceptions.check_failed_error import CheckFailedError
from v3_0.actions.named.stage.logic.base.check import Check
from v3_0.shared.helpers.singleton import Singleton
from v3_0.shared.models.photoset import Photoset


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
