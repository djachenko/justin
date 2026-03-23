import glob
import sys
from enum import Enum
from pathlib import Path

from justin_utils.cd import cd

from justin.typer.app.app import build_app


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
    WEB_SYNC = "web-sync"
    REGISTER_PEOPLE = "reg_people"
    FIX_PEOPLE = "fix_people"
    DRONE = "drone"
    ATTACH_ALBUM = "attach_album"
    STEP = "step_sources"


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
    current_command = Commands.WEB_SYNC
    current_pattern = "*fen*"

    locations = {
        0: f"{current_location.value}photos/stages/{current_stage.value}",
        1: f"{current_location.value}photos",
        2: "/Users/justin/photos/stages/stage2.develop/21.04.30.white_cottage",
    }

    with cd(Path(locations[0])):
        commands = {
            0: " ".join([current_command.value] + glob.glob(current_pattern)),
            1: "mig_person shtro roman",
            2: "append_album 75 305671811",
            3: "get_likers https://vk.com/wall-100568944_3923 https://vk.com/wall-100568944_3921 https://vk.com/wall-100568944_3902 https://vk.com/wall-100568944_3900 https://vk.com/wall-100568944_3892 https://vk.com/wall-100568944_3889",
            4: "get_likers https://vk.com/wall-100568944_3923",
            5: "index --group jvstin",
            6: "manage_tags --posts scheduled",
            7: "json2sqlite",
            8: "--help",
            9: "setup-event --create --url test_url --manual --folder test_folder",
        }

        app = build_app(Path(__file__).parent.parent.parent.parent)

        x = sys.argv

        app(commands[0].split())



if __name__ == '__main__':
    main()
