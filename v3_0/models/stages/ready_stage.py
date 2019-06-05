from pathlib import Path

from logic.photoset.checks.readiness_check import ReadinessCheck
from v3_0.logic.factories.check_factory import CheckFactory
from v3_0.models.stages.stage import Stage


class ReadyStage(Stage):
    def __init__(self, path: Path):
        checks_factory = CheckFactory.instance()

        super().__init__(
            path,
            command="ready",
            incoming_checks=[
                checks_factory.metadata(),
                checks_factory.odd_selection(),
                checks_factory.unselected(),
                checks_factory.missing_gifs(),

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
