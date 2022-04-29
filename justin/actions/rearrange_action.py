import random
from argparse import Namespace
from datetime import timedelta, datetime
from functools import lru_cache
from typing import List

from pyvko.models.active_models import Group

from justin.actions.group_action import GroupAction
from justin_utils.cli import Context, Parameter
from justin_utils.util import parse_time, random_date


class RearrangeAction(GroupAction):
    DEFAULT_STEP = 1

    @property
    @lru_cache()
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("--step", type=int, default=RearrangeAction.DEFAULT_STEP),
            Parameter("--shuffle", action=Parameter.Action.STORE_TRUE),
            Parameter("--no-date", action=Parameter.Action.STORE_TRUE),
            Parameter("--time", action=Parameter.Action.STORE_TRUE),
            Parameter("--start_time", type=parse_time, default="00:00:00"),
            Parameter("--end_time", type=parse_time, default="23:59:59"),
        ]

    def perform_for_group(self, group: Group, args: Namespace, context: Context) -> None:
        print("Performing rearrange... ", end="")

        step_value_in_days = args.step

        scheduled_posts = group.get_scheduled_posts()

        if len(scheduled_posts) < 2:
            return

        step = timedelta(days=step_value_in_days)

        dates = [post.date.date() for post in scheduled_posts]
        times = [post.date.time() for post in scheduled_posts]

        if not args.no_date:
            earliest_date = min(dates)

            new_dates = [earliest_date + step * index for index in range(len(scheduled_posts))]
        else:
            new_dates = dates

        if args.time:
            new_times = list(random_date(args.start_time, args.end_time, len(times)))
        else:
            new_times = times

        if args.shuffle:
            random.shuffle(new_dates)

        dates_and_posts = list(zip(new_dates, new_times, scheduled_posts))

        reversed_posts = reversed(dates_and_posts)  # this is needed because last posts may occupy the same time

        posts_to_move = []

        for post_date, post_time, post in reversed_posts:
            if post_date != post.date.date() or post_time != post.date.time():
                posts_to_move.append((post_date, post_time, post))

        # list(filter(lambda d, t, p: d != p.date.date() or t != p.date.time(), reversed_posts))
        # [(date, t, post) for date, t, post in reversed_posts if True or date != post.date.date()]

        if len(posts_to_move) == 0:
            print("no need.")

            return

        print()

        for new_date, new_time, post in posts_to_move:
            old_date = post.date.date()

            print(f"Moving post {post.id} from {old_date} to {new_date}...")

            new_datetime = datetime.combine(new_date, new_time)

            post.date = new_datetime

            group.update_post(post)

            print("success.")
