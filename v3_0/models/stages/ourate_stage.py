from pathlib import Path

from logic.photoset.filters.edited_filter import EditedFilter
from v3_0.logic.metadata.metadata_check import MetadataCheck
from v3_0.logic.unselected.unselected_check import UnselectedCheck
from v3_0.models.stages.stage import Stage


class OurateStage(Stage):
    def __init__(self, path: Path):
        super().__init__(
            path,
            command="ourate",
            incoming_checks=[],
            outcoming_checks=[
                UnselectedCheck(),
                MetadataCheck(),
            ],
            preparation_hooks=[
                EditedFilter()
            ]
        )
