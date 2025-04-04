from argparse import Namespace
from typing import List

from justin.actions.destinations_aware_action import DestinationsAwareAction
from justin.actions.group_action import GroupAction
from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.metafile import MetaFolder, PostMetafile, AlbumMetafile, PostStatus
from justin_utils.cli import Parameter
from pyvko.aspects.groups import Group


class AppendAlbumAction(GroupAction):
    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(name="post_id", type=int),
            Parameter(name="album_id", type=int),
        ]

    def perform_for_group(self, group: Group, args: Namespace, context: Context) -> None:
        album_id: int = args.album_id
        post_id: int = args.post_id

        album = group.get_album_by_id(album_id)

        if album is None:
            print(f"Album with id {album_id} not found in {group.name}.")

            return

        post = group.get_post(post_id)

        if post is None:
            print(f"Post with id {post_id} not found in {group.name}.")

            return

        post.attachments.append(album)

        group.update_post(post)


class AppendAlbumAction2(DestinationsAwareAction):
    def perform_for_folder(self, folder: MetaFolder, args: Namespace, context: Context, extra: Extra) -> None:
        if folder.has_metafile(PostMetafile) and folder.has_metafile(AlbumMetafile):
            AppendAlbumAction2.__run(context.default_group, folder)
        else:
            super().perform_for_folder(folder, args, context, extra)

    def handle_justin(self, justin_folder: MetaFolder, context: Context, extra: Extra) -> None:
        self.handle_tagged_folder(justin_folder, context, extra)

    def handle_tag_part(self, tag_part_folder: MetaFolder, context: Context, extra: Extra) -> None:
        if tag_part_folder.has_metafile(PostMetafile) and tag_part_folder.has_metafile(AlbumMetafile):
            AppendAlbumAction2.__run(context.default_group, tag_part_folder)

    @staticmethod
    def __run(group: Group, folder: MetaFolder) -> None:
        post_metafile = folder.get_metafile(PostMetafile)
        album_metafile = folder.get_metafile(AlbumMetafile)

        assert post_metafile
        assert album_metafile
        assert post_metafile.status is not PostStatus.PUBLISHED

        album = group.get_album_by_id(album_metafile.album_id)
        post = group.get_post(post_metafile.post_id)

        assert album not in post.attachments

        post.attachments.append(album)
        group.update_post(post)
