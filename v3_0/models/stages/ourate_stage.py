from pathlib import Path

from v3_0.logic.factories.check_factory import CheckFactory
from v3_0.logic.factories.extractor_factory import ExtractorFactory
from v3_0.models.stages.stage import Stage


class OurateStage(Stage):
    def __init__(self, path: Path):
        checks_factory = CheckFactory.instance()
        extractor_factory = ExtractorFactory.instance()

        super().__init__(
            path,
            command="ourate",
            incoming_checks=[],
            outcoming_checks=[
                checks_factory.unselected(),
                checks_factory.metadata(),
            ],
            preparation_hooks=[
                extractor_factory.edited()
            ]
        )
