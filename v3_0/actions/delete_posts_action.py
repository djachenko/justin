from argparse import Namespace

from pyvko.models.group import Group
from v3_0.shared.helpers import util

from v3_0.actions.action import Action
from v3_0.shared.models.world import World


class DeletePostsAction(Action):
    def perform(self, args: Namespace, world: World, group: Group) -> None:
        if args.published:
            posts = group.get_posts()

            characteristic = "published"
        else:
            posts = group.get_scheduled_posts()

            characteristic = "scheduled"

        if len(posts) == 0:
            print(f"There are no {characteristic} posts to delete.")

            return

        if not util.ask_for_permission(f"You're about to delete all {characteristic} posts from vk.com/{group.url}. "
                                       f"You sure?"):
            return

        if args.published:
            if not util.ask_for_permission("This will be noticeable. Are you REALLY sure?"):
                return

        for post in posts:
            print(f"Deleting post {post.id}... ", end="")

            group.delete_post(post.id)

            print("done.")
