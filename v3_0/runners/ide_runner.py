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
    D = "D:/"
    H = "H:/"
    PESTILENCE = "/Volumes/pestilence/"


class Stage(str, Enum):
    GIF = "stage0.gif"
    DEVELOP = "stage2.develop"
    OURATE = "stage2.ourate"
    READY = "stage3.ready"
    PUBLISHED = "stage4.published"


if __name__ == '__main__':
    def build_command(command: Commands, location: Locations, stage: Stage, name: str):
        return f"{command} {location}photos/stages/{stage}/{name}"

    current_location = Locations.H

    commands = [
        build_command(
            command=Commands.PUBLISH,
            location=current_location,
            stage=Stage.PUBLISHED,
            name="*"
        ),
        "upload -s 1",
        "local_sync",
        "rearrange -s 1",
        "delay"
    ]

    with cd(Path(str(current_location.value))):
        general_runner.run(
            Path(__file__).parent.parent.parent,
            commands[0].split()
        )
