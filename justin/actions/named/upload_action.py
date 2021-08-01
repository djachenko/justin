import random
from argparse import Namespace
from datetime import time, date, datetime, timedelta
from typing import List

from pyvko.models.active_models import Event
from pyvko.models.models import Post
from pyvko.shared.mixins import Wall, Albums

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
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

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        extra.update({
            "set_name": photoset.name,
            "set_context": {}
        })

        super().perform_for_photoset(photoset, args, context, extra)

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
                for part_folder in folder_tree_parts(category):
                    to_upload.append((destination.name, category.name, part_folder))

        photoset_metafile = part.get_metafile()

        posted_paths = {url: [post.path for post in posts] for url, posts in photoset_metafile.posts.values()}
        set_name = extra["set_name"]

        for dest, cat, part_folder in to_upload:
            relative_path = part_folder.path.relative_to(part.path)

            if relative_path in posted_paths[dest]:
                continue

            if dest == "justin":
                community = context.justin_group

                if part_folder.file_count() > 10:
                    part_name = part.name

                    if set_name != part_name:
                        part_name = ".".join([set_name, part_name])

                    self.__upload_to_album(community, part_name, part_folder)
                else:
                    self.__upload_to_post(
                        community,
                        part_folder,
                        text=f"#{cat}@{community.url}"
                    )


            elif dest == "closed":

                community = context.closed_group
                set_context = extra["set_context"]

                event: Event

                if cat in set_context:
                    event = set_context[cat]

                elif args.event is not None:
                    event_url = args.event

                    event = community.get_event(event_url)
                else:
                    event = self.__create_event(community, set_name)

                if part_folder.file_count() > 10:
                    self.__upload_to_album(event, set_name, part_folder)
                else:
                    self.__upload_to_post(event, part_folder)

                set_context[cat] = event

            elif dest == "meeting":
                community = context.meeting_group

                event = self.__create_event(community, set_name)

                if part_folder.file_count() <= 10:  # todo: check for multiple photographers
                    self.__upload_to_post(event, part_folder)
                else:
                    self.__upload_to_album(event, part.name, part_folder)

    # noinspection PyMethodMayBeStatic
    def __create_event(self, community, name) -> Event:
        event = community.create_event(name)

        event.event_category = Event.Category.CIRCUS

        for section in Event.Section:
            event.set_section_state(section, Event.SectionState.DISABLED)

        event.set_section_state(Event.Section.PHOTOS, Event.SectionState.LIMITED)
        event.set_section_state(Event.Section.WALL, Event.SectionState.LIMITED)
        event.is_closed = True
        event.main_section = Event.Section.PHOTOS

        event.save()

        return event

    # noinspection PyMethodMayBeStatic
    def __upload_to_post(self, community: Wall, post: FolderTree, text: str = None) -> None:
        vk_photos = [community.upload_photo_to_wall(file.path) for file in post.files]

        post = Post(
            text=text,
            attachments=vk_photos
        )

        community.add_post(post)

    # noinspection PyMethodMayBeStatic
    def __upload_to_album(self, community: Albums, name: str, folder: FolderTree) -> None:
        album = community.create_album(name)

        for file in folder.files:
            album.add_photo(file.path)

    @staticmethod
    def __get_start_date(scheduled_posts: List[Post]) -> date:
        if scheduled_posts:
            scheduled_dates = [post.date for post in scheduled_posts]

            last_date = max(scheduled_dates)
        else:
            last_date = date.today()

        return last_date
