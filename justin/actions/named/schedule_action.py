import json
import random
from argparse import Namespace
from datetime import time, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Iterable

from pyvko.attachment.attachment import Attachment
from pyvko.models.group import Group
from pyvko.models.post import Post

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.shared.filesystem import FolderTree, File
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PostStatus
from justin.shared.models.photoset import Photoset, Metafiled


# class PostConfig

class PostTemplate(Metafiled):
    __CONFIG_FILE = "post_config.json"

    def __init__(self, folder: FolderTree) -> None:
        super().__init__()

        assert len(folder.subtrees) == 0

        self.__folder = folder

    @property
    def metafile_path(self) -> Path:
        return self.__folder.path / PostTemplate.__CONFIG_FILE

    @property
    def path(self) -> Path:
        return self.__folder.path

    @property
    def files(self) -> List[File]:
        folder_files = self.__folder.files

        folder_files = [file for file in folder_files if file.name != PostTemplate.__CONFIG_FILE]

        return folder_files

    @property
    @lru_cache()
    def __config(self):
        post_config_path = self.metafile_path

        if not post_config_path.exists():
            return None

        with post_config_path.open() as post_config_file:
            post_config = json.load(post_config_file)

            return post_config

    @property
    def cover(self):
        return self.__config["cover"]

    @property
    def grid(self):
        return self.__config["grid"]


class ScheduleAction(NamedAction):
    __STEP = timedelta(days=RearrangeAction.DEFAULT_STEP)
    __SCHEDULED_POSTS = "scheduled_posts"

    @staticmethod
    def __date_generator(start_date: date):
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

    @staticmethod
    def __get_not_uploaded_hierarchy(part: Photoset, group_url: str) -> Dict[Photoset, Dict[str, List[PostTemplate]]]:
        upload_hierarchy = {}

        justin_folder = part.justin

        photoset_metafile = part.get_metafile()

        posted_paths = [post.path for post in photoset_metafile.posts[group_url]]

        hashtags_to_upload = ScheduleAction.__not_uploaded_hashtags(justin_folder, part.path, posted_paths)

        if len(hashtags_to_upload) > 0:
            upload_hierarchy[part] = hashtags_to_upload

        return upload_hierarchy

    @staticmethod
    def __not_uploaded_hashtags(justin_folder: FolderTree, root_path: Path, posted_paths: List[Path]) \
            -> Dict[str, List[PostTemplate]]:
        hashtags_to_upload = {}

        for hashtag in justin_folder.subtrees:
            parts = folder_tree_parts(hashtag)

            parts_to_upload = ScheduleAction.__not_uploaded_parts(parts, root_path, posted_paths)

            if len(parts_to_upload) > 0:
                hashtags_to_upload[hashtag.name] = parts_to_upload

        return hashtags_to_upload

    @staticmethod
    def __not_uploaded_parts(parts: Iterable[FolderTree], root_path: Path, posted_paths: List[Path]) \
            -> List[PostTemplate]:
        parts_to_upload = []

        for justin_part in parts:
            part_path = justin_part.path.relative_to(root_path)

            if part_path not in posted_paths:
                post_template = PostTemplate(justin_part)

                parts_to_upload.append(post_template)

        return parts_to_upload

    def get_extra(self, context: Context) -> Extra:
        return {
            ScheduleAction.__SCHEDULED_POSTS: context.group.get_scheduled_posts()
        }

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:

        scheduled_posts = extra[ScheduleAction.__SCHEDULED_POSTS]
        group = context.group

        last_date = ScheduleAction.__get_start_date(scheduled_posts)
        date_generator = ScheduleAction.__date_generator(last_date)

        print("Performing scheduling... ", end="")

        upload_hierarchy = ScheduleAction.__get_not_uploaded_hierarchy(part, group.url)

        if len(upload_hierarchy) > 0:
            print()
        else:
            print("already done.")

            return

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
    def __get_simple_attachments(self, group, photo_files) -> List[Attachment]:
        vk_photos = [group.upload_photo_to_wall(file.path) for file in photo_files]

        return vk_photos

    # noinspection PyMethodMayBeStatic
    def __get_report_attachments(self, group: Group, set_name: str, folder: PostTemplate) -> List[Attachment]:
        album = group.create_album(set_name)

        cover = folder.cover
        grid_stems = folder.grid

        assert cover not in grid_stems

        photos = {}

        for file in folder.files:
            photo = album.add_photo(file.path)

            if file.stem() == cover:
                album.set_cover(photo)

            if file.stem() in grid_stems:
                photos[file.stem()] = photo

        sorted_photos = [photos[stem] for stem in grid_stems]

        # noinspection PyTypeChecker
        return sorted_photos + [album]

    @staticmethod
    def __get_start_date(scheduled_posts: List[Post]) -> date:
        scheduled_dates = [post.date for post in scheduled_posts]

        scheduled_dates.sort(reverse=True)

        if len(scheduled_dates) > 0:
            last_date = scheduled_dates[0].date()
        else:
            last_date = date.today()

        return last_date
