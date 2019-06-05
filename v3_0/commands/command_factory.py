from functools import lru_cache
from typing import List

from v3_0.commands.command import Command
from v3_0.commands.stage_command import StageCommand
from v3_0.models.stages.stages_factory import StagesFactory


class CommandFactory:
    @staticmethod
    @lru_cache()
    def instance() -> 'CommandFactory':
        return CommandFactory()

    @lru_cache
    def commands(self) -> List[Command]:
        return [
            self.stage()
        ]

    @lru_cache()
    def stage(self) -> Command:
        return StageCommand(StagesFactory.instance())
