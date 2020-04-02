from argparse import Namespace
from datetime import timedelta

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.shared.models.world import World


class DelayAction(Action):
    DEFAULT_DAYS = 1

    def perform(self, args: Namespace, world: World, group: Group) -> None:
        posts = group.get_scheduled_posts()

        delay_days = args.days

        delay = timedelta(days=delay_days)

        print(f"Delaying posts for {delay}...")

        for post in posts:
            old_date = post.date
            new_date = old_date + delay

            print(f"Moving post {post.id} from {old_date} to {new_date}...", end="")

            post.date = new_date

            group.update_post(post)

            print(" done.")
