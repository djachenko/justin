from argparse import Namespace, ArgumentParser
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import List, Type, Tuple, TypeVar, Any, Callable, Iterable, ClassVar, Dict
from uuid import UUID

from justin.cms.db import DBEntry, Database
from justin.shared.context import Context
from justin.shared.metafile import PostMetafile, RootMetafile, GroupMetafile, MetaFolder, PhotosetMetafile
from justin.shared.models.photoset import Photoset
from justin.shared.models.world import World
from justin_utils.cli import Action
from pyvko.aspects.posts import Post, Posts
from pyvko.attachment.photo import Photo

T = TypeVar("T", bound="DBEntry")

V = TypeVar("V")


def wide(start: V, provider: Callable[[V], Iterable[V]]) -> None:
    roots = [start]

    while roots:
        roots += provider(roots.pop(0))


@dataclass
class PhotosetEntry(DBEntry):
    photoset_id: UUID
    photoset_name: str
    photoset_date: str
    photoset_size: int
    photoset_location: str  # maybe location
    photoset_path: str
    post_ids: List[Tuple[int, int]]  # (group, post)
    description: str = None

    @classmethod
    def from_photoset(cls, photoset: Photoset, world: World) -> 'PhotosetEntry':
        photoset_name = photoset.name
        photoset_size = photoset.folder.total_size

        location_path = world.location_of_path(photoset.path).path
        photoset_location = location_path.as_posix()
        photoset_path = photoset.path.relative_to(location_path).as_posix()

        def collect(folder: MetaFolder, meta_type: Type[RootMetafile]) -> List[MetaFolder]:
            if folder.has_metafile(meta_type):
                return [folder]

            result = []

            for item in folder.subfolders:
                result += collect(item, meta_type)

            return result

        post_ids = []

        group_folders = collect(photoset.folder, GroupMetafile)

        for group_folder in group_folders:
            group_metafile = group_folder.get_metafile(GroupMetafile)

            group_id = group_metafile.group_id

            post_folders = collect(group_folder, PostMetafile)

            for post_folder in post_folders:
                post_metafile = post_folder.get_metafile(PostMetafile)

                post_id = post_metafile.post_id

                post_ids.append((group_id, post_id))

        year, month, day, rest = photoset.name.split(".", maxsplit=3)

        if not (year.isdecimal() and month.isdecimal() and day.isdecimal()):
            assert False, "date not parceable"

        year = int(year) + 2000
        month = int(month)
        day = int(day)

        photoset_date = date(
            year=year,
            month=month,
            day=day
        )

        return PhotosetEntry(
            photoset_id=photoset.id,
            photoset_name=photoset_name,
            photoset_date=photoset_date.strftime("%d.%m.%Y"),
            photoset_size=photoset_size,
            photoset_location=photoset_location,
            photoset_path=photoset_path,
            post_ids=post_ids
        )

    def as_dict(self):
        self_dict = super().as_dict()

        self_dict["post_ids"] = ", ".join(f"{group_id}_{post_id}" for group_id, post_id in self_dict["post_ids"])

        return self_dict

    @classmethod
    def from_dict(cls: Type[T], csv_dict) -> T:
        csv_dict = csv_dict.copy()

        if "post_ids" not in csv_dict:
            csv_dict["post_ids"] = ""

        csv_dict["post_ids"] = [s.split("_") for s in csv_dict["post_ids"].split(", ")]

        return super().from_dict(csv_dict)

    @property
    def key(self) -> Any:
        return self.photoset_id

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, PhotosetEntry):
            return NotImplemented

        return self.key == other.key


