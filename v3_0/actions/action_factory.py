from functools import lru_cache
from typing import List

from v3_0.actions.action import Action
from v3_0.actions.schedule.schedule_action import ScheduleAction
from v3_0.actions.stage.stage_action import StageAction
from v3_0.shared.helpers.singleton import Singleton
from v3_0.actions.stage.models.stages_factory import StagesFactory


class ActionFactory(Singleton):
    @lru_cache()
    def actions(self) -> List[Action]:
        return [
            self.stage(),
            self.schedule()
        ]

    @lru_cache()
    def stage(self) -> Action:
        return StageAction(StagesFactory.instance())

    @lru_cache()
    def schedule(self) -> Action:
        return ScheduleAction()
