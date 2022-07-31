from enum import Enum
from pathlib import Path
from typing import Tuple

from lazy_object_proxy import Proxy
from pyvko.config.config import Config as PyvkoConfig
from pyvko.pyvko_main import Pyvko

from justin.shared.config import Config
from justin.shared.context import Context
from justin.shared.factories_container import FactoriesContainer
from justin.shared.metafile_migrations import *
from justin.shared.models.world import World
from justin_utils.cd import cd
from justin_utils.cli import App
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


def __run(config_path: Path, args: List[str] = None):
    config, pyvko_config = __prepare_configs(config_path)

    factories_container, pyvko = __prepare_containers(config, pyvko_config)

    commands = factories_container.commands_factory.commands()

    context: Context = Context(
        world=Proxy(lambda: World(config[Config.Keys.DISK_STRUCTURE])),
        justin_group=Proxy(lambda: pyvko.get_by_url(config[Config.Keys.JUSTIN_URL])),
        closed_group=Proxy(lambda: pyvko.get_by_url(config[Config.Keys.CLOSED_URL])),
        meeting_group=Proxy(lambda: pyvko.get_by_url(config[Config.Keys.MEETING_URL])),
        kot_i_kit_group=Proxy(lambda: pyvko.get_by_url(config[Config.Keys.KOT_I_KIT_URL])),
        pyvko=pyvko,
    )

    JsonMigrator.instance().register(
        PostFormatMigration(),
        PostStatusMigration(),
    )

    try:
        App(commands, context).run(args)
    except KeyboardInterrupt:
        print("^C")


# endregion general

# region console

def console_run():
    try:
        __run(Path.home())
    except KeyboardInterrupt:
        print("Ctrl+^C")


# endregion console

# region ide

class Commands(str, Enum):
    ARCHIVE = "archive"
    CHECK_RATIOS = "check_ratios"
    DEVELOP = "develop"
    FIX_METAFILE = "fix_metafile"
    LOCAL_SYNC = "local_sync"
    MAKE_GIF = "make_gif"
    MOVE = "move"
    OURATE = "ourate"
    PUBLISH = "publish"
    READY = "ready"
    RESIZE_GIF_SOURCES = "resize_gif_sources"
    SCHEDULE = "schedule"
    SPLIT = "split"
    UPLOAD = "upload"
    WEB_SYNC = "web_sync"


class Locations(str, Enum):
    C = "C:/Users/justin/"
    D = "D:/"
    E = "E:/"
    H = "H:/"
    F = "F:/"
    PESTILENCE = "/Volumes/pestilence/"
    MICHAEL = "/Volumes/michael/"
    MAC_OS_HOME = "/Users/justin/"


class Stages(str, Enum):
    GIF = "stage0.gif"
    DEVELOP = "stage2.develop"
    OURATE = "stage2.ourate"
    READY = "stage3.ready"
    SCHEDULED = "stage3.schedule"
    PUBLISHED = "stage4.published"


def main():
    def build_command(command: Commands, location: Locations, stage: Stages, name: str) -> str:
        return f"{command} {name}"

    current_location = Locations.C
    current_stage = Stages.DEVELOP

    commands = {
        0: build_command(
            command=Commands.READY,
            location=current_location,
            stage=current_stage,
            name="*toka*",
        ),
        1: "rearrange -s 1",
        2: "rearrange",
        8: "rearrange --shuffle",
        7: "rearrange --group kotikit --shuffle --step 2 --start_time 18:00 --end_time 19:00",
        3: "delay",
        4: "",
        5: "check_ratios",
        6: "delete_posts",
    }

    with cd(Path(f"{current_location}photos/stages/{current_stage}")):
        __run(
            Path(__file__).parent.parent,
            commands[0].split()
        )


if __name__ == '__main__':
    main()

# endregion ide
