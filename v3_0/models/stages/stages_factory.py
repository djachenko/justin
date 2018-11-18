import structure
from v3_0.models.stages.develop_stage import DevelopStage
from v3_0.models.stages.filter_stage import FilterStage
from v3_0.models.stages.gif_stage import GifStage
from v3_0.models.stages.ourate_stage import OurateStage
from v3_0.models.stages.published_stage import PublishedStage
from v3_0.models.stages.ready_stage import ReadyStage
from v3_0.models.stages.stage import Stage
from v3_0.models.world import World


class StagesFactory:
    STAGE_CLASSES = [
        GifStage,
        FilterStage,
        OurateStage,
        DevelopStage,
        ReadyStage,
        PublishedStage,
    ]

    __PATHS_MAPPING = {ss.name: ss.path for ss in structure.disk_structure["stages"].substructures}
    __PRODUCERS_MAPPING = {
        "gif": GifStage,
        "filter": FilterStage,
        "ourate": OurateStage,
        "develop": DevelopStage,
        "ready": ReadyStage,
        "published": PublishedStage,
    }

    # noinspection PyMethodMayBeStatic
    def stage(self, name: str, world: World) -> Stage:
        relative_path = StagesFactory.__PATHS_MAPPING[name]

        absolute_path = world.active_disk.root / relative_path

        producer = StagesFactory.__PRODUCERS_MAPPING[name]

        stage = producer(absolute_path)

        return stage
