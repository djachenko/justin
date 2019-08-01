from functools import lru_cache
from typing import List

from v3_0.commands.command import Command
from v3_0.schedule.schedule_command import ScheduleCommand
from v3_0.stage.stage_command import StageCommand
from v3_0.stage.models.stages_factory import StagesFactory


class CommandFactory:
    @staticmethod
    @lru_cache()
    def instance() -> 'CommandFactory':
        return CommandFactory()

    @lru_cache()
    def commands(self) -> List[Command]:
        return [
            self.stage(),
            self.schedule()
        ]

    @lru_cache()
    def stage(self) -> Command:
        return StageCommand(StagesFactory.instance())

    @lru_cache()
    def schedule(self) -> Command:
        return ScheduleCommand()
