from enum import Enum
from pathlib import Path
from typing import List

from lazy_object_proxy import Proxy

from justin.di.app import DI
from justin.shared.config import Config
from justin.shared.context import Context
from justin.shared.models.person import PeopleRegistry
from justin.shared.models.world import World
from justin_utils.cd import cd
from justin_utils.cli import App
from pyvko.config.config import Config as PyvkoConfig
from pyvko.pyvko_main import Pyvko

__CONFIGS_FOLDER = ".justin"
__CONFIG_FILE = "config.py"
__PYVKO_CONFIG_FILE = "pyvko_config.json"


def __run(config_path: Path, args: List[str] = None):
    configs_folder = config_path / __CONFIGS_FOLDER
    pyvko_config_file = configs_folder / __PYVKO_CONFIG_FILE

    pyvko_config = PyvkoConfig.read(pyvko_config_file)
    pyvko = Pyvko(pyvko_config)

    my_people = PeopleRegistry(configs_folder, "my_people", pyvko)
    closed = PeopleRegistry(configs_folder, "closed", pyvko)

    config = Config.from_source(configs_folder / __CONFIG_FILE, init_globals={
        "my_people": my_people,
        "closed": closed
    })

    def get_lazy_group(url_key):
        return Proxy(lambda: pyvko.get_by_url(config[url_key]))

    context = Context(
        world=Proxy(lambda: World()),
        justin_group=get_lazy_group(Config.Keys.JUSTIN_URL),
        closed_group=get_lazy_group(Config.Keys.CLOSED_URL),
        meeting_group=get_lazy_group(Config.Keys.MEETING_URL),
        kot_i_kit_group=get_lazy_group(Config.Keys.KOT_I_KIT_URL),
        my_people_group=get_lazy_group(Config.Keys.MY_PEOPLE_URL),
        pyvko=pyvko,
        my_people=my_people,
        closed=closed,
    )

    context.my_people.read()
    context.closed.read()

    commands = DI(config).commands_factory.commands()

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
    FILTER = "stage1.filter"
    DEVELOP = "stage2.develop"
    OURATE = "stage2.ourate"
    READY = "stage3.ready"
    SCHEDULED = "stage3.schedule"
    PUBLISHED = "stage4.published"


def main():
    current_location = Locations.MAC_OS_HOME
    current_stage = Stages.PUBLISHED
    current_command = Commands.ARCHIVE
    current_pattern = "*"

    commands = {
        0: f"{current_command} {current_pattern}",
        1: "rearrange -s 1",
        2: "rearrange",
        3: "delay",
        4: "",
        5: "check_ratios",
        6: "delete_posts",
        7: "rearrange --group kotikit --shuffle --step 2 --start_time 18:00 --end_time 19:00",
        8: "rearrange --shuffle",
        9: "setup_event --parent_id 143472211 206107409 21.05.22 22.05.21.night_with_bet",
        10: "setup_event https://vk.com/event206314876 24.06.22 22.06.24.bakina_prom --parent https://vk.com/mothilda",
        11: "upload -h",
        12: "people_fix -a",
        13: "setup_event --url https://vk.com/event206315284 --folder .",
        14: "cms -ig jvstin",
        15: "cms -ip 22.05.14.self_maevka",
        16: "cms -il .",
        17: "group",
    }

    locations = {
        0: f"{current_location}photos/stages/{current_stage}",
        1: f"{current_location}photos"
    }

    with cd(Path(locations[1])):
        __run(
            Path(__file__).parent.parent,
            commands[14].split()
        )


if __name__ == '__main__':
    main()

# endregion ide
