from argparse import Namespace
from datetime import timedelta, datetime

from pyvko.group.group import Group
from pyvko.photos.photos_uploader import PhotosUploader

from v3_0.actions.action import Action
from v3_0.shared.models.world import World


class RearrangeAction(Action):
    DEFAULT_STEP = 3

    def perform(self, args: Namespace, world: World, group: Group, uploader: PhotosUploader) -> None:
        scheduled_posts = group.get_scheduled_posts()

        if len(scheduled_posts) < 2:
            return

        step_value_in_days = args.step

        if step_value_in_days is None:
            step_value_in_days = RearrangeAction.DEFAULT_STEP

        step = timedelta(days=step_value_in_days)

        earliest_date = scheduled_posts[0].date.date()

        indexed_posts = list(enumerate(scheduled_posts))[1:]
        reversed_posts = reversed(indexed_posts)  # this is needed because last posts may occupy the same time

        for index, post in reversed_posts:
            new_date = earliest_date + step * index
            new_time = post.date.time()

            new_datetime = datetime.combine(new_date, new_time)

            post.date = new_datetime

            group.update_post(post)
