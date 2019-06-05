from pathlib import Path

from v3_0.logic.factories.check_factory import CheckFactory
from v3_0.models.stages.stage import Stage


class GifStage(Stage):
    def __init__(self, path: Path):
        super().__init__(
            path,
            command="gif",
            incoming_checks=[],
            outcoming_checks=[],
            preparation_hooks=[]
        )
