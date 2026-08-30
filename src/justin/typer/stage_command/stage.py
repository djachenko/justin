from abc import abstractmethod, ABC
from collections import defaultdict
from pathlib import Path
from typing import List

from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.check import Check
from justin.typer.stage_command.abstracts.hook import Hook
from justin.typer.stage_command.checks.base import StageCheckError
from justin.typer.stage_command.checks_reporter import ChecksReporter


class Stage(ABC):
    """
    Стейдж пайплайна. Владеет своими чеками и хуками.

    Порядок при переходе A → B для каждой части фотосета:
      1. a.exit(part, reporter)  — unfix хуков A, прогон outcoming_checks A
      2. b.enter(part, reporter) — прогон incoming_checks B, fix хуков B

    Оба метода кидают StageCheckError при первой проблеме.
    Transfer вызывается снаружи только если все части прошли.
    """

    def __init__(
        self,
        folder: str,
        command: str = None,
        incoming_checks: List[Check] = None,
        outcoming_checks: List[Check] = None,
        hooks: List[Hook] = None,
    ) -> None:
        self.__folder = folder
        self.__command = command
        self.__incoming_checks = incoming_checks or []
        self.__outcoming_checks = outcoming_checks or []
        self.__hooks = hooks or []

    # region Properties

    @property
    def name(self) -> str:
        return self.__folder.split(".")[-1]

    @property
    def folder(self) -> str:
        return self.__folder

    @property
    def command(self) -> str:
        return self.__command

    def __str__(self) -> str:
        return f"Stage: {self.name}"

    # endregion

    # region Transition

    def exit(self, photoset: Photoset, reporter: ChecksReporter) -> None:
        """
        Проверки при выходе из стейджа.
        Порядок: unfix хуков → прогон outcoming_checks.
        Кидает StageCheckError если что-то не прошло.
        """
        for hook in self.__hooks:
            for part in photoset.parts:
                hook.unfix(part)

        Stage.__run_checks(self.__outcoming_checks, photoset, reporter)

    def enter(self, photoset: Photoset, reporter: ChecksReporter) -> None:
        """
        Проверки при входе в стейдж.
        Порядок: прогон incoming_checks → fix хуков.
        Кидает StageCheckError если что-то не прошло.
        """
        Stage.__run_checks(self.__incoming_checks, photoset, reporter)

        for hook in self.__hooks:
            for part in photoset.parts:
                hook.fix(part)

    def transfer(self, photoset: Photoset, root: Path) -> None:
        """Физически перемещает папку фотосета. Вызывается только после успешных exit+enter."""

        photoset.move(self.get_new_parent(photoset, root))

    # endregion

    # region Private

    @staticmethod
    def __run_checks(
        checks: List[Check],
        photoset: Photoset,
        reporter: ChecksReporter,
    ) -> None:
        """
        Прогоняет список чеков.
        Сначала unfix всех — откатить предыдущие fix-ы.
        При первой проблеме кидает StageCheckError.
        """
        photoset_parts = photoset.parts

        for check in checks:
            for part in photoset_parts:
                check.unfix(part)

        for check in checks:
            problems = []

            for part in photoset_parts:
                problems += check.get_problems(part)

            if not problems:
                reporter.on_check_passed(check.name)
                continue

            reporter.on_check_failed(check.name, problems)

            if check.should_fix(reporter):
                for part in photoset_parts:
                    check.fix(part)

            raise StageCheckError(problems)

    # endregion

    # region Abstract

    @abstractmethod
    def get_new_parent(self, photoset: Photoset, root: Path) -> Path:
        pass

    # endregion


class DefaultStage(Stage):
    def get_new_parent(self, photoset: Photoset, root: Path) -> Path:
        return root / "stages" / self.folder


class ArchiveStage(Stage):
    _DESTINATIONS = [
        "closed",
        "drive",
        "justin",
        "kot_i_kit",
        "meeting",
        "my_people",
        "photoclub",
    ]

    _GROUPED_DESTINATIONS = {"closed", "drive"}
    _TAGGED_DESTINATIONS = {"justin"}
    _TAGGED_CATEGORIES = {"report", "nanoreport"}

    def get_new_parent(self, photoset: Photoset, root: Path) -> Path:
        files_mapping: dict[str, list] = defaultdict(list)

        for part in photoset.parts:
            for dest in self._DESTINATIONS:
                if dest in part.folder:
                    files_mapping[dest] += part.folder[dest].flatten()

        largest = max(files_mapping.keys(), key=lambda x: len(files_mapping[x]))
        new_path = root / largest

        if largest in self._GROUPED_DESTINATIONS:
            category_mapping: dict[str, list] = defaultdict(list)

            for part in photoset.parts:
                if largest not in part.folder:
                    continue

                for category in part.folder[largest].subfolders:
                    category_mapping[category.name] += category.flatten()

            largest_category = max(category_mapping, key=lambda x: len(category_mapping[x]))
            new_path /= largest_category

        elif largest in self._TAGGED_DESTINATIONS:
            category_mapping = defaultdict(list)

            for part in photoset.parts:
                if largest not in part.folder:
                    continue

                for category in part.folder[largest].subfolders:
                    name = category.name if category.name in self._TAGGED_CATEGORIES else "art"
                    category_mapping[name] += category.flatten()

            largest_category = max(category_mapping, key=lambda x: len(category_mapping[x]))
            new_path /= largest_category

        return new_path
