from enum import Enum
from pathlib import Path

from v3_0.runners import general_runner
from v3_0.shared.helpers.cd import cd


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


class Locations(str, Enum):
    C = "C:/Users/justin/"
    D = "D:/"
    E = "E:/"
    H = "H:/"
    PESTILENCE = "/Volumes/pestilence/"
    MICHAEL = "/Volumes/michael/"
    MAC_OS_HOME = "/Users/justin"


class Stage(str, Enum):
    GIF = "stage0.gif"
    DEVELOP = "stage2.develop"
    OURATE = "stage2.ourate"
    READY = "stage3.ready"
    SCHEDULED = "stage3.schedule"
    PUBLISHED = "stage4.published"


if __name__ == '__main__':
    def build_command(command: Commands, location: Locations, stage: Stage, name: str):
        return f"{command} {location}photos/stages/{stage}/{name}"

    current_location = Locations.C

    commands = [
        build_command(
            command=Commands.OURATE,
            location=current_location,
            stage=Stage.OURATE,
            name="17.07*"
        ),
        "upload",
        "local_sync",
        "rearrange -s 1",
        "rearrange",
        "delay",
        "",
        "web_sync",
        "delay",
        f"move " + " ".join([f"{Locations.C}/photos/{f}" for f in [
            "1",
            "2",
        ]])
    ]

    with cd(Path(str(current_location.value))):
        general_runner.run(
            Path(__file__).parent.parent.parent,
            commands[9].split()
        )
