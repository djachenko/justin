from pathlib import Path
from typing import Type, List, Optional

from v3_0 import structure
from v3_0.structure import Structure
from v3_0.models.stages.develop_stage import DevelopStage
from v3_0.models.stages.filter_stage import FilterStage
from v3_0.models.stages.gif_stage import GifStage
from v3_0.models.stages.ourate_stage import OurateStage
from v3_0.models.stages.published_stage import PublishedStage
from v3_0.models.stages.ready_stage import ReadyStage
from v3_0.models.stages.stage import Stage
from v3_0.models.world import World


class StagesFactory:

    @staticmethod
    def __name_from_class(cls: Type[Stage]) -> str:
        return cls.__name__.lower().replace("stage", "")

    @staticmethod
    def __name_from_structure(struct: Structure) -> str:
        return struct.path.name.split(".", 1)[1]

    __STAGE_CLASSES = [
        GifStage,
        FilterStage,
        OurateStage,
        DevelopStage,
        ReadyStage,
        PublishedStage,
    ]

    __STAGE_STRUCTURES = structure.disk_structure["stages"].substructures

    @staticmethod
    def __map_stages(world: World) -> List[Stage]:
        classes_by_name = {StagesFactory.__name_from_class(cls): cls for cls in StagesFactory.__STAGE_CLASSES}
        structures_by_name = {StagesFactory.__name_from_structure(struct): struct for struct in
                              StagesFactory.__STAGE_STRUCTURES}

        assert set(classes_by_name.keys()) <= set(structures_by_name.keys())

        names = classes_by_name.keys()

        root_path = world.active_disk.root.path

        stages = []

        for name in names:
            struct = structures_by_name[name]
            cls = classes_by_name[name]

            stage = cls(root_path / struct.path)

            stages.append(stage)

        return stages

    def __init__(self, world: World) -> None:
        super().__init__()

        stages = StagesFactory.__map_stages(world)

        self.__stages_by_command = {stage.command: stage for stage in stages}
        self.__stages_by_folders = {stage.folder: stage for stage in stages}

        self.__commands = [stage.command for stage in stages]

    @property
    def commands(self):
        return self.__commands

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
