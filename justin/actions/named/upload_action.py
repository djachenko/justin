import random
from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from datetime import time, date, datetime, timedelta
from pathlib import Path
from typing import List, Union, Optional, Iterator

from py_linq import Enumerable
from pyvko.attachment.attachment import Attachment
from pyvko.models.active_models import Event
from pyvko.models.models import Post
from pyvko.shared.mixins import Wall, Albums, Events

from justin.actions.named.mixins import EventUtils
from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PostStatus
from justin.shared.models.photoset import Photoset
from justin_utils.util import ask_for_permission


class UploadAction(NamedAction, EventUtils):
    __STEP = timedelta(days=RearrangeAction.DEFAULT_STEP)
    __JUSTIN_DATE_GENERATOR = "date_generator"

    __SET_NAME = "set_name"
    __SET_CONTEXT = "set_context"

    __ROOT = "root_itself"
    __ROOT_PATH = "root_path"
    __POSTED_PATHS = "posted_paths"
    __PART_NAME = "part_name"
    __CLOSED_NAMES = "closed_names"

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
        names = Enumerable([photoset]) \
            .select(lambda p: p.closed) \
            .where(lambda e: e is not None) \
            .select_many(lambda p: p.subtrees) \
            .select(lambda p: p.name) \
            .to_list()

        names_count = defaultdict(lambda: 0)

        for name in names:
            names_count[name] += 1

        extra.update({
            UploadAction.__SET_NAME: photoset.name,
            UploadAction.__SET_CONTEXT: {},
            UploadAction.__CLOSED_NAMES: names_count,
        })

        super().perform_for_photoset(photoset, args, context, extra)

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:

        print(f"Scheduling {extra[UploadAction.__SET_NAME]}... ")

        destinations = [
            (part.justin, UploadAction.__upload_justin),
            (part.closed, UploadAction.__upload_closed),
            (part.meeting, UploadAction.__upload_meeting),
        ]

        part_metafile = part.get_metafile()

        posted_paths = Enumerable(part_metafile.posts.values()) \
            .select_many() \
            .select(lambda p: p.path) \
            .to_list()

        posted_paths = set(posted_paths)

        extra[UploadAction.__POSTED_PATHS] = posted_paths
        extra[UploadAction.__ROOT] = part
        extra[UploadAction.__ROOT_PATH] = part.path
        extra[UploadAction.__PART_NAME] = part.name

        for destination, handler in destinations:
            if destination is None:
                continue

            handler(destination, context, extra)

    # region utils

    @staticmethod
    def __check_all_posted(extra: Extra, *posts_folders: FolderTree) -> bool:
        root_path = extra[UploadAction.__ROOT_PATH]
        posted_paths = extra[UploadAction.__POSTED_PATHS]

        for post_folder in posts_folders:
            if post_folder.path.relative_to(root_path) not in posted_paths:
                return False

        return True

    @staticmethod
    def __get_date(set_name: str) -> date:
        name_parts = set_name.split(".")

        if len(name_parts) >= 3 and all([name_part.isdecimal() for name_part in name_parts[:3]]):
            year, month, day = [int(name_part) for name_part in name_parts[:3]]

            year += 2000

            event_date = date(year, month, day)
        else:
            event_date = date.today() + timedelta(days=1)

        return event_date

    # endregion utils

    # region upload strategies

    @staticmethod
    def __upload_justin(folder: FolderTree, context: Context, extra: Extra) -> None:
        justin_group = context.justin_group
        set_name = extra[UploadAction.__SET_NAME]
        part_name = extra[UploadAction.__PART_NAME]

        date_generator = extra[UploadAction.__JUSTIN_DATE_GENERATOR]

        if set_name != part_name:
            album_name = f"{set_name}.{part_name}"
        else:
            album_name = part_name

        for hashtag_folder in folder.subtrees:
            UploadAction.__upload_bottom(
                community=justin_group,
                posts_folder=hashtag_folder,
                extra=extra,
                params=UploadAction.UploadParams(
                    album_name=album_name,
                    text=f"#{hashtag_folder.name}@{justin_group.url}",
                    date_generator=date_generator
                )
            )

    @staticmethod
    def __upload_closed(closed_folder: FolderTree, context: Context, extra: Extra) -> None:
        set_name = extra[UploadAction.__SET_NAME]
        names_count = extra[UploadAction.__CLOSED_NAMES]

        event_date = UploadAction.__get_date(set_name)

        for name_folder in closed_folder.subtrees:
            if UploadAction.__check_all_posted(extra, *folder_tree_parts(name_folder)):
                continue

            closed_name = name_folder.name

            print(f"Handling closed for {closed_name}...")

            if names_count[closed_name] > 1:
                event_name = set_name
            else:
                event_name = f"{set_name}_{closed_name}"

            UploadAction.__upload_event(
                context=context,
                extra=extra,
                folder=name_folder,
                params=UploadAction.EventParams(
                    destination=closed_folder.name,
                    category=closed_name,
                    event_name=event_name,
                    event_date=event_date
                )
            )

    @staticmethod
    def __upload_meeting(meeting_folder: FolderTree, context: Context, extra: Extra) -> None:
        if UploadAction.__check_all_posted(extra, *folder_tree_parts(meeting_folder)):
            return

        print("Handling meeting...")

        set_name: str = extra[UploadAction.__SET_NAME]

        event_date = UploadAction.__get_date(set_name)

        UploadAction.__upload_event(
            context=context,
            extra=extra,
            folder=meeting_folder,
            params=UploadAction.EventParams(
                destination=meeting_folder.name,
                event_name=set_name,
                event_date=event_date
            )
        )

    # endregion upload strategies

    # region event

    @dataclass
    class EventParams:
        destination: str
        event_name: str
        event_date: date
        category: Optional[str] = None

    @staticmethod
    def __upload_event(context: Context, extra: Extra, folder: FolderTree, params: EventParams) -> None:
        event = UploadAction.__get_event(
            owner=context.meeting_group,
            extra=extra,
            params=params,
            folder=folder
        )

        set_name: str = extra[UploadAction.__SET_NAME]
        date_generator = UploadAction.__generator_for_group(event)

        UploadAction.__upload_bottom(
            community=event,
            posts_folder=folder,
            extra=extra,
            params=UploadAction.UploadParams(
                album_name=set_name,
                date_generator=date_generator
            )
        )

    @staticmethod
    def __get_event(owner: Events, folder: FolderTree, extra: Extra, params: EventParams) -> Event:
        set_context: Extra = extra[UploadAction.__SET_CONTEXT]
        root: Photoset = extra[UploadAction.__ROOT]

        destination = params.destination

        if params.category is not None:
            set_context[destination] = set_context.get(destination, {})

            set_context = set_context[destination]
            event_key = params.category
        else:
            event_key = destination

        if event_key not in set_context:
            event_url = UploadAction.get_community_id(folder, root)

            if event_url != "":
                event = owner.get_event(event_url)
            else:
                event = None

            if event is None and ask_for_permission(f"No event with url \"{event_url}\". Create?"):
                event = UploadAction.__create_event(owner, params)

            if event is not None:
                set_context[event_key] = event

        return set_context[event_key]

    @staticmethod
    def __create_event(community: Events, params: EventParams) -> Event:
        event: Event = community.create_event(params.event_name)

        event.event_category = Event.Category.CIRCUS

        event.start_date = datetime.combine(params.event_date, time(hour=12))
        event.end_date = event.start_date + timedelta(hours=4)

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
    def __upload_bottom(community: Union[Wall, Albums], posts_folder: FolderTree, extra: Extra, params: UploadParams) \
            -> None:
        posted_paths: List[Path] = extra[UploadAction.__POSTED_PATHS]
        root_path: Path = extra[UploadAction.__ROOT_PATH]
        root: Photoset = extra[UploadAction.__ROOT]

        photoset_metafile = root.get_metafile()

        post_parts = folder_tree_parts(posts_folder)
        base_album_name = params.album_name

        for post_folder in post_parts:
            if UploadAction.__check_all_posted(extra, post_folder):
                continue

            post_path = post_folder.path.relative_to(root_path)

            if post_path in posted_paths:
                continue

            print(f"Uploading {post_path}...")

            if len(post_parts) > 1:
                part_index = int(post_folder.name.split(".")[0])

                params.album_name = f"{base_album_name}_{part_index}"
            else:
                params.album_name = base_album_name

            post_id = UploadAction.__upload_folder(community, post_folder, params)

            photoset_metafile.posts[community.id].append(PostMetafile(
                path=post_path,
                post_id=post_id,
                status=PostStatus.SCHEDULED
            ))

            root.save_metafile(photoset_metafile)

    @staticmethod
    def __upload_folder(community: Union[Wall, Albums], folder: FolderTree, params: UploadParams) -> int:
        if folder.file_count() <= 10:
            attachments = UploadAction.__get_post_attachments(community, folder)
        else:
            attachments = UploadAction.__get_album_attachments(community, folder, params)

        post = Post(
            text=params.text,
            attachments=attachments,
            date=next(params.date_generator)
        )

        post_id = community.add_post(post)

        return post_id

    @staticmethod
    def __get_post_attachments(community: Wall, folder: FolderTree) -> [Attachment]:
        vk_photos = [community.upload_photo_to_wall(file.path) for file in folder.files]

        return vk_photos

    @staticmethod
    def __get_album_attachments(community: Albums, folder: FolderTree, params: UploadParams) -> [Attachment]:
        album = community.create_album(params.album_name)

        for file in folder.files:
            album.add_photo(file.path)

        return [album]

    # endregion uploading
