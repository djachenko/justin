from abc import abstractmethod
from dataclasses import dataclass, asdict, field
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Type, TypeVar, List, Self, ClassVar
from uuid import UUID, uuid4

from justin.shared.filesystem import Folder
from justin.shared.helpers.utils import Json, fromdict
from justin_utils import util

T = TypeVar('T', bound='Metafile')
V = TypeVar('V', bound='RootMetafile')


class Metafile:
    @classmethod
    @abstractmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        pass

    @abstractmethod
    def as_json(self) -> Json:
        # todo: asdict(self)
        return {}


class MetafileReadWriter:
    def read(self, path: Path, metafile_type: V = None) -> V | None:
        pass

    def read_all(self, path: Path) -> List[V]:
        pass

    def write(self, metafile: 'RootMetafile', path: Path) -> None:
        pass


@dataclass
class RootMetafile(Metafile):
    __METAFILE_NAME = "_meta.json"
    __reader_internal: ClassVar[MetafileReadWriter]

    @classmethod
    @cache
    @abstractmethod
    def type(cls) -> str:
        pass

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return fromdict(json_object, cls)

    def as_json(self) -> Json:
        return super().as_json() | asdict(self)

    @classmethod
    def __metafile_path(cls, folder: Folder) -> Path:
        return folder.path / RootMetafile.__METAFILE_NAME

    @classmethod
    @cache
    def __reader(cls) -> MetafileReadWriter:
        return cls.__reader_internal

    @classmethod
    def set_reader(cls, reader: MetafileReadWriter) -> None:
        cls.__reader_internal = reader

    @classmethod
    def has(cls, folder: Folder) -> bool:
        if not cls.__metafile_path(folder).exists():
            return False

        return cls.get(folder) is not None

    @classmethod
    def get(cls, folder: Folder) -> Self | None:
        if not cls.__metafile_path(folder).exists():
            return None

        return cls.__reader().read(cls.__metafile_path(folder), cls)

    def save(self, folder: Folder) -> None:
        self.__reader().write(self, self.__metafile_path(folder))

    @classmethod
    def remove(cls, folder: Folder) -> None:
        metafile_path = cls.__metafile_path(folder)

        if cls == RootMetafile:
            assert False

            metafile_path.unlink(missing_ok=True)

            return

        metafiles: List[RootMetafile] = cls.__reader().read_all(metafile_path)

        saved_metafiles = [metafile for metafile in metafiles if type(metafile) is not cls]

        metafile_path.unlink(missing_ok=True)

        for metafile in saved_metafiles:
            metafile.save(folder)

    @classmethod
    def collect_metafile_paths(cls, folder: Folder) -> List[Path]:
        return [cls.__metafile_path(folder)] + \
            util.flat_map(cls.collect_metafile_paths(subfolder) for subfolder in folder.subfolders)


class PostStatus(Metafile, Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        assert isinstance(json_object, str)

        return cls(json_object)

    def as_json(self) -> Json:
        return str(self.value)


DATE_FORMAT_D_M_Y = "%d.%m.%y"


@dataclass
class PhotosetMetafile(RootMetafile):
    photoset_id: UUID = field(default_factory=lambda: uuid4())

    @classmethod
    def type(cls) -> str:
        return "photoset"

    def as_json(self) -> Json:
        return super().as_json() | {
            "photoset_id": self.photoset_id.hex
        }


@dataclass
class PostMetafile(RootMetafile):
    post_id: int
    status: PostStatus

    @classmethod
    def type(cls) -> str:
        return "post"

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return PostMetafile(
            post_id=json_object["post_id"],
            status=PostStatus.from_json(json_object["status"])
        )

    def as_json(self) -> Json:
        self_as_dict = asdict(self)

        self_as_dict["status"] = self.status.as_json()

        return super().as_json() | self_as_dict


@dataclass
class NoPostMetafile(RootMetafile):
    @classmethod
    def type(cls) -> str:
        return "no_post"


@dataclass
class GroupMetafile(RootMetafile):
    group_id: int

    @classmethod
    def type(cls) -> str:
        return "group"


@dataclass
class CommentMetafile(Metafile):
    id: int
    files: List[str]
    status: PostStatus

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return CommentMetafile(
            id=json_object["id"],
            files=json_object["files"],
            status=PostStatus.from_json(json_object["status"]),
        )

    def as_json(self) -> Json:
        self_as_dict = asdict(self)

        self_as_dict["status"] = self.status.as_json()

        return super().as_json() | self_as_dict


@dataclass
class PersonMetafile(RootMetafile):
    comments: List[CommentMetafile] = field(default_factory=lambda: [])

    @classmethod
    def type(cls) -> str:
        return "person"

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return PersonMetafile(
            comments=[CommentMetafile.from_json(comment) for comment in json_object["comments"]],
        )

    def as_json(self) -> Json:
        return super().as_json() | {
            "comments": [comment.as_json() for comment in self.comments]
        }


@dataclass
class AlbumMetafile(RootMetafile):
    album_id: int
    images: List[str]

    @classmethod
    def type(cls) -> str:
        return "album"

    def as_json(self) -> Json:
        return super().as_json() | asdict(self)

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return AlbumMetafile(
            album_id=json_object["album_id"],
            images=json_object["images"]
        )


@dataclass
class LocationMetafile(RootMetafile):
    location_name: str
    location_description: str
    location_order: int = -17

    @classmethod
    def type(cls) -> str:
        return "location"


@dataclass
class DriveMetafile(RootMetafile):
    folder_name: str

    @classmethod
    def type(cls) -> str:
        return "drive"
