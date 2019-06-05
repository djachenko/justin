from pathlib import Path

from v3_0.logic.unselected.unselected_check import UnselectedCheck
from v3_0.logic.metadata.metadata_check import MetadataCheck
from v3_0.models.stages.stage import Stage


class DevelopStage(Stage):
    def __init__(self, path: Path):
        super().__init__(
            path,
            command="develop",
            incoming_checks=[],
            outcoming_checks=[
                UnselectedCheck(),
                MetadataCheck(),
            ],
            preparation_hooks=[]
        )
