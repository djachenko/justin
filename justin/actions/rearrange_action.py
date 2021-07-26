import random
from argparse import Namespace
from datetime import timedelta, datetime

from justin.actions.action import Action
from justin.shared.context import Context


class RearrangeAction(Action):
    DEFAULT_STEP = 1

    def perform(self, args: Namespace, context: Context) -> None:
        print("Performing rearrange... ", end="")

        scheduled_posts = context.group.get_scheduled_posts()

        if len(scheduled_posts) < 2:
            return

        step_value_in_days = args.step

        if step_value_in_days is None:
            step_value_in_days = RearrangeAction.DEFAULT_STEP

        step = timedelta(days=step_value_in_days)

        dates = [post.date.date() for post in scheduled_posts]
        earliest_date = min(dates)

        new_dates = [earliest_date + step * index for index in range(len(scheduled_posts))]

        if args.shuffle:
            random.shuffle(scheduled_posts)

        dates_and_posts = list(zip(new_dates, scheduled_posts))[1:]

        reversed_posts = reversed(dates_and_posts)  # this is needed because last posts may occupy the same time

        posts_to_move = [(date, post) for date, post in reversed_posts if date != post.date.date()]

        if len(posts_to_move) == 0:
            print("no need.")

            return

        print()

        for new_date, post in posts_to_move:
            old_date = post.date.date()

            print(f"Moving post {post.id} from {old_date} to {new_date}...")

            new_time = post.date.time()

            new_datetime = datetime.combine(new_date, new_time)

            post.date = new_datetime

            context.group.update_post(post)

            print("success.")
