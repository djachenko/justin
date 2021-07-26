from argparse import Namespace
from datetime import timedelta

from justin.actions.action import Action
from justin.shared.context import Context


class DelayAction(Action):
    DEFAULT_DAYS = 1

    def perform(self, args: Namespace, context: Context) -> None:
        group = context.group

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
