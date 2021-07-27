import random
from argparse import Namespace
from datetime import time, date, datetime, timedelta
from typing import List

from pyvko.attachment.attachment import Attachment
from pyvko.models.active_models import Group
from pyvko.models.models import Post

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PostStatus
from justin.shared.models.photoset import Photoset


# class PostConfig


class UploadAction(NamedAction):
    __STEP = timedelta(days=RearrangeAction.DEFAULT_STEP)
    __DATE_GENERATOR = "date_generator"

    @staticmethod
    def __date_generator(start_date: date):
        counter = 1

        while True:
            post_date = start_date + UploadAction.__STEP * counter
            post_time = time(
                hour=random.randint(8, 23),
                minute=random.randint(0, 59),
            )

            post_datetime = datetime.combine(post_date, post_time)

            counter += 1

            yield post_datetime

    def get_extra(self, context: Context) -> Extra:
        scheduled_posts = context.default_group.get_scheduled_posts()
        last_date = UploadAction.__get_start_date(scheduled_posts)
        date_generator = UploadAction.__date_generator(last_date)

        return {
            **super().get_extra(context),
            **{
                UploadAction.__DATE_GENERATOR: date_generator
            },
        }

    def upload_post(self):
        pass

    def upload_to_album(self):
        pass

    def upload_to_group(self):
        pass

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        date_generator = extra[UploadAction.__DATE_GENERATOR]

        group = context.default_group

        print("Performing scheduling... ", end="")

        destinations = [
            part.justin,
            part.closed
        ]

        to_upload = []

        for destination in destinations:
            if destination is None:
                continue

            for category in destination.subtrees:
                for post in folder_tree_parts(category):
                    to_upload.append((destination.name, category.name, post))

        photoset_metafile = part.get_metafile()

        posted_paths = {url: [post.path for post in posts] for url, posts in photoset_metafile.posts.values()}

        for dest, cat, post in to_upload:
            relative_path = post.path.relative_to(part.path)

            if relative_path in posted_paths[dest]:
                continue

            if dest == "closed":
                community = context.default_group  # .create_event(path.name)
            else:
                community = context.default_group

            if len(post.files) > 10:
                # upload to album
                attachments = self.__get_report_attachments(community, part.name, post)
            else:
                attachments = self.__get_simple_attachments(community, post)

            post = Post(
                attachments=attachments
            )

            community.add_post(post)

        # todo: replace nested loops with one
        for part, hashtags in upload_hierarchy.items():
            print(f"Uploading photoset {part.name}")

            photoset_metafile = part.get_metafile()

            for hashtag, parts in hashtags.items():
                print(f"Uploading #{hashtag}")

                for post_template in parts:
                    part_path = post_template.path.relative_to(part.path)

                    print(f"Uploading contents of {part_path}... ", end="", flush=True)

                    photo_files = post_template.files

                    if hashtag != "report":
                        attachments = self.__get_simple_attachments(group, photo_files)
                    else:
                        attachments = self.__get_report_attachments(group, part.name, post_template)

                    post_datetime = next(date_generator)

                    post = Post(
                        text=f"#{hashtag}@{group.url}",
                        attachments=attachments,
                        date=post_datetime
                    )

                    post_id = group.add_post(post)

                    post_metafile = PostMetafile(
                        path=part_path,
                        post_id=post_id,
                        status=PostStatus.SCHEDULED
                    )

                    photoset_metafile.posts[group.url].append(post_metafile)
                    part.save_metafile(photoset_metafile)

                    print(f"successful, new post has id {post_id}")

    # noinspection PyMethodMayBeStatic
    def __get_simple_attachments(self, community: Group, post: FolderTree) -> List[Attachment]:
        vk_photos = [community.upload_photo_to_wall(file.path) for file in post.files]

        return vk_photos

    # noinspection PyMethodMayBeStatic
    def __get_report_attachments(self, community: Group, name: str, folder: FolderTree) -> List[Attachment]:
        album = community.create_album(name)

        for file in folder.files:
            album.add_photo(file.path)

        return [album]

    @staticmethod
    def __get_start_date(scheduled_posts: List[Post]) -> date:
        scheduled_dates = [post.date for post in scheduled_posts]

        scheduled_dates.sort(reverse=True)

        if len(scheduled_dates) > 0:
            last_date = scheduled_dates[0].date()
        else:
            last_date = date.today()

        return last_date
