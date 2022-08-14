from argparse import Namespace
from datetime import timedelta
from typing import List

from justin_utils.cli import Parameter
from pyvko.entities.user import Group

from justin.actions.rearrange_action import GroupAction
from justin.shared.context import Context


class DelayAction(GroupAction):
    __DEFAULT_DAYS = 1

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("days", type=int)
        ]

    def perform_for_group(self, group: Group, args: Namespace, context: Context) -> None:
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
