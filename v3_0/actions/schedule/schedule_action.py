import random
from argparse import Namespace
from datetime import time, date, datetime, timedelta
from pathlib import Path
from typing import List, Generator

from pyvko.models.group import Group
from pyvko.models.post import Post

from v3_0.actions.action import Action
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.shared.metafiles.post_metafile import PostMetafile, PostStatus
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

    def perform(self, args: Namespace, world: World, group: Group) -> None:
        stage_tree = self.__tree_with_sets()

        photosets = [Photoset(subtree) for subtree in stage_tree.subtrees]

        scheduled_posts = group.get_scheduled_posts()

        last_date = ScheduleAction.get_start_date(scheduled_posts)
        date_generator = ScheduleAction.date_generator(last_date)

        print("Performing upload")

        for photoset in photosets:
            print(f"Uploading photoset {photoset.name}")

            justin_folder = photoset.justin

            photoset_metafile = photoset.get_metafile()

            posted_paths = [post.path for post in photoset_metafile.posts]

            new_posts = []

            for hashtag in justin_folder.subtrees:
                print(f"Uploading #{hashtag.name}")

                parts = PartingHelper.folder_tree_parts(hashtag)

                for part in parts:
                    part_path = part.path.relative_to(photoset.path)

                    if part_path in posted_paths:
                        continue

                    print(f"Uploading contents of {part_path}... ", end="")

                    assert len(part.subtrees) == 0

                    photo_files = part.files

                    vk_photos = [group.upload_photo_to_wall(file.path) for file in photo_files]

                    post_datetime = next(date_generator)

                    post = Post(
                        text=f"#{hashtag.name}@{group.url}",
                        attachments=vk_photos,
                        date=post_datetime
                    )

                    post_id = group.add_post(post)

                    post_metafile = PostMetafile(part_path, post_id, PostStatus.SCHEDULED)

                    new_posts.append(post_metafile)

                    print(f"successful, new post has id {post_id}")

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
