from dataclasses import dataclass
from enum import Enum
from pathlib import Path


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
    TIMELAPSE = "timelapse"
    SETUP_EVENT = "setup-event"


class Locations(str, Enum):
    C = "C:/Users/justin/"
    D = "D:/"
    E = "E:/"
    H = "H:/"
    F = "F:/"
    PESTILENCE = "/Volumes/pestilence/"
    MICHAEL = "/Volumes/michael/"
    TB4 = "/Volumes/4tb/"
    SHARGE = "/Volumes/sharge/"
    MAC_OS_HOME = "/Users/justin/"


class Stages(str, Enum):
    GIF = "stage0.gif"
    FILTER = "stage1.filter"
    DEVELOP = "stage2.develop"
    OURATE = "stage2.ourate"
    READY = "stage3.ready"
    SCHEDULE = "stage3.schedule"
    PUBLISHED = "stage4.published"


@dataclass
class RunConfig:
    cwd: Path
    command: str
