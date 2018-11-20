from typing import Type

import structure
from structure import Structure
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
    def __map_stages(world: World):
        classes_by_name = {StagesFactory.__name_from_class(cls): cls for cls in StagesFactory.__STAGE_CLASSES}
        structures_by_name = {StagesFactory.__name_from_structure(struct): struct for struct in
                              StagesFactory.__STAGE_STRUCTURES}

        assert set(classes_by_name.keys()) <= set(structures_by_name.keys())

        names = classes_by_name.keys()

        stages_by_name = {}
        stages_by_command = {}

        root_path = world.active_disk.root.path

        for name in names:
            struct = structures_by_name[name]
            cls = classes_by_name[name]

            stage = cls(root_path / struct.path)

            stages_by_name[name] = stage
            stages_by_command[stage.command] = stage

        return stages_by_name, stages_by_command

    def __init__(self, world: World) -> None:
        super().__init__()

        self.__stages_by_name, self.__stages_by_command = StagesFactory.__map_stages(world)

    def stage_by_name(self, name: str) -> Stage:
        return self.__stages_by_name[name]

    def stage_by_command(self, command: str) -> Stage:
        return self.__stages_by_command[command]


if __name__ == '__main__':
    w = World()

    fac = StagesFactory(w)

    a = 7
