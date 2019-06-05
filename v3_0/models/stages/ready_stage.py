from pathlib import Path

from logic.photoset.checks.odd_selection_check import OddSelectionCheck
from logic.photoset.checks.readiness_check import ReadinessCheck
from v3_0.logic.unselected.unselected_check import UnselectedCheck
from v3_0.models.stages.stage import Stage


class ReadyStage(Stage):
    def __init__(self, path: Path):
        super().__init__(
            path,
            command="ready",
            incoming_checks=[
                OddSelectionCheck(),
                UnselectedCheck(),
                ReadinessCheck(),
                # no service folders
                # gifs has been created
            ],
            outcoming_checks=[],
            preparation_hooks=[
                # instagram
                # sandbox
            ]
        )
