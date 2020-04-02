from enum import Enum, auto


class ActionId(Enum):
    ARCHIVE = auto()
    DELETE_POSTS = auto()
    LOCAL_SYNC = auto()
    MAKE_GIF = auto()
    MOVE = auto()
    REARRANGE = auto()
    SCHEDULE = auto()
    STAGE = auto()
    SYNC_POSTS_STATUS = auto()
    SPLIT = auto()
    FIX_METAFILE = auto()
    DELAY = auto()
    RESIZE_SOURCES = auto()
