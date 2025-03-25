from pathlib import Path
from typing import List, Type

from justin.cms_2.sqlite_database import SQLiteDatabase, SQLiteEntry
from justin.cms_2.sqlite_entries import Drive, Closed, MyPeople, Photoset as PhotosetEntry, Post as PostEntry, Tag, \
    PostToTag, PersonPhotos
from justin.shared.metafile import PhotosetMetafile, MetaFolder
from justin.shared.models.photoset import Photoset
from justin_utils.util import bfs, distinct
from pyvko.aspects.posts import Posts, Post
from pyvko.attachment.photo import Photo
from pyvko.pyvko_main import Pyvko


class SQLiteCMS:
    def __init__(self, root: Path):
        self.__db = SQLiteDatabase(root, "justin.db")

    # region Photosets

    def index_photoset(self, photoset: Photoset) -> None:
        assert photoset.folder.has_metafile(PhotosetMetafile)

        entries_to_index = [PhotosetEntry(
            folder=photoset.name
        )]

        def to_entries(folder: MetaFolder | None, cls: Type[PersonPhotos]) -> List[SQLiteEntry]:
            if folder is None:
                return []

            return [cls(
                folder=subfolder.name,
                photoset=photoset.name,
                count=subfolder.file_count()
            ) for subfolder in folder.subfolders]

        entries_to_index += to_entries(photoset.drive, Drive)
        entries_to_index += to_entries(photoset.closed, Closed)
        entries_to_index += to_entries(photoset.my_people, MyPeople)

        with self.__db.connect():
            self.__db.update(*entries_to_index)

    def index_folder(self, folder: MetaFolder) -> None:
        def provider(candidate: MetaFolder) -> List[MetaFolder]:
            if candidate.has_metafile(PhotosetMetafile):
                self.index_photoset(Photoset.from_folder(candidate))

                return []
            else:
                return candidate.subfolders

        bfs(folder, provider)

    # endregion

    # region Posts

    __TAGS_REPLACE_MAP = {
        "#polls": "#poll",
        "#portait": "#portrait",
        "#reports": "#report",
        "#patterns": "#pattern",
        "#nanoreports": "#nanoreport",
        "#initiation": "#init",
    }

    @staticmethod
    def __get_index_text(post: Post) -> str:
        photos = [attach for attach in post.attachments if isinstance(attach, Photo)]

        photo_texts = [photo.text for photo in photos]
        index_texts = [post.text] + photo_texts

        index_texts = [text for text in index_texts if text]

        return " ".join(index_texts)

    @staticmethod
    def __extract_tags(post: Post) -> List[str]:
        words = SQLiteCMS.__get_index_text(post).split()

        tags = [word for word in words if word.startswith("#") and "@" in word]

        tags = [tag.split("@")[0] for tag in tags]
        tags = [SQLiteCMS.__TAGS_REPLACE_MAP.get(tag, tag) for tag in tags]
        tags = distinct(tags)

        return tags

    def index_post(self, post: Post, group_id: int) -> None:
        self.__update_post(post, group_id)
        self.__update_tags(post)
        self.__map_post_to_tags(post, group_id)

    def __map_post_to_tags(self, post: Post, group_id: int) -> None:
        tags = SQLiteCMS.__extract_tags(post)

        with self.__db.connect():
            existing_tags = self.__db.get_entries(Tag)

        tags_mapping = {tag.text: tag for tag in existing_tags}

        post_to_tags = [PostToTag(
            group_id=group_id,
            post_id=post.post_id,
            tag_id=tags_mapping[tag].tag_id
        ) for tag in tags]

        with self.__db.connect():
            self.__db.update(*post_to_tags)

    def __update_tags(self, post: Post) -> None:
        tags = SQLiteCMS.__extract_tags(post)

        with self.__db.connect():
            existing_tags = self.__db.get_entries(Tag)

        tags_mapping = {tag.text: tag for tag in existing_tags}

        tags_entries = [tags_mapping.get(tag) or Tag(text=tag) for tag in tags]

        with self.__db.connect():
            self.__db.update(*tags_entries)

    def __update_post(self, post: Post, group_id: int) -> None:
        with self.__db.connect():
            self.__db.update(PostEntry(
                group_id=group_id,
                post_id=post.id,
                text=post.text,
                date=post.date
            ))

    def index_group(self, identifier: str, pyvko: Pyvko) -> None:
        group = pyvko.get(identifier)

        assert isinstance(group, Posts)

        group_id = group.id
        posts = group.get_posts()

        for post in posts:
            self.index_post(post, group_id)

    # endregion
