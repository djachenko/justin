from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Type
from uuid import uuid4

from justin.shared.filesystem import Folder
from justin.shared.metafile import PostMetafile, RootMetafile, GroupMetafile
from justin.shared.models.photoset import Photoset
from justin.shared.models.world import World
from pyvko.attachment.photo import Photo
from pyvko.pyvko_main import Pyvko


@dataclass
class CMSEntry:
    entry_id = uuid4()

    post_id: int
    group_id: int
    post_date: datetime
    tags: List[str]

    photoset_name: str
    photoset_date: date
    photoset_size: int
    photoset_location: str  # maybe location

    @classmethod
    def from_photoset(cls, photoset: Photoset, pyvko: Pyvko, world: World) -> List['CMSEntry']:
        photoset_name = photoset.name
        photoset_date = photoset.date
        photoset_size = photoset.total_size

        photoset_location = str(world.location_of_path(photoset.path))

        def collect(folder: Folder, meta_type: Type[RootMetafile]) -> List[Folder]:
            if folder.has_metafile(meta_type):
                return [folder]

            result = []

            for item in folder.subfolders:
                result += collect(item, meta_type)

        group_folders = collect(photoset.folder, GroupMetafile)

        entries = []

        for group_folder in group_folders:
            group_metafile = group_folder.get_metafile(GroupMetafile)

            group_id = group_metafile.group_id
            group = pyvko.get_group(group_id)

            post_folders = collect(group_folder, PostMetafile)

            for post_folder in post_folders:
                post_metafile = post_folder.get_metafile(PostMetafile)

                post_id = post_metafile.post_id
                post = group.get_post(post_id)

                post_date = post.date

                photos = [attach for attach in post.attachments if isinstance(attach, Photo)]

                words = post.text.split()

                for photo in photos:
                    words += photo.text.split()

                tags = [word for word in words if word.startswith("#") and "@" in word]

                tags = [tag.split("@")[0] for tag in tags]

                entries.append(CMSEntry(
                    post_id=post_id,
                    group_id=group_id,
                    post_date=post_date,
                    tags=tags,
                    photoset_name=photoset_name,
                    photoset_date=photoset_date,
                    photoset_size=photoset_size,
                    photoset_location=photoset_location
                ))

        return entries


class CMS:
    def __init__(self, pyvko: Pyvko, world: World) -> None:
        super().__init__()

        self.__entries: List[CMSEntry] = []
        self.__pyvko = pyvko
        self.__world = world

    def add_entry(self, entry: Photoset):
        self.__entries += CMSEntry.from_photoset(entry, self.__pyvko, self.__world)

    def upload(self) -> None:
        pass

    def save_local(self) -> None:
        pass


