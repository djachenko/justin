import json
from abc import abstractmethod, ABC
from datetime import date
from functools import lru_cache
from typing import Iterable, Tuple

from justin.shared.metafile import Json
from justin.shared.metafile import PostStatus, PostMetafile, MetafileReadWriter, GroupMetafile, PhotosetMetafile
from justin.shared.models.photoset import Photoset
from justin_utils.singleton import Singleton


class PhotosetMigration(Singleton):
    @abstractmethod
    def migrate(self, photoset: Photoset) -> None:
        pass


class SplitMetafilesMigration(PhotosetMigration):
    def migrate(self, photoset: Photoset) -> None:
        metafile_name = "_meta.json"
        old_metafile_path = photoset.path / metafile_name

        if not old_metafile_path.exists():
            return

        with old_metafile_path.open() as metafile_file:
            json_dict = json.load(metafile_file)

        if "migrated" in json_dict and json_dict["migrated"] or "type" in json_dict:
            return

        posts_jsons: Json = json_dict["posts"]

        posts = []

        for group_id, group_posts in posts_jsons.items():
            for group_post in group_posts:
                path = photoset.path / group_post["path"]
                post_id = int(group_post["id"])
                post_status = PostStatus(group_post["post_status"])

                post_metafile = PostMetafile(post_id, post_status)

                posts.append((path, post_metafile))

                relative_parts = path.relative_to(photoset.path).parts

                group_metafile = GroupMetafile(group_id=int(group_id))
                group_metafile_path = photoset.path

                if relative_parts[0] in ("justin", "kot_i_kit", "meeting"):
                    group_metafile_path /= relative_parts[0]
                elif relative_parts[0] == "closed":
                    group_metafile_path /= relative_parts[0]
                    group_metafile_path /= relative_parts[1]

                posts.append((group_metafile_path, group_metafile))

        writer = MetafileReadWriter.instance()

        for path, post_metafile in posts:
            new_metafile_path = path / metafile_name

            writer.write(post_metafile, new_metafile_path)

        json_dict["migrated"] = True

        with old_metafile_path.open(mode="w") as metafile_file:
            json.dump(json_dict, metafile_file, indent=4)

        # old_metafile_path.unlink()


class RenameFoldersMigration(PhotosetMigration, ABC):
    @property
    @abstractmethod
    def renamings(self) -> Iterable[Tuple[str, str]]:
        pass

    def migrate(self, photoset: Photoset) -> None:
        for src, dst in self.renamings:
            src_path = photoset.path / src

            if not src_path.exists():
                continue

            dst_path = photoset.path / dst

            if dst_path.exists():
                print(f"{dst_path} already exists, not migrating from {src_path}.")

                continue

            src_path.rename(dst_path)


class ChangeStructureMigration(RenameFoldersMigration):
    @property
    @lru_cache()
    def renamings(self) -> Iterable[Tuple[str, str]]:
        return [
            ("our_people", "my_people",),
            ("selection", "not_signed",),
        ]


class RenamePeopleMigration(RenameFoldersMigration):
    @property
    def renamings(self) -> Iterable[Tuple[str, str]]:
        root = "my_people/"

        people_mapping = [
            ("voloshina", "voloshina_nastya",),
            ("dementyeva", "dementyeva_tanya",),
            ("kravchenko", "kravchenko_nastya",),
        ]

        return [(root + src, root + dst) for src, dst in people_mapping]


class ParseMetafileMigration(PhotosetMigration):
    def migrate(self, photoset: Photoset) -> None:
        if not photoset.folder.has_metafile(PhotosetMetafile):
            photoset.folder.save_metafile(PhotosetMetafile())


ALL_MIGRATIONS = [
    SplitMetafilesMigration.instance(),
    ChangeStructureMigration.instance(),
    ParseMetafileMigration.instance(),
    RenamePeopleMigration.instance(),
]
