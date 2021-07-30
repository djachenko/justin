import random
from argparse import Namespace
from datetime import time, date, datetime, timedelta
from typing import List

from pyvko.attachment.attachment import Attachment
from pyvko.models.active_models import Group, Event
from pyvko.models.models import Post
from pyvko.shared.mixins import Wall, Albums

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PostStatus
from justin.shared.models.photoset import Photoset


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
                for photos_folder in folder_tree_parts(category):
                    to_upload.append((destination.name, category.name, photos_folder))

        photoset_metafile = part.get_metafile()

        posted_paths = {url: [post.path for post in posts] for url, posts in photoset_metafile.posts.values()}

        for dest, cat, photos_folder in to_upload:
            relative_path = photos_folder.path.relative_to(part.path)

            if relative_path in posted_paths[dest]:
                continue

            if dest == "justin":
                community = context.justin_group

                if photos_folder.file_count() > 10:
                    attach = self.__get_report_attachments(community, part.name, photos_folder)
                else:
                    attach = self.__get_simple_attachments(community, photos_folder)

                photos_folder = Post(
                    text=f"#{cat}@{community.url}",
                    attachments=attach
                )

                community.add_post(photos_folder)

            elif dest == "closed":
                community = context.closed_group

                event = community.create_event(part.name)

                event.event_category = Event.Category.CIRCUS

                for section in Event.Section:
                    event.set_section_state(section, Event.SectionState.DISABLED)

                event.set_section_state(Event.Section.PHOTOS, Event.SectionState.LIMITED)
                event.set_section_state(Event.Section.WALL, Event.SectionState.LIMITED)
                event.is_closed = True
                event.main_section = Event.Section.PHOTOS

                event.save()

                community = event

                if photos_folder.file_count() > 10:
                    attach = self.__get_report_attachments(community, part.name, photos_folder)
                else:
                    attach = self.__get_simple_attachments(community, photos_folder)

                photos_folder = Post(
                    attachments=attach
                )

                community.add_post(photos_folder)

            elif dest == "meeting":
                community = context.meeting_group

                if photos_folder.file_count() <= 10:  # todo: check for multiple photographers
                    attach = self.__get_simple_attachments(community, photos_folder)
                else:
                    event = community.create_event(part.name)

                    event.event_category = Event.Category.CIRCUS

                    for section in Event.Section:
                        event.set_section_state(section, Event.SectionState.DISABLED)

                    event.set_section_state(Event.Section.PHOTOS, Event.SectionState.LIMITED)
                    event.set_section_state(Event.Section.WALL, Event.SectionState.LIMITED)
                    event.is_closed = True
                    event.main_section = Event.Section.PHOTOS

                    event.save()

                    community = event

                    attach = self.__get_report_attachments(community, part.name, photos_folder)

                post = Post(
                    attachments=attach
                )

                community.add_post(post)

    # noinspection PyMethodMayBeStatic
    def __get_simple_attachments(self, community: Wall, post: FolderTree) -> List[Attachment]:
        vk_photos = [community.upload_photo_to_wall(file.path) for file in post.files]

        return vk_photos

    # noinspection PyMethodMayBeStatic
    def __get_report_attachments(self, community: Albums, name: str, folder: FolderTree) -> List[Attachment]:
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
