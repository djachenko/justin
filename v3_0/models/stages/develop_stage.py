from pathlib import Path

from v3_0.logic.factories.check_factory import CheckFactory
from v3_0.models.stages.stage import Stage


class DevelopStage(Stage):
    def __init__(self, path: Path):
        checks_factory = CheckFactory.instance()

        super().__init__(
            path,
            command="develop",
            incoming_checks=[],
            outcoming_checks=[
                checks_factory.unselected(),
                checks_factory.metadata(),
            ],
            preparation_hooks=[]
        )
