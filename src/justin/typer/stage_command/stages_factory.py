

from functools import cached_property
from pathlib import Path
from typing import List

from justin.typer.stage_command.checks_factory import ChecksFactory
from justin.typer.stage_command.hooks_factory import HooksFactory
from justin.typer.stage_command.stage import Stage, DefaultStage, ArchiveStage


class StagesFactory:
    def __init__(self, checks_factory: ChecksFactory, hooks_factory: HooksFactory) -> None:
        self.__checks_factory = checks_factory
        self.__hooks_factory = hooks_factory

    # region Stages list

    @cached_property
    def stages(self) -> List[Stage]:
        return [
            self.filter,
            self.develop,
            self.ourate,
            self.ready,
            self.scheduled,
            self.published,
        ]

    @cached_property
    def commands(self) -> List[str]:
        return [stage.command for stage in self.stages]

    # endregion

    # region Individual stages

    @cached_property
    def filter(self) -> Stage:
        return DefaultStage(
            folder="stage1.filter",
            command="filter",
        )

    @cached_property
    def develop(self) -> Stage:
        return DefaultStage(
            folder="stage2.develop",
            command="develop",
            outcoming_checks=[
                self.__checks_factory.unselected,
                self.__checks_factory.odd_selection,
                self.__checks_factory.metadata,
            ],
            hooks=[
                self.__hooks_factory.progress,
            ],
        )

    @cached_property
    def ourate(self) -> Stage:
        return DefaultStage(
            folder="stage2.ourate",
            command="ourate",
            outcoming_checks=[
                self.__checks_factory.unselected,
                self.__checks_factory.odd_selection,
                self.__checks_factory.metadata,
            ],
            hooks=[
                self.__hooks_factory.progress,
                self.__hooks_factory.candidates,
            ],
        )

    @cached_property
    def ready(self) -> Stage:
        return DefaultStage(
            folder="stage3.ready",
            command="ready",
            incoming_checks=[
                self.__checks_factory.metadata,
                self.__checks_factory.odd_selection,
                self.__checks_factory.unselected,
            ],
            outcoming_checks=[
                self.__checks_factory.structure,
            ],
        )

    @cached_property
    def scheduled(self) -> Stage:
        return DefaultStage(
            folder="stage3.schedule",
            command="schedule",
            incoming_checks=[
                self.__checks_factory.metadata,
                self.__checks_factory.odd_selection,
                self.__checks_factory.unselected,
                self.__checks_factory.structure,
            ],
            outcoming_checks=[
                self.__checks_factory.metafiles_exist,
                self.__checks_factory.metafiles_published,
            ],
        )

    @cached_property
    def published(self) -> Stage:
        return DefaultStage(
            folder="stage4.published",
            command="publish",
            incoming_checks=[
                self.__checks_factory.metadata,
                self.__checks_factory.odd_selection,
                self.__checks_factory.unselected,
                self.__checks_factory.structure,
                self.__checks_factory.metafiles_exist,
                self.__checks_factory.metafiles_published,
                self.__checks_factory.everything_is_published,
            ],
        )

    @cached_property
    def gif(self) -> Stage:
        return DefaultStage(
            folder="stage0.gif",
            command="gif",
            outcoming_checks=[
                self.__checks_factory.gif_sources,
            ],
        )

    @cached_property
    def archive(self) -> Stage:
        return ArchiveStage(
            folder=".archive",
            command="archive",
            incoming_checks=[
                self.__checks_factory.metadata,
                self.__checks_factory.everything_is_published,
                self.__checks_factory.unselected,
                self.__checks_factory.odd_selection,
                self.__checks_factory.structure,
            ],
        )

    @cached_property
    def stub(self) -> Stage:
        return DefaultStage(folder="")

    # endregion

    # region Lookup

    def stage_by_command(self, command: str) -> Stage:
        return self.__by_command[command]

    def stage_by_path(self, path: Path) -> Stage | None:
        for part in path.absolute().parts:
            stage = self.__by_folder.get(part)

            if stage is not None:
                return stage

        return None

    @cached_property
    def __by_command(self) -> dict[str, Stage]:
        return {stage.command: stage for stage in self.stages}

    @cached_property
    def __by_folder(self) -> dict[str, Stage]:
        return {stage.folder: stage for stage in self.stages}

    # endregion