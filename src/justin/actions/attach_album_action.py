from argparse import Namespace

from justin.actions.destinations_aware_action import DestinationsAwareAction
from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.metafiles.metafile import PostMetafile, AlbumMetafile, PostStatus, GroupMetafile
from pyvko.aspects.albums import Albums
from pyvko.aspects.posts import Posts


class AttachAlbumAction2(DestinationsAwareAction):
    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        if PostMetafile.has(folder) and AlbumMetafile.has(folder):
            AttachAlbumAction2.__run(context.default_group, folder)
        else:
            super().perform_for_folder(folder, args, context, extra)

    def handle_justin(self, justin_folder: Folder, context: Context, extra: Extra) -> None:
        self.handle_tagged_folder(justin_folder, context, extra)

    def handle_closed(self, closed_folder: Folder, context: Context, extra: Extra) -> None:
        for name_folder in closed_folder.subfolders:
            group_metafile = GroupMetafile.get(name_folder)

            if not group_metafile or not AlbumMetafile.has(name_folder):
                continue

            group = context.pyvko.get_event(group_metafile.group_id)

            AttachAlbumAction2.__run(group, name_folder)

    def handle_common(self, folder: Folder, context: Context, extra: Extra) -> None:
        pass

    def handle_tag_part(self, tag_part_folder: Folder, context: Context, extra: Extra) -> None:
        if PostMetafile.has(tag_part_folder) and AlbumMetafile.has(tag_part_folder):
            AttachAlbumAction2.__run(context.default_group, tag_part_folder)

    @staticmethod
    def __run(group: Posts | Albums, folder: Folder) -> None:
        post_metafile = PostMetafile.get(folder)
        album_metafile = AlbumMetafile.get(folder)

        assert post_metafile
        assert album_metafile
        assert post_metafile.status is not PostStatus.PUBLISHED

        album = group.get_album_by_id(album_metafile.album_id)
        post = group.get_post(post_metafile.post_id)

        post.text = post.text.strip()
        post.text += f"\n\nА фотки лежат [{album.url}|вот здесь]."
        post.text = post.text.strip()

        group.update_post(post)
