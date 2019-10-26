import argparse
from pathlib import Path
from typing import Tuple

from pyvko.pyvko_main import Pyvko

from v3_0.shared.configuration.config import Config
from v3_0.shared.factories_container import FactoriesContainer
from v3_0.shared.helpers.cd import cd
from v3_0.shared.justin import Justin
from pyvko.config.config import Config as PyvkoConfig

from v3_0.shared.models.world import World

__CONFIGS_FOLDER = Path(".justin_configs")
__CONFIG_FILE = "config.py"


def __prepare_configs() -> Tuple[Config, PyvkoConfig]:
    config = Config.from_source(__CONFIGS_FOLDER / __CONFIG_FILE)
    pyvko_config = PyvkoConfig.read(__CONFIGS_FOLDER / config[Config.Keys.PYVKO_CONFIG])

    return config, pyvko_config


def __prepare_containers(config: Config, pyvko_config: PyvkoConfig) -> Tuple[FactoriesContainer, Pyvko]:
    pyvko = Pyvko(pyvko_config)
    factories_container = FactoriesContainer(config)

    return factories_container, pyvko


def run(working_path: Path, args=None):
    with cd(working_path):
        config, pyvko_config = __prepare_configs()

        factories_container, pyvko = __prepare_containers(config, pyvko_config)

        commands = factories_container.commands_factory.commands()

        parser = argparse.ArgumentParser()

        parser_adder = parser.add_subparsers()

        for command in commands:
            command.configure_parser(parser_adder)

        name = parser.parse_args(args)

        if hasattr(name, "func") and name.func:
            url = config[Config.Keys.GROUP_URL]
            group = pyvko.get(url)

            world = World(config[Config.Keys.DISK_STRUCTURE])

            justin = Justin(group, world, factories_container.actions_factory)

            name.func(name, justin)
        else:
            print("no parameters is bad")
