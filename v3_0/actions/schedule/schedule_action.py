import random
from argparse import Namespace
from datetime import time, date, datetime, timedelta
from pathlib import Path
from typing import List

from pyvko.group.group import Group
from pyvko.photos.photos_uploader import PhotosUploader
from pyvko.post import Post

from v3_0.actions.action import Action
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.shared.metafiles.post_metafile import PostMetafile
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class ScheduleAction(Action):
    __STEP = timedelta(days=3)

    # noinspection PyMethodMayBeStatic
    def __tree_with_sets(self) -> FolderTree:
        ready_path = Path("D:/photos/stages/stage3.schedule")
        # todo: stages_region[stage3.schedule]

        stage_tree = SingleFolderTree(ready_path)

        return stage_tree

    @staticmethod
    def __filter_existing_posts(post_metafiles: List[PostMetafile], existing_ids: List[int]):
        existing_posts = []

        for post_metafile in post_metafiles:
            if post_metafile.post_id in existing_ids:
                existing_posts.append(post_metafile)

        return existing_posts

    @staticmethod
    def date_generator(start_date: date):
        counter = 1

        while True:
            post_date = start_date + ScheduleAction.__STEP * counter
            post_time = time(
                hour=random.randint(8, 23),
                minute=random.randint(0, 59),
            )

            post_datetime = datetime.combine(post_date, post_time)

            counter += 1

            yield post_datetime

    def perform(self, args: Namespace, world: World, group: Group, photo_uploader: PhotosUploader) -> None:
        stage_tree = self.__tree_with_sets()

        photosets = [Photoset(subtree) for subtree in stage_tree.subtrees]

        scheduled_posts = group.get_scheduled_posts()

        last_date = ScheduleAction.get_start_date(scheduled_posts)
        date_generator = ScheduleAction.date_generator(last_date)

        published_posts = group.get_posts()

        all_post_ids = [post.id for post in scheduled_posts + published_posts]

        for photoset in photosets:
            justin_folder = photoset.justin

            photoset_metafile = photoset.get_metafile()

            existing_posts = self.__filter_existing_posts(photoset_metafile.posts, all_post_ids)

            photoset_metafile.posts = existing_posts
            photoset.save_metafile(photoset_metafile)

            posted_paths = [post.path for post in existing_posts]

            new_posts = []

            for hashtag in justin_folder.subtrees:
                parts = PartingHelper.folder_tree_parts(hashtag)

                for part in parts:
                    part_path = part.path.relative_to(photoset.path)

                    if part_path in posted_paths:
                        continue

                    assert len(part.subtrees) == 0

                    photo_files = part.files

                    vk_photos = [photo_uploader.upload_to_wall(group.id, file.path) for file in
                                 photo_files]

                    post_datetime = next(date_generator)

                    post = Post(
                        text=f"#{hashtag.name}@djachenko",
                        attachments=vk_photos,
                        date=post_datetime
                    )

                    post_id = group.add_post(post)

                    post_metafile = PostMetafile(part_path, post_id)

                    new_posts.append(post_metafile)

                    print(post_id)

            photoset_metafile.posts += new_posts

            photoset.save_metafile(photoset_metafile)

    @staticmethod
    def get_start_date(scheduled_posts: List[Post]) -> date:
        scheduled_dates = [post.date for post in scheduled_posts]

        scheduled_dates.sort(reverse=True)

        if len(scheduled_dates) > 0:
            last_date = scheduled_dates[0].date()
        else:
            last_date = date.today()

        return last_date
