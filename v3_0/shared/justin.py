from argparse import Namespace
from typing import Callable

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.actions.action_factory import ActionFactory
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

    @property
    def schedule(self) -> Callable[[Namespace], None]:
        return self.__build_action(self.__actions_factory.schedule())

    @property
    def stage(self) -> Callable[[Namespace], None]:
        return self.__build_action(self.__actions_factory.stage())

    @property
    def rearrange(self) -> Callable[[Namespace], None]:
        return self.__build_action(self.__actions_factory.rearrange())

    @property
    def sync_posts_status(self) -> Callable[[Namespace], None]:
        return self.__build_action(self.__actions_factory.sync_posts_status())

    @property
    def delete_posts(self) -> Callable[[Namespace], None]:
        return self.__build_action(self.__actions_factory.delete_posts())

    @property
    def local_sync(self):
        return self.__build_action(self.__actions_factory.local_sync())

    @property
    def archive(self):
        return self.__build_action(self.__actions_factory.archive())

    @property
    def move(self):
        return self.__build_action(self.__actions_factory.move())
