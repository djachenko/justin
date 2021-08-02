import random
from argparse import Namespace
from dataclasses import dataclass
from datetime import time, date, datetime, timedelta
from typing import List, Union, Optional, Iterator

from py_linq import Enumerable
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
    __JUSTIN_DATE_GENERATOR = "date_generator"

    # region date generator

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
                hour=random.randint(17, 23),
                minute=random.randint(0, 59),
            )

            post_datetime = datetime.combine(post_date, post_time)

            counter += 1

            yield post_datetime

    @staticmethod
    def __generator_for_group(group: Wall):
        scheduled_posts = group.get_scheduled_posts()
        last_date = UploadAction.__get_start_date(scheduled_posts)
        date_generator = UploadAction.__date_generator(last_date)

        return date_generator

    # endregion date generator

    def get_extra(self, context: Context) -> Extra:
        return {
            **super().get_extra(context),
            **{
                UploadAction.__JUSTIN_DATE_GENERATOR: UploadAction.__generator_for_group(context.justin_group)
            },
        }

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        names = Enumerable(folder_tree_parts(photoset.tree)) \
            .select(lambda p: p.closed) \
            .where(lambda e: e is not None) \
            .select_many(lambda p: p.subtrees) \
            .select(lambda p: p.name) \
            .to_list()

        names_count = {}

        for name in names:
            names_count[name] = names_count.get(name, default=0) + 1

        extra.update({
            "set_name": photoset.name,
            "set_context": {},
            "closed_names": names_count,
        })

        super().perform_for_photoset(photoset, args, context, extra)

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:

        print("Performing scheduling... ", end="")

        destinations = [
            part.justin,
            part.closed
        ]

        photoset_metafile = part.get_metafile()

        posted_paths = {url: [post.path for post in posts] for url, posts in photoset_metafile.posts.values()}
        extra["posted_paths"] = posted_paths

        for destination in destinations:
            if destination is None:
                continue

            if destination.name == "justin":
                self.__upload_justin(
                    folder=destination,
                    context=context,
                    extra=extra,
                    part=part
                )
            elif destination.name == "closed":
                self.__upload_closed(
                    folder=destination,
                    context=context,
                    extra=extra
                )
            elif destination.name == "meeting":
                self.__upload_meeting(
                    folder=destination,
                    context=context,
                    extra=extra
                )

            # todo: metafile

    # region upload strategies

    def __upload_justin(self, folder: FolderTree, context: Context, extra: Extra, part: Photoset):
        community = context.justin_group
        set_name = extra["set_name"]
        date_generator = extra[UploadAction.__JUSTIN_DATE_GENERATOR]

        if set_name != part.name:
            album_name = ".".join([set_name, part.name])
        else:
            album_name = part.name

        for category in folder.subtrees:
            params = UploadAction.UploadParams(
                album_name=album_name,
                text=f"#{category.name}@{context.justin_group.url}",
                date_generator=date_generator
            )

            for post_folder in folder_tree_parts(category):
                self.__upload_folder(community, post_folder, params)

    def __upload_closed(self, folder: FolderTree, context: Context, extra: Extra):
        set_context = extra["set_context"]
        set_name = extra["set_name"]

        names_count = extra["closed_names"]

        for name in folder.subtrees:
            if names_count[name.name] > 1:
                event_name = set_name
            else:
                event_name = f"{set_name}_{name.name}"

            event = self.__get_event(
                community=context.closed_group,
                context=set_context,
                params=UploadAction.EventParams(
                    destination=folder.name,
                    category=name.name,
                    event_name=event_name
                ))

            date_generator = UploadAction.__generator_for_group(event)

            for post_folder in folder_tree_parts(name):
                self.__upload_folder(event, post_folder, UploadAction.UploadParams(
                    album_name=set_name,
                    date_generator=date_generator
                ))

    def __upload_meeting(self, folder: FolderTree, context: Context, extra: Extra):
        set_context = extra["set_context"]
        set_name = extra["set_name"]

        event = self.__get_event(
            community=context.meeting_group,
            context=set_context,
            params=UploadAction.EventParams(
                destination=folder.name,
                event_name=set_name
            ))

        date_generator = UploadAction.__generator_for_group(event)

        for post_folder in folder_tree_parts(folder):
            self.__upload_folder(event, post_folder, UploadAction.UploadParams(
                album_name=set_name,
                date_generator=date_generator
            ))

    # endregion upload strategies

    # region event

    @dataclass
    class EventParams:
        destination: str
        event_name: str
        category: Optional[str] = None

    def __get_event(self, community: Events, context: Extra, params: EventParams) -> Event:
        destination = params.destination

        if params.category is not None:
            context[destination] = context.get(destination, default={})

            context = context[destination]
            key = params.category
        else:
            key = destination

        if key not in context:
            event_url = input("Please input event url: ")

            event = community.get_event(event_url)

            if event is None:
                event = self.__create_event(community, params.event_name)

            context[key] = event

        return context[key]

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

    # endregion event

    # region uploading

    @dataclass
    class UploadParams:
        album_name: str
        date_generator: Iterator[datetime]
        text: Optional[str] = None

    def __upload_folder(self, community: Union[Wall, Albums], folder: FolderTree, params: UploadParams):
        if folder.file_count() <= 10:
            self.__upload_to_post(community, folder, params)
        else:
            self.__upload_to_album(community, folder, params)

    # noinspection PyMethodMayBeStatic
    def __upload_to_post(self, community: Wall, folder: FolderTree, params: UploadParams) -> None:
        vk_photos = [community.upload_photo_to_wall(file.path) for file in folder.files]

        folder = Post(
            text=params.text,
            attachments=vk_photos,
            date=next(params.date_generator)
        )

        community.add_post(folder)

    # noinspection PyMethodMayBeStatic
    def __upload_to_album(self, community: Albums, folder: FolderTree, params: UploadParams) -> None:
        album = community.create_album(params.album_name)

        for file in folder.files:
            album.add_photo(file.path)

    # endregion uploading