@dataclass
class PostEntry(DBEntry):
    class State(str, Enum):
        PUBLISHED = "Published"
        SCHEDULED = "Scheduled"

    DATETIME_FORMAT: ClassVar[str] = "%H:%M:%S %d.%m.%Y"

    TAGS_REPLACE_MAP: ClassVar[Dict[str, str]] = {
        "#polls": "#poll",
        "#portait": "#portrait",
        "#reports": "#report",
        "#patterns": "#pattern",
        "#nanoreports": "#nanoreport",
        "#initiation": "#init",
    }

    TAGS_SEPARATOR: ClassVar[str] = ", "

    post_id: int
    group_id: int
    post_date: datetime
    tags: List[str]
    text: str
    state: State
    timer_id: int = None
    description: str = None

    @classmethod
    def from_post(cls, post: Post, state: State) -> 'PostEntry':
        post_date = post.date

        photos = [attach for attach in post.attachments if isinstance(attach, Photo)]

        words = post.text.split()

        for photo in photos:
            words += photo.text.split()

        tags = [word for word in words if word.startswith("#") and "@" in word]

        tags = [tag.split("@")[0] for tag in tags]
        tags = [PostEntry.TAGS_REPLACE_MAP.get(tag) or tag for tag in tags]

        return PostEntry(
            post_id=post.id,
            timer_id=post.timer_id,
            group_id=post.owner_id,
            post_date=post_date,
            tags=tags,
            text=post.text,
            state=state
        )

    @property
    def key(self) -> Any:
        return self.group_id, self.post_id

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        if not isinstance(other, PostEntry):
            return NotImplemented

        if self.group_id != other.group_id:
            return False

        return self.post_id == other.post_id \
            or self.timer_id == other.post_id \
            or self.post_id == other.timer_id

    @classmethod
    def from_dict(cls: Type[T], csv_dict) -> T:
        csv_dict["tags"] = csv_dict["tags"].split(PostEntry.TAGS_SEPARATOR)
        csv_dict["post_date"] = datetime.strptime(csv_dict["post_date"], PostEntry.DATETIME_FORMAT)
        csv_dict["state"] = PostEntry.State(csv_dict["state"])

        return super().from_dict(csv_dict)

    def as_dict(self):
        super_dict = super().as_dict()

        super_dict["tags"] = ", ".join(self.tags)
        super_dict["post_date"] = self.post_date.strftime(PostEntry.DATETIME_FORMAT)
        super_dict["state"] = self.state.value

        return super_dict


class CMSAction(Action):

    def configure_subparser(self, subparser: ArgumentParser) -> None:
        super().configure_subparser(subparser)

        meg_adder = subparser.add_mutually_exclusive_group(required=True)

        meg_adder.add_argument("--index_group", "-ig")
        meg_adder.add_argument("--index_photoset", "-ip", type=lambda x: MetaFolder.from_path(Path(x)))
        meg_adder.add_argument("--index_location", "-il", type=lambda x: MetaFolder.from_path(Path(x)))

    def perform(self, args: Namespace, context: Context) -> None:
        db = context.cms_db

        if args.index_group is not None:
            group = context.pyvko.get(args.index_group)

            self.index_group(group, db)
        elif args.index_photoset is not None:
            self.index_photoset(args.index_photoset, context.world, db)
        elif args.index_location is not None:
            self.index_location(args.index_location, context.world, db)

    @staticmethod
    def index_group(group: Posts, db: Database):
        posted_entries = [PostEntry.from_post(post, PostEntry.State.PUBLISHED) for post in group.get_posts()]
        scheduled_entries = [PostEntry.from_post(post, PostEntry.State.SCHEDULED)
                             for post in group.get_scheduled_posts()]

        tags = defaultdict(lambda: 0)

        for posted_entry in posted_entries:
            for tag in posted_entry.tags:
                tags[tag] += 1

        for posted_entry in posted_entries:
            for tag in posted_entry.tags:
                tags[tag] += 1

        for tag in sorted(tags.keys(), key=lambda x: (tags[x], x), reverse=True):
            print(tag, end=" ")

        db.update(*(posted_entries + scheduled_entries))

    @staticmethod
    def index_photoset(photoset_folder: MetaFolder, world: World, db: Database):
        photoset = Photoset.from_folder(photoset_folder)

        new_entry = PhotosetEntry.from_photoset(photoset, world)

        db.update(new_entry)

    @staticmethod
    def index_location(location: MetaFolder, world: World, db: Database) -> None:
        sets = []

        def wide_func(candidate: MetaFolder) -> Iterable[MetaFolder]:
            if candidate.has_metafile(PhotosetMetafile):
                sets.append(candidate)

                return []
            else:
                return candidate.subfolders

        wide(location, wide_func)

        for photoset in sets:
            CMSAction.index_photoset(photoset, world, db)
