import json
from abc import abstractmethod
from pathlib import Path

from justin.shared.filesystem import FolderTree
from justin.shared.metafile import PostStatus, PostMetafile, MetafileReadWriter, GroupMetafile
from justin.shared.models.photoset import Photoset
from justin.shared.metafile import Json


class PhotosetMigration:
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

        if "migrated" in json_dict and json_dict["migrated"]:
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


class RenameFoldersMigration(PhotosetMigration):
    def migrate(self, photoset: Photoset) -> None:
        renamings = [
            ("our_people", "my_people",),
            ("selection", "not_signed",),
        ]

        for src, dst in renamings:
            src_tree = photoset.tree[src]

            if src_tree is None:
                continue

            src_tree.rename(dst)


ALL_MIGRATIONS = [
    SplitMetafilesMigration(),
    RenameFoldersMigration(),
]


def main():
    migration = SplitMetafilesMigration()

    migration.migrate(
        Photoset(FolderTree(Path("C:/Users/justin/photos/stages/stage3.schedule/21.12.18.loading_party"))))


if __name__ == '__main__':
    main()
