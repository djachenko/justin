import argparse
from enum import Enum
from pathlib import Path
from typing import Tuple, Callable

from justin.shared.context import Context
from justin.shared.metafile_migrations import *
from justin_utils.cd import cd
from lazy_object_proxy import Proxy
from pyvko.config.config import Config as PyvkoConfig
from pyvko.pyvko_main import Pyvko

from justin.shared.config import Config
from justin.shared.factories_container import FactoriesContainer
from justin.shared.models.world import World

# region general
from justin_utils.json_migration import JsonMigrator

__CONFIGS_FOLDER = ".justin"
__CONFIG_FILE = "config.py"


def __prepare_configs(config_path: Path) -> Tuple[Config, PyvkoConfig]:
    config = Config.from_source(config_path / __CONFIGS_FOLDER / __CONFIG_FILE)
    pyvko_config = PyvkoConfig.read(config_path / __CONFIGS_FOLDER / config[Config.Keys.PYVKO_CONFIG])

    return config, pyvko_config


def __prepare_containers(config: Config, pyvko_config: PyvkoConfig) -> Tuple[FactoriesContainer, Pyvko]:
    pyvko = Pyvko(pyvko_config)
    factories_container = FactoriesContainer(config)

    return factories_container, pyvko


def __run(config_path: Path, args=None):
    config, pyvko_config = __prepare_configs(config_path)

    factories_container, pyvko = __prepare_containers(config, pyvko_config)

    commands = factories_container.commands_factory.commands()

    parser = argparse.ArgumentParser()

    parser_adder = parser.add_subparsers()

    for command in commands:
        command.configure_parser(parser_adder)

    namespace = parser.parse_args(args)

    if not hasattr(namespace, "func") or not namespace.func or not isinstance(namespace.func, Callable):
        print("no parameters is bad")

        return

    JsonMigrator.instance().register(
        PostFormatMigration(),
        PostStatusMigration(),
    )

    context = Context(
        world=Proxy(lambda: World(config[Config.Keys.DISK_STRUCTURE])),
        justin_group=Proxy(lambda: pyvko.get(config[Config.Keys.JUSTIN_URL])),
        closed_group=Proxy(lambda: pyvko.get(config[Config.Keys.CLOSED_URL])),
        meeting_group=Proxy(lambda: pyvko.get(config[Config.Keys.MEETING_URL]))
    )

    namespace.func(namespace, context)


# endregion general

# region console

def console_run():
    __run(Path.home())


# endregion console

# region ide

class Commands(str, Enum):
    DEVELOP = "develop"
    OURATE = "ourate"
    READY = "ready"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    MOVE = "move"
    MAKE_GIF = "make_gif"
    SPLIT = "split"
    FIX_METAFILE = "fix_metafile"
    RESIZE_GIF_SOURCES = "resize_gif_sources"
    UPLOAD = "upload"
    WEB_SYNC = "web_sync"
    LOCAL_SYNC = "local_sync"


class Locations(str, Enum):
    C = "C:/Users/justin/"
    D = "D:/"
    E = "E:/"
    H = "H:/"
    PESTILENCE = "/Volumes/pestilence/"
    MICHAEL = "/Volumes/michael/"
    MAC_OS_HOME = "/Users/justin"


class Stages(str, Enum):
    GIF = "stage0.gif"
    DEVELOP = "stage2.develop"
    OURATE = "stage2.ourate"
    READY = "stage3.ready"
    SCHEDULED = "stage3.schedule"
    PUBLISHED = "stage4.published"


def main():
    def build_command(command: Commands, location: Locations, stage: Stages, name: str):
        return f"{command} {location}photos/stages/{stage}/{name}"

    current_location = Locations.D

    commands = {
        0: build_command(
            command=Commands.WEB_SYNC,
            location=current_location,
            stage=Stages.SCHEDULED,
            name="*"
        ),
        1: "rearrange -s 1",
        2: "rearrange",
        3: "delay",
        4: "",
    }

    with cd(Path(str(current_location.value))):
        __run(
            Path(__file__).parent.parent,
            commands[2].split()
        )


if __name__ == '__main__':
    main()

# endregion ide
