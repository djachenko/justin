from argparse import Namespace
from pathlib import Path

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

    def schedule(self, args: Namespace) -> None:
        action = self.__actions_factory.schedule()

        self.__run_action(action, args)

    def stage(self, args: Namespace) -> None:
        action = self.__actions_factory.stage()

        self.__run_action(action, args)

    def rearrange(self, args: Namespace) -> None:
        action = self.__actions_factory.rearrange()

        self.__run_action(action, args)
