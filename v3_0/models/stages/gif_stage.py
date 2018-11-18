from pathlib import Path

from v3_0.models.stages.stage import Stage


class GifStage(Stage):
    @classmethod
    def name(cls) -> str:
        pass

    @classmethod
    def command(cls) -> str:
        pass

    def __init__(self, path: Path):
        super().__init__(path, command="gif", incoming_checks=[], outcoming_checks=[], preparation_hooks=[])
