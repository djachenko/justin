from typing import Iterable, List

import structure
from logic.photoset.checks.base_check import BaseCheck
from logic.photoset.checks.metadata_check import MetadataCheck
from logic.photoset.checks.readiness_check import ReadinessCheck
from logic.photoset.checks.unselected_check import UnselectedCheck
from logic.photoset.checks.odd_selection_check import OddSelectionCheck
from logic.photoset.filters.base_filter import BaseFilter
from logic.photoset.filters.edited_filter import EditedFilter
from models.disk import Disk
from models.photoset import Photoset

__incoming_checks_key = "incoming_checks"
__outcoming_checks_key = "outcoming_checks"
__preparation_hooks_key = "preparation_hooks"


class Stage:
    def __init__(
            self,
            name: str,
            folder: str,
            path: List[str],
            command: str = None,
            incoming_checks: Iterable[BaseCheck] = None,
            outcoming_checks: Iterable[BaseCheck] = None,
            preparation_hooks: Iterable[BaseFilter] = None
    ):
        if incoming_checks is None:
            incoming_checks = []

        if outcoming_checks is None:
            outcoming_checks = []

        if preparation_hooks is None:
            preparation_hooks = []

        if command is None:
            command = name

        self.__path = path
        self.__command = command
        self.__folder = folder
        self.__incoming_checks = incoming_checks
        self.__outcoming_checks = outcoming_checks
        self.__preparation_hooks = preparation_hooks

        self.__name = name

    @property
    def name(self) -> str:
        return self.__name

    @property
    def folder(self) -> str:
        return self.__folder

    @property
    def path(self) -> List[str]:
        assert False

    @property
    def command(self) -> str:
        return self.__command

    @staticmethod
    def __run_checks(photoset: Photoset, checks: Iterable[BaseCheck]) -> bool:
        checks_results = [check.check(photoset) for check in checks]
        checks_passed = all(checks_results)

        return checks_passed

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

    def transfer(self, photoset: Photoset, disk: Disk):
        new_path = disk.photos_path.append_component(*self.__path)

        photoset.move(new_path)


__premapping = {
    "gif": {},
    "recapture": {},
    "filter": {},
    "develop": {
        __outcoming_checks_key: [
            UnselectedCheck(),
            MetadataCheck(),
        ]
    },

    "ourate": {
        __outcoming_checks_key: [
            UnselectedCheck(),
            MetadataCheck(),
        ],
        __preparation_hooks_key: [EditedFilter()]
    },
    "ready": {
        __incoming_checks_key: [
            OddSelectionCheck(),
            UnselectedCheck(),
            ReadinessCheck(),
            # no service folders
            # gifs has been created
        ],
        __preparation_hooks_key: [
            # instagram
            # sandbox
        ]
    },

    "published": {
        __preparation_hooks_key: [
            # ask whether want to publish
        ],
        __incoming_checks_key: [
            # check folder splitting
        ],
    }
}


def __stage_name_from_folder(folder_name: str) -> str:
    return folder_name.split(".")[1]


def __stage_from_structure(substructure: structure.Structure):
    stage_folder = substructure.name
    stage_name = __stage_name_from_folder(stage_folder)
    stage_handlers = __premapping[stage_name]
    stage_path = substructure.path

    stage = Stage(
        name=stage_name,
        folder=stage_folder,
        path=stage_path,
        incoming_checks=stage_handlers.get(__incoming_checks_key, None),
        preparation_hooks=stage_handlers.get(__preparation_hooks_key, None),
        outcoming_checks=stage_handlers.get(__outcoming_checks_key, None),
    )

    return stage


ALL_STAGES = [__stage_from_structure(substructure) for substructure in structure.disk_structure["stages"].substructures]
