from argparse import Namespace
from pathlib import Path
from typing import Callable

from pyvko.pyvko_main import Pyvko
from pyvko.config.config import Config as PyvkoConfig

from v3_0.actions.action import Action
from v3_0.actions.action_factory import ActionFactory
from v3_0.shared.configuration.config import Config
from v3_0.shared.models.world import World
from v3_0.shared.helpers.singleton import Singleton


class Justin(Singleton):
    __CONFIGS_FOLDER = Path(".justin_configs")
    __CONFIG_FILE = "config.json"

    def __init__(self) -> None:
        super().__init__()

        config = Config.read(Justin.__CONFIGS_FOLDER / Justin.__CONFIG_FILE)

        pyvko = Pyvko(PyvkoConfig.read(Justin.__CONFIGS_FOLDER / config.pyvko_config))

        self.__group = pyvko.get_group(config.group_url)
        self.__world = World.instance()

        self.__actions_factory = ActionFactory.instance()

    def __run_action(self, action: Action, args: Namespace) -> None:
        action.perform(args, self.__world, self.__group)

    def __build_action(self, action: Action) -> Callable[[Namespace], None]:
        def inner(args: Namespace) -> None:
            self.__run_action(action, args)

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
