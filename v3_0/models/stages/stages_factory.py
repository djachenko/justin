from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from logic.photoset.checks.readiness_check import ReadinessCheck
from v3_0.logic.factories.check_factory import CheckFactory
from v3_0.logic.factories.extractor_factory import ExtractorFactory
from v3_0.models.stages.stage import Stage


class StagesFactory:
    @staticmethod
    @lru_cache()
    def instance() -> 'StagesFactory':
        return StagesFactory(
            checks_factory=CheckFactory.instance(),
            extractors_factory=ExtractorFactory.instance()
        )

    def __init__(self, checks_factory: CheckFactory, extractors_factory: ExtractorFactory) -> None:
        super().__init__()

        self.__checks_factory = checks_factory
        self.__extractors_factory = extractors_factory

        stages = self.stages()

        self.__stages_by_command = {stage.command: stage for stage in stages}
        self.__stages_by_folders = {stage.folder: stage for stage in stages}

        self.__commands = [stage.command for stage in stages]

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
        ]

    @lru_cache()
    def gif(self) -> Stage:
        return Stage(
            path=Path("stage0.gif"),
            command="gif",
            incoming_checks=[],
            outcoming_checks=[],
            preparation_hooks=[]
        )

    @lru_cache()
    def filter(self) -> Stage:
        return Stage(
            path=Path("stage1.filter"),
            command="filter",
            incoming_checks=[],
            outcoming_checks=[],
            preparation_hooks=[]
        )

    @lru_cache()
    def develop(self) -> Stage:
        return Stage(
            path=Path("stage2.develop"),
            command="develop",
            incoming_checks=[],
            outcoming_checks=[
                self.__checks_factory.unselected(),
                self.__checks_factory.metadata(),
            ],
            preparation_hooks=[]
        )

    @lru_cache()
    def ourate(self) -> Stage:
        return Stage(
            path=Path("stage2.ourate"),
            command="ourate",
            incoming_checks=[],
            outcoming_checks=[
                self.__checks_factory.unselected(),
                self.__checks_factory.metadata(),
            ],
            preparation_hooks=[
                self.__extractors_factory.edited()
            ]
        )

    @lru_cache()
    def ready(self) -> Stage:
        return Stage(
            path=Path("stage3.ready"),
            command="ready",
            incoming_checks=[
                self.__checks_factory.metadata(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.unselected(),
                self.__checks_factory.missing_gifs(),

                # todo: investigate and rewrite
                ReadinessCheck(),

                # todo: no service folders
                # todo: gifs has been created
            ],
            outcoming_checks=[],
            preparation_hooks=[
                # todo: instagram
                # sandbox
            ]
        )

    @lru_cache()
    def published(self) -> Stage:
        return Stage(
            path=Path("stage4.published"),
            command="publish",
            incoming_checks=[
                self.__checks_factory.missing_gifs()
            ],
            outcoming_checks=[],
            preparation_hooks=[]
        )

    def stage_by_folder(self, name: str) -> Optional[Stage]:
        return self.__stages_by_folders.get(name)

    def stage_by_command(self, command: str) -> Stage:
        return self.__stages_by_command[command]

    def stage_by_path(self, path: Path) -> Optional[Stage]:
        for path_part in path.parts:
            possible_stage = self.stage_by_folder(path_part)

            if possible_stage is not None:
                return possible_stage

        return None
