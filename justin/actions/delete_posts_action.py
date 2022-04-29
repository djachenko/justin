from argparse import Namespace
from typing import List

from pyvko.models.active_models import Group

from justin.actions.group_action import GroupAction
from justin.shared.context import Context
from justin_utils import util
from justin_utils.cli import Parameter


class DeletePostsAction(GroupAction):
    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("--published", action=Parameter.Action.STORE_TRUE),
        ]

    def perform_for_group(self, group: Group, args: Namespace, context: Context) -> None:
        if args.published:
            characteristic = "published"
        else:
            characteristic = "scheduled"

        if not util.ask_for_permission(
                f"You're about to delete all {characteristic} posts from vk.com/{group.url}. "
                f"You sure?"):
            return

        if args.published:
            if not util.ask_for_permission("This will be noticeable. Are you REALLY sure?"):
                return

            posts = group.get_posts()
        else:
            posts = group.get_scheduled_posts()

        if len(posts) == 0:
            print(f"There are no {characteristic} posts to delete.")

            return

        for post in posts:
            print(f"Deleting post {post.id}... ", end="")

            group.delete_post(post.id)

            print("done.")
