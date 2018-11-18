from pathlib import Path

from v3_0.models.stages.stage import Stage


class FilterStage(Stage):
    def __init__(self, path: Path):
        super().__init__(path, command="filter", incoming_checks=[], outcoming_checks=[], preparation_hooks=[])
