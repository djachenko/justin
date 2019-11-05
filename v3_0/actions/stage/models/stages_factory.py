from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from v3_0.actions.stage.logic.factories.checks_factory import ChecksFactory
from v3_0.actions.stage.logic.factories.extractor_factory import ExtractorFactory
from v3_0.actions.stage.models.stage import Stage


class StagesFactory:
    def __init__(self, checks_factory: ChecksFactory, extractors_factory: ExtractorFactory) -> None:
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
            self.scheduled(),
        ]

    @lru_cache()
    def gif(self) -> Stage:
        return Stage(
            path=Path("stage0.gif"),
            command="gif",
            outcoming_checks=[
                self.__checks_factory.gif_sources()
            ]
        )

    @lru_cache()
    def filter(self) -> Stage:
        return Stage(
            path=Path("stage1.filter"),
            command="filter"
        )

    @lru_cache()
    def develop(self) -> Stage:
        return Stage(
            path=Path("stage2.develop"),
            command="develop",
            outcoming_checks=[
                self.__checks_factory.unselected(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.metadata(),
            ]
        )

    @lru_cache()
    def ourate(self) -> Stage:
        return Stage(
            path=Path("stage2.ourate"),
            command="ourate",
            outcoming_checks=[
                self.__checks_factory.unselected(),
                self.__checks_factory.odd_selection(),
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
                self.__checks_factory.missing_gifs()
            ],
            outcoming_checks=[
                self.__checks_factory.structure(),
            ],
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
                self.__checks_factory.metadata(),
                self.__checks_factory.odd_selection(),
                self.__checks_factory.unselected(),
                self.__checks_factory.missing_gifs(),
                self.__checks_factory.structure(),
                self.__checks_factory.metafile(),
            ]
        )

    @lru_cache()
    def scheduled(self) -> Stage:
        return Stage(
            path=Path("stage3.schedule"),
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
            ],
            preparation_hooks=[
                # todo: offer to upload
            ]
        )

    def stage_by_folder(self, name: str) -> Optional[Stage]:
        return self.__stages_by_folders.get(name)

    def stage_by_command(self, command: str) -> Stage:
        return self.__stages_by_command[command]

    def stage_by_path(self, path: Path) -> Optional[Stage]:
        for path_part in path.absolute().parts:
            possible_stage = self.stage_by_folder(path_part)

            if possible_stage is not None:
                return possible_stage

        return None
