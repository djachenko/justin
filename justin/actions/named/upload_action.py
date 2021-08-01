import random
from argparse import Namespace
from datetime import time, date, datetime, timedelta
from typing import List, Union

from pyvko.models.active_models import Event
from pyvko.models.models import Post
from pyvko.shared.mixins import Wall, Albums, Events

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.models.photoset import Photoset


class UploadAction(NamedAction):
    __STEP = timedelta(days=RearrangeAction.DEFAULT_STEP)
    __DATE_GENERATOR = "date_generator"

    @staticmethod
    def __get_start_date(scheduled_posts: List[Post]) -> date:
        if scheduled_posts:
            scheduled_dates = [post.date for post in scheduled_posts]

            last_date = max(scheduled_dates)
        else:
            last_date = date.today()

        return last_date

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

        print("Performing scheduling... ", end="")

        destinations = [
            part.justin,
            part.closed
        ]

        photoset_metafile = part.get_metafile()

        posted_paths = {url: [post.path for post in posts] for url, posts in photoset_metafile.posts.values()}
        set_name = extra["set_name"]

        for destination in destinations:
            if destination is None:
                continue

            for category in destination.subtrees:
                for post_folder in folder_tree_parts(category):
                    destination_name = destination.name
                    category_name = category.name

                    relative_path = post_folder.path.relative_to(part.path)

                    if relative_path in posted_paths[destination_name]:
                        continue

                    if destination_name == "justin":
                        if set_name != part.name:
                            album_name = ".".join([set_name, part.name])
                        else:
                            album_name = part.name

                        community = context.justin_group

                        self.__upload_folder(community, album_name, post_folder, f"#{category_name}@{community.url}")

                    elif destination_name == "closed":
                        if len(destination.subtrees) == 1:
                            event_name = set_name
                        else:
                            event_name = f"{set_name}_{category_name}"

                        event = self.__get_event(
                            args,
                            extra,
                            destination_name,
                            category_name,
                            context.closed_group,
                            event_name
                        )

                        self.__upload_folder(event, set_name, post_folder)

                    elif destination_name == "meeting":
                        event = self.__get_event(
                            args,
                            extra,
                            destination_name,
                            category_name,
                            context.meeting_group,
                            set_name
                        )

                        self.__upload_folder(event, set_name, post_folder)

    def __get_event(self, args, extra: Extra, dest: str, cat: str, community: Events, set_name: str) -> Event:
        set_context = extra["set_context"]
        dest_context = set_context.get(dest, default={})

        event: Event

        if cat in dest_context:
            event = dest_context[cat]

        elif args.event is not None:
            event_url = args.event

            event = community.get_event(event_url)
        else:
            # todo: handle multiple cats for single set
            event = self.__create_event(community, set_name)

        dest_context[cat] = event
        set_context[dest] = dest_context

        return event

    # noinspection PyMethodMayBeStatic
    def __create_event(self, community: Events, name: str) -> Event:
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

    def __upload_folder(self, event: Union[Wall, Albums], album_name: str, folder: FolderTree, text: str = None):
        if folder.file_count() <= 10:
            self.__upload_to_post(event, folder, text)
        else:
            self.__upload_to_album(event, album_name, folder)

    # noinspection PyMethodMayBeStatic
    def __upload_to_post(self, community: Wall, folder: FolderTree, text: str = None) -> None:
        vk_photos = [community.upload_photo_to_wall(file.path) for file in folder.files]

        folder = Post(
            text=text,
            attachments=vk_photos
        )

        community.add_post(folder)

    # noinspection PyMethodMayBeStatic
    def __upload_to_album(self, community: Albums, name: str, folder: FolderTree) -> None:
        album = community.create_album(name)

        for file in folder.files:
            album.add_photo(file.path)
