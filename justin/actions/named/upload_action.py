import random
from argparse import Namespace
from dataclasses import dataclass
from datetime import time, date, datetime, timedelta
from typing import List, Union, Optional, Iterator, Tuple

from py_linq import Enumerable
from pyvko.attachment.attachment import Attachment
from pyvko.models.active_models import Event
from pyvko.models.models import Post
from pyvko.shared.mixins import Wall, Albums, Events

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PostStatus
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
            part.closed,
            part.meeting,
        ]

        part_metafile = part.get_metafile()

        posted_paths = Enumerable(part_metafile.posts.values()) \
            .select_many() \
            .select(lambda p: p.path) \
            .to_list()

        posted_paths = set(posted_paths)

        extra["posted_paths"] = posted_paths
        extra["root_path"] = part.path
        extra["part_name"] = part.name

        destination_handlers = {
            "justin": UploadAction.__upload_justin,
            "closed": UploadAction.__upload_closed,
            "meeting": UploadAction.__upload_meeting,
        }

        for destination in destinations:
            if destination is None:
                continue

            assert destination.name in destination_handlers

            community_id, metafiles = destination_handlers[destination.name](destination, context, extra)

            part_metafile.posts[community_id] += metafiles

    # region upload strategies

    @staticmethod
    def __upload_justin(folder: FolderTree, context: Context, extra: Extra) -> Tuple[int, List[PostMetafile]]:
        community = context.justin_group
        set_name = extra["set_name"]
        part_name = extra["part_name"]
        date_generator = extra[UploadAction.__JUSTIN_DATE_GENERATOR]

        if set_name != part_name:
            album_name = ".".join([set_name, part_name])
        else:
            album_name = part_name

        justin_metafiles = []

        for hashtag_folder in folder.subtrees:
            params = UploadAction.UploadParams(
                album_name=album_name,
                text=f"#{hashtag_folder.name}@{community.url}",
                date_generator=date_generator
            )

            hashtag_metafiles = UploadAction.upload_bottom(community, hashtag_folder, params, extra)

            justin_metafiles += hashtag_metafiles

        return community.id, justin_metafiles

    @staticmethod
    def __upload_closed(folder: FolderTree, context: Context, extra: Extra) -> Tuple[int, List[PostMetafile]]:
        set_context = extra["set_context"]
        set_name = extra["set_name"]
        names_count = extra["closed_names"]

        closed_metafiles = []

        for name in folder.subtrees:
            if names_count[name.name] > 1:
                event_name = set_name
            else:
                event_name = f"{set_name}_{name.name}"

            event = UploadAction.__get_event(
                community=context.closed_group,
                context=set_context,
                params=UploadAction.EventParams(
                    destination=folder.name,
                    category=name.name,
                    event_name=event_name
                ))

            date_generator = UploadAction.__generator_for_group(event)

            params = UploadAction.UploadParams(
                album_name=set_name,
                date_generator=date_generator
            )

            name_metafiles = UploadAction.upload_bottom(event, name, params, extra)

            closed_metafiles += name_metafiles

        return context.closed_group.id, closed_metafiles

    @staticmethod
    def __upload_meeting(folder: FolderTree, context: Context, extra: Extra) -> Tuple[int, List[PostMetafile]]:
        set_context = extra["set_context"]
        set_name = extra["set_name"]

        event = UploadAction.__get_event(
            community=context.meeting_group,
            context=set_context,
            params=UploadAction.EventParams(
                destination=folder.name,
                event_name=set_name
            ))

        date_generator = UploadAction.__generator_for_group(event)

        params = UploadAction.UploadParams(
            album_name=set_name,
            date_generator=date_generator
        )

        new_post_metafiles = UploadAction.upload_bottom(event, folder, params, extra)

        return context.meeting_group.id, new_post_metafiles

    # endregion upload strategies

    # region event

    @dataclass
    class EventParams:
        destination: str
        event_name: str
        category: Optional[str] = None

    @staticmethod
    def __get_event(community: Events, context: Extra, params: EventParams) -> Event:
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
                event = UploadAction.__create_event(community, params.event_name)

            context[key] = event

        return context[key]

    @staticmethod
    def __create_event(community: Events, name: str) -> Event:
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

    @staticmethod
    def upload_bottom(community: Union[Wall, Albums], folder: FolderTree, params: UploadParams, extra: Extra) \
            -> List[PostMetafile]:
        posted_paths = extra["posted_paths"]
        root_path = extra["root_path"]

        uploaded_metafiles = []

        for post_folder in folder_tree_parts(folder):
            post_path = post_folder.path.relative_to(root_path)

            if post_path in posted_paths:
                continue

            post_id = UploadAction.__upload_folder(community, post_folder, params)

            uploaded_metafiles.append(PostMetafile(
                path=post_path,
                post_id=post_id,
                status=PostStatus.SCHEDULED
            ))

        return uploaded_metafiles

    @staticmethod
    def __upload_folder(community: Union[Wall, Albums], folder: FolderTree, params: UploadParams) -> int:
        if folder.file_count() <= 10:
            attachments = UploadAction.__upload_to_post(community, folder)
        else:
            attachments = UploadAction.__upload_to_album(community, folder, params)

        post = Post(
            text=params.text,
            attachments=attachments,
            date=next(params.date_generator)
        )

        post_id = community.add_post(post)

        return post_id

    @staticmethod
    def __upload_to_post(community: Wall, folder: FolderTree) -> [Attachment]:
        vk_photos = [community.upload_photo_to_wall(file.path) for file in folder.files]

        return vk_photos

    @staticmethod
    def __upload_to_album(community: Albums, folder: FolderTree, params: UploadParams) -> [Attachment]:
        album = community.create_album(params.album_name)

        for file in folder.files:
            album.add_photo(file.path)

        return [album]

    # endregion uploading
