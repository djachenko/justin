from argparse import Namespace
from random import shuffle

from justin.actions.pattern_action import PatternAction, Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.metafiles.metafile import PostMetafile, AlbumMetafile, GroupMetafile


class PopulateAction(PatternAction):
    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        post_metafile = PostMetafile.get(folder)
        album_metafile = AlbumMetafile.get(folder)
        group_metafile = GroupMetafile.get(folder)

        group = context.pyvko.get(group_metafile.group_id)
        album = group.get_album_by_id(album_metafile.album_id)
        post = group.get_post(post_metafile.post_id)

        photos = album.get_photos()
        photo_indices = list(range(len(photos)))

        existing_attachments = post.attachments

        while True:
            shuffle(photo_indices)

            indices_for_post = photo_indices[:9 - len(existing_attachments)]
            indices_for_post.sort()
            photos_for_post = [photos[i] for i in indices_for_post]

            post.attachments = existing_attachments + photos_for_post

            group.update_post(post)

            if input("ok? > "):
                break
