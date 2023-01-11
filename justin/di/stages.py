from functools import lru_cache
from pathlib import Path
from typing import List

from justin.actions.stage.stage import Stage, DefaultStage, ArchiveStage
from justin.di.checks import ChecksFactory
from justin.di.extractors import ExtractorFactory


class StagesFactory:
    def __init__(self, checks_factory: ChecksFactory, extractors_factory: ExtractorFactory) -> None:
        super().__init__()

        self.__checks_factory = checks_factory
        self.__extractors_factory = extractors_factory

        stages = self.stages()

        self.__stages_by_command = {stage.command: stage for stage in stages}
        self.__stages_by_folders = {stage.folder: stage for stage in stages}

    @property
    @lru_cache()
    def commands(self):
        return [stage.command for stage in self.stages()]

    @lru_cache()
    def stages(self) -> List[Stage]:
        return [
            self.gif(),
            self.filter(),
            self.develop(),
            self.ourate(),
            self.ready(),
            self.published(),
            self.scheduled(),
            self.archive(),
        ]

    @lru_cache()
    def archive(self) -> Stage:
        return ArchiveStage(
            folder=".archive",
            command="archive",
            incoming_checks=[
                self.__checks_factory.metadata(),
                self.__checks_factory.everything_is_published(),
                self.__checks_factory.unselected(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.structure(),
                self.__checks_factory.missing_gifs()
            ],
        )

    @lru_cache()
    def gif(self) -> Stage:
        return DefaultStage(
            folder="stage0.gif",
            command="gif",
            outcoming_checks=[
                self.__checks_factory.gif_sources(),
            ]
        )

    @lru_cache()
    def filter(self) -> Stage:
        return DefaultStage(
            folder="stage1.filter",
            command="filter"
        )

    @lru_cache()
    def develop(self) -> Stage:
        return DefaultStage(
            folder="stage2.develop",
            command="develop",
            outcoming_checks=[
                self.__checks_factory.unselected(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.metadata(),
            ],
            preparation_hooks=[
                self.__extractors_factory.progress(),
            ]
        )

    @lru_cache()
    def ourate(self) -> Stage:
        return DefaultStage(
            folder="stage2.ourate",
            command="ourate",
            outcoming_checks=[
                self.__checks_factory.unselected(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.metadata(),
            ],
            preparation_hooks=[
                self.__extractors_factory.progress(),
                self.__extractors_factory.edited(),
            ]
        )

    @lru_cache()
    def ready(self) -> Stage:
        return DefaultStage(
            folder="stage3.ready",
            command="ready",
            incoming_checks=[
                self.__checks_factory.metadata(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.unselected(),
                self.__checks_factory.missing_gifs()
            ],
            outcoming_checks=[
                self.__checks_factory.structure(),
            ]
        )

    @lru_cache()
    def published(self) -> Stage:
        return DefaultStage(
            folder="stage4.published",
            command="publish",
            incoming_checks=[
                self.__checks_factory.metadata(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.unselected(),
                self.__checks_factory.missing_gifs(),
                self.__checks_factory.structure(),
                self.__checks_factory.metafile(),
                self.__checks_factory.everything_is_published(),
            ]
        )

    @lru_cache()
    def scheduled(self) -> Stage:
        return DefaultStage(
            folder="stage3.schedule",
            command="schedule",
            incoming_checks=[
                self.__checks_factory.metadata(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.unselected(),
                self.__checks_factory.missing_gifs(),
                self.__checks_factory.structure(),
            ],
            outcoming_checks=[
                self.__checks_factory.metafile(),
            ]
        )

    @lru_cache()
    def stub(self) -> Stage:
        return Stage(
            folder=""
        )

    def stage_by_folder(self, name: str) -> Stage | None:
        return self.__stages_by_folders.get(name)

    def stage_by_command(self, command: str) -> Stage:
        return self.__stages_by_command[command]

    def stage_by_path(self, path: Path) -> Stage | None:
        for path_part in path.absolute().parts:
            possible_stage = self.stage_by_folder(path_part)

            if possible_stage is not None:
                return possible_stage

        return self.archive()
