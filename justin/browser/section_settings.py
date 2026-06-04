from dataclasses import dataclass, field
from enum import Enum


class PostsPublishing(Enum):
    ALL_FOLLOWERS = "All followers"
    ADMINS_AND_EDITORS = "Administrators and editors"


class ContentType(Enum):
    ITEMS = "items"
    ITEMS_AND_ALBUMS = "items_and_albums"
    ALBUMS = "albums"


class AddAllowed(Enum):
    MEMBERS = "members"
    ADMINS_AND_EDITORS = "admins_and_editors"


@dataclass
class SectionSettings:
    enabled: bool


@dataclass
class PostsSettings(SectionSettings):
    enabled: bool = True
    publishing: PostsPublishing = PostsPublishing.ADMINS_AND_EDITORS
    sharing_disabled: bool = False


@dataclass
class PhotosSettings(SectionSettings):
    enabled: bool = True
    content_type: ContentType = ContentType.ITEMS
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass
class VideosSettings(SectionSettings):
    enabled: bool = True
    content_type: ContentType = ContentType.ITEMS
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass
class TopicsSettings(SectionSettings):
    enabled: bool = True
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass
class MusicSettings(SectionSettings):
    enabled: bool = False
    content_type: ContentType = ContentType.ITEMS
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass
class FilesSettings(SectionSettings):
    enabled: bool = False
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass
class MaterialsSettings(SectionSettings):
    enabled: bool = False
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass
class SectionsConfig:
    """None = не трогать секцию."""
    posts: PostsSettings | None = None #= field(default_factory=PostsSettings)
    photos: PhotosSettings | None = None # = field(default_factory=PhotosSettings)
    videos: VideosSettings | None = None
    topics: TopicsSettings | None = None
    music: MusicSettings | None = None
    files: FilesSettings | None = None
    materials: MaterialsSettings | None = None
