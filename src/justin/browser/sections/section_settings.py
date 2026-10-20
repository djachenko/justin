from dataclasses import dataclass
from enum import Enum


class PostsPublishing(Enum):
    ALL_FOLLOWERS = "All followers"
    ADMINS_AND_EDITORS = "Administrators and editors"


class AddAllowed(Enum):
    MEMBERS = "members"
    ADMINS_AND_EDITORS = "admins_and_editors"


@dataclass(frozen=True)
class SectionSettings:
    enabled: bool = True


@dataclass(frozen=True)
class PostsSettings(SectionSettings):
    publishing: PostsPublishing = PostsPublishing.ADMINS_AND_EDITORS
    sharing_disabled: bool = False


@dataclass(frozen=True)
class PhotosSettings(SectionSettings):
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass(frozen=True)
class VideosSettings(SectionSettings):
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass(frozen=True)
class TopicsSettings(SectionSettings):
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass(frozen=True)
class MusicSettings(SectionSettings):
    enabled: bool = False
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass(frozen=True)
class FilesSettings(SectionSettings):
    enabled: bool = False
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass(frozen=True)
class MaterialsSettings(SectionSettings):
    enabled: bool = False
    add_allowed: AddAllowed = AddAllowed.ADMINS_AND_EDITORS


@dataclass(frozen=True)
class ServicesSettings(SectionSettings):
    enabled: bool = False


@dataclass(frozen=True)
class ChatsSettings(SectionSettings):
    """Toggled in the section list itself, without a modal."""
    enabled: bool = False


@dataclass(frozen=True)
class ClipsSettings(SectionSettings):
    enabled: bool = False


@dataclass(frozen=True)
class ArticlesSettings(SectionSettings):
    enabled: bool = False


@dataclass(frozen=True)
class MomentsSettings(SectionSettings):
    enabled: bool = False


@dataclass(frozen=True)
class ProductsSettings(SectionSettings):
    enabled: bool = False


class MainSection(str, Enum):
    """The main block is the first tab on the Content tabs page — set by reordering."""
    POSTS = "wall"
    PHOTOS = "photos"
    VIDEOS = "videos"
    TOPICS = "discussions"
    MUSIC = "audios"
    SERVICES = "services"
    PRODUCTS = "market"


@dataclass(frozen=True)
class SectionsConfig:
    """None — leave the section alone."""
    posts: PostsSettings | None = None
    photos: PhotosSettings | None = None
    videos: VideosSettings | None = None
    topics: TopicsSettings | None = None
    music: MusicSettings | None = None
    files: FilesSettings | None = None
    materials: MaterialsSettings | None = None
    services: ServicesSettings | None = None
    chats: ChatsSettings | None = None
    clips: ClipsSettings | None = None
    articles: ArticlesSettings | None = None
    moments: MomentsSettings | None = None
    products: ProductsSettings | None = None
    main_section: MainSection | None = None
