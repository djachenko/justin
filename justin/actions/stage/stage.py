from abc import abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import List, Iterable

from justin.actions.stage.logic.base import Check, Problem
from justin.actions.stage.logic.base import Extractor
from justin.shared.models.photoset import Photoset


class Stage:
    def __init__(
            self,
            folder: str,
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

        self.__folder = folder
        self.__command = command
        self.__incoming_checks = incoming_checks
        self.__outcoming_checks = outcoming_checks
        self.__preparation_hooks = preparation_hooks

    @property
    def name(self):
        return self.folder.split(".")[-1]

    @property
    def folder(self) -> str:
        return self.__folder

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

    def prepare(self, photoset: Photoset):
        for hook in self.__preparation_hooks:
            hook.forward(photoset)

    def cleanup(self, photoset: Photoset) -> Iterable[Problem]:
        for hook in self.__preparation_hooks:
            problems = hook.backwards(photoset)

            if problems:
                return problems

        return []

    def transfer(self, photoset: Photoset, root: Path) -> None:
        photoset.move(self.get_new_parent(photoset, root))

    @abstractmethod
    def get_new_parent(self, photoset: Photoset, root: Path) -> Path:
        pass


class DefaultStage(Stage):
    def get_new_parent(self, photoset: Photoset, root: Path) -> Path:
        return root / "stages" / self.folder


class ArchiveStage(Stage):
    def get_new_parent(self, photoset: Photoset, root: Path) -> Path:
        destinations = [
            "closed",
            "drive",
            "justin",
            "kot_i_kit",
            "meeting",
            "my_people",
            "photoclub",
        ]

        files_mapping = defaultdict(lambda: [])

        for part in photoset.parts:
            for destination in destinations:
                if destination not in part.folder:
                    continue

                files_mapping[destination] += part.folder[destination].flatten()

        # existing_destinations = [d for d in destinations if d in photoset.folder]
        #
        # largest_destination = max(existing_destinations, key=lambda x: len(photoset.folder[x].flatten()))

        largest_destination = max(files_mapping.keys(), key=lambda x: len(files_mapping[x]))
        new_path = root / largest_destination

        if largest_destination in ["justin", "closed", "drive", ]:
            files_mapping = defaultdict(lambda: [])

            for part in photoset.parts:
                if largest_destination not in part.folder:
                    continue

                for category in part.folder[largest_destination].subfolders:
                    files_mapping[category.name] += category.flatten()

            largest_category = max(files_mapping.keys(), key=lambda x: len(files_mapping[x]))

            new_path /= largest_category

        return new_path
