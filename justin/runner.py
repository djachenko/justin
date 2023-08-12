from enum import Enum
from pathlib import Path
from typing import List

from lazy_object_proxy import Proxy

from justin.cms.cms import CMS
from justin.di.app import DI
from justin.shared.config import Config
from justin.shared.context import Context
from justin.shared.models.photoset_migration import PhotosetMigrationFactory
from justin.shared.world import World
from justin_utils.cd import cd
from justin_utils.cli import App
from pyvko.config.config import Config as PyvkoConfig
from pyvko.pyvko_main import Pyvko

__CONFIGS_FOLDER = ".justin"
__CONFIG_FILE = "config.py"
__PYVKO_CONFIG_FILE = "pyvko_config.json"
__CMS_FOLDER = "cms"


def __run(config_path: Path, args: List[str] = None):
    configs_folder = config_path / __CONFIGS_FOLDER
    pyvko_config_file = configs_folder / __PYVKO_CONFIG_FILE
    cms_root = configs_folder / __CMS_FOLDER

    pyvko_config = PyvkoConfig.read(pyvko_config_file)
    pyvko = Pyvko(pyvko_config)
    cms = CMS(cms_root)

    config = Config.from_source(configs_folder / __CONFIG_FILE, init_globals={
        "people": cms.people,
    })

    def get_lazy_group(url_key):
        return Proxy(lambda: pyvko.get_by_url(config[url_key]))

    commands = DI(config).commands_factory.commands()

    context = Context(
        world=Proxy(lambda: World()),
        justin_group=get_lazy_group(Config.Keys.JUSTIN_URL),
        closed_group=get_lazy_group(Config.Keys.CLOSED_URL),
        meeting_group=get_lazy_group(Config.Keys.MEETING_URL),
        kot_i_kit_group=get_lazy_group(Config.Keys.KOT_I_KIT_URL),
        my_people_group=get_lazy_group(Config.Keys.MY_PEOPLE_URL),
        pyvko=pyvko,
        cms=cms,
        photoset_migrations_factory=PhotosetMigrationFactory(cms)
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
    REGISTER_PEOPLE = "reg_people"
    FIX_PEOPLE = "fix_people"


class Locations(str, Enum):
    C = "C:/Users/justin/"
    D = "D:/"
    E = "E:/"
    H = "H:/"
    F = "F:/"
    PESTILENCE = "/Volumes/pestilence/"
    MICHAEL = "/Volumes/michael/"
    TB4 = "/Volumes/4tb/"
    MAC_OS_HOME = "/Users/justin/"


class Stages(str, Enum):
    GIF = "stage0.gif"
    FILTER = "stage1.filter"
    DEVELOP = "stage2.develop"
    OURATE = "stage2.ourate"
    READY = "stage3.ready"
    SCHEDULE = "stage3.schedule"
    PUBLISHED = "stage4.published"


def main():
    current_location = Locations.MAC_OS_HOME
    current_stage = Stages.SCHEDULE
    current_command = Commands.REGISTER_PEOPLE
    current_pattern = "*.aerocolor"

    commands = {
        0: f"{current_command.value} {current_pattern}",
        1: "mig_person shtro roman"
    }

    locations = {
        0: f"{current_location.value}photos/stages/{current_stage.value}",
        1: f"{current_location.value}photos",
        2: "/Users/justin/photos/stages/stage2.develop/21.04.30.white_cottage",
    }

    with cd(Path(locations[0])):
        __run(
            Path(__file__).parent.parent,
            commands[0].split()
        )


if __name__ == '__main__':
    main()

# endregion ide
