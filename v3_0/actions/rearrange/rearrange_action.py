from argparse import Namespace
from datetime import timedelta, datetime

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.shared.models.world import World


class RearrangeAction(Action):
    DEFAULT_STEP = 3

    def perform(self, args: Namespace, world: World, group: Group) -> None:
        print("Performing rearrange... ", end="")

        scheduled_posts = group.get_scheduled_posts()

        if len(scheduled_posts) < 2:
            return

        step_value_in_days = args.step

        if step_value_in_days is None:
            step_value_in_days = RearrangeAction.DEFAULT_STEP

        step = timedelta(days=step_value_in_days)
        earliest_date = scheduled_posts[0].date.date()

        new_dates = [earliest_date + step * index for index in range(len(scheduled_posts))]

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

            group.update_post(post)

            print("success.")
