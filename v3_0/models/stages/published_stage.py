from pathlib import Path

from v3_0.logic.factories.check_factory import CheckFactory
from v3_0.models.stages.stage import Stage


class PublishedStage(Stage):
    def __init__(self, path: Path):
        checks_factory = CheckFactory.instance()

        super().__init__(
            path,
            command="publish",
            incoming_checks=[
                checks_factory.missing_gifs()
            ],
            outcoming_checks=[],
            preparation_hooks=[]
        )
