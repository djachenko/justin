from argparse import Namespace
from typing import List

from justin.actions.group_action import GroupAction
from justin.shared.context import Context
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
