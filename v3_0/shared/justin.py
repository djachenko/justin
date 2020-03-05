from argparse import Namespace
from typing import Callable

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.actions.action_factory import ActionFactory
from v3_0.actions.action_id import ActionId
from v3_0.shared.models.world import World


class Justin:
    def __init__(self, group: Group, world: World, actions_factory: ActionFactory) -> None:
        super().__init__()

        self.__group = group
        self.__world = world

        self.__actions_factory = actions_factory

    def __build_action(self, action: Action) -> Callable[[Namespace], None]:
        def inner(args: Namespace) -> None:
            action.perform(args, self.__world, self.__group)

        return inner

    def __getitem__(self, action: ActionId) -> Callable[[Namespace], None]:
        return self.__build_action(self.__actions_factory[action])
