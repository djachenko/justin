import random
from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from datetime import time, date, datetime, timedelta
from pathlib import Path
from typing import List, Iterator

from PIL import Image

from justin.actions.destinations_aware_action import DestinationsAwareAction
from justin.actions.event import SetupEventAction
from justin.actions.mixins import EventUtils
from justin.actions.pattern_action import Context, Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.cms.people_cms import PersonEntry
from justin.shared.filesystem import File, Folder
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PostStatus, GroupMetafile, PersonMetafile, CommentMetafile, \
    AlbumMetafile, MetaFolder
from justin.shared.models.exif import parse_exif
from justin.shared.models.photoset import Photoset
from justin_utils.pylinq import Sequence
from justin_utils.util import stride, flat_map
from pyvko.aspects.albums import Albums
from pyvko.aspects.comments import CommentModel
from pyvko.aspects.events import Event
from pyvko.aspects.posts import Post, PostModel, Posts
from pyvko.attachment.attachment import Attachment
from pyvko.pyvko_main import Pyvko

Community = Posts | Albums


class UploadAction(DestinationsAwareAction, EventUtils):
    __STEP = timedelta(days=RearrangeAction.DEFAULT_STEP)
    __JUSTIN_DATE_GENERATOR = "date_generator"

    __SET_CONTEXT = "set_context"

    __ROOT = "root_itself"
    __ROOT_PATH = "root_path"
    __PART_NAME = "part_name"
    __SINGLE_NAME = "closed_names"

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
    def __generator_for_group(group: Posts):
        scheduled_posts = group.get_scheduled_posts()
        last_date = UploadAction.__get_start_date(scheduled_posts)
        date_generator = UploadAction.__date_generator(last_date)

        return date_generator

    def __init__(self, setup: SetupEventAction) -> None:
        super().__init__()

        self.__setup = setup

    # endregion date generator

    def get_extra(self, context: Context) -> Extra:
        return super().get_extra(context) | {
            UploadAction.__JUSTIN_DATE_GENERATOR: UploadAction.__generator_for_group(context.justin_group)
        }

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        only_one_closed_name = Sequence \
            .with_single(photoset) \
            .flat_map(lambda ps: ps.parts) \
            .map(lambda pt: pt.closed) \
            .not_null() \
            .flat_map(lambda pt: pt.subfolders) \
            .is_distinct(lambda sf: sf.name)

        super().perform_for_photoset(photoset, args, context, extra | {
            UploadAction.__SET_CONTEXT: defaultdict(lambda: {}),
            UploadAction.__SINGLE_NAME: only_one_closed_name,
        })

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        set_name = extra[UploadAction.SET_NAME]

        if part.name != set_name:
            set_name = set_name + "/" + part.name

        print(f"Scheduling {set_name}... ")

        super().perform_for_part(part, args, context, extra | {
            UploadAction.__ROOT: part,
            UploadAction.__ROOT_PATH: part.path,
            UploadAction.__PART_NAME: part.name,
            UploadAction.SET_NAME: set_name,
        })

    # region utils

    @staticmethod
    def __check_all_posted(*posts_folders: MetaFolder) -> bool:
        for post_folder in posts_folders:
            if not post_folder.has_metafile(PostMetafile):
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

    def handle_drive(self, drive_folder: Folder, context: Context, extra: Extra) -> None:
        pass

    def handle_justin(self, justin_folder: MetaFolder, context: Context, extra: Extra) -> None:
        justin_group = context.justin_group
        set_name = extra[UploadAction.SET_NAME]
        part_name = extra[UploadAction.__PART_NAME]

        date_generator = extra[UploadAction.__JUSTIN_DATE_GENERATOR]

        if set_name != part_name:
            album_name = f"{set_name}_{part_name}"
        else:
            album_name = set_name

        justin_folder.save_metafile(GroupMetafile(
            group_id=justin_group.id
        ))

        for hashtag_folder in justin_folder.subfolders:
            hashtag_name = hashtag_folder.name

            if UploadAction.__check_all_posted(*folder_tree_parts(hashtag_folder)):
                continue

            UploadAction.__upload_bottom(
                community=justin_group,
                posts_folder=hashtag_folder,
                extra=extra,
                params=UploadAction.UploadParams(
                    album_name=album_name,
                    text=f"#{hashtag_name}@{justin_group.url}",
                    date_generator=date_generator
                )
            )

    def handle_closed(self, closed_folder: MetaFolder, context: Context, extra: Extra) -> None:
        set_name: str = extra[UploadAction.SET_NAME]
        only_one_name: bool = extra[UploadAction.__SINGLE_NAME]

        event_date = UploadAction.__get_date(set_name)

        for name_folder in closed_folder.subfolders:
            if UploadAction.__check_all_posted(*folder_tree_parts(name_folder)):
                continue

            closed_name = name_folder.name

            print(f"Handling closed for {closed_name}...")

            if not only_one_name:
                event_name = f"{set_name}_{closed_name}"
            else:
                event_name = set_name

            UploadAction.__upload_event(
                extra=extra,
                folder=name_folder,
                params=UploadAction.EventParams(
                    destination=closed_folder.name,
                    category=closed_name,
                    event_name=event_name,
                    event_date=event_date,
                    pyvko=context.pyvko,
                )
            )

    def handle_meeting(self, meeting_folder: MetaFolder, context: Context, extra: Extra) -> None:
        if UploadAction.__check_all_posted(*folder_tree_parts(meeting_folder)):
            return

        print("Handling meeting...")

        set_name: str = extra[UploadAction.SET_NAME]

        event_date = UploadAction.__get_date(set_name)

        UploadAction.__upload_event(
            extra=extra,
            folder=meeting_folder,
            params=UploadAction.EventParams(
                destination=meeting_folder.name,
                event_name=set_name,
                event_date=event_date,
                pyvko=context.pyvko,
            )
        )

    def handle_kot_i_kit(self, kot_i_kit_folder: MetaFolder, context: Context, extra: Extra) -> None:
        kot_i_kit_group = context.kot_i_kit_group

        skip_subtrees = [
            "logo",
            "market",
            "service",
        ]

        kot_i_kit_folder.save_metafile(GroupMetafile(
            group_id=kot_i_kit_group.id
        ))

        for hashtag_folder in kot_i_kit_folder.subfolders:
            hashtag_name = hashtag_folder.name

            if hashtag_name in skip_subtrees or hashtag_name.isdecimal():
                continue

            if UploadAction.__check_all_posted(*folder_tree_parts(hashtag_folder)):
                continue

            UploadAction.__upload_bottom(
                community=kot_i_kit_group,
                posts_folder=hashtag_folder,
                extra=extra,
                params=UploadAction.UploadParams(
                    album_name="",
                    text=f"#{hashtag_name}@{kot_i_kit_group.url}",
                    date_generator=UploadAction.__generator_for_group(kot_i_kit_group)
                )
            )

    def handle_my_people(self, my_people_folder: MetaFolder, context: Context, extra: Extra) -> None:
        my_people_group = context.my_people_group

        if not my_people_folder.has_metafile(PostMetafile):
            post = my_people_group.add_post(PostModel(text=extra[UploadAction.SET_NAME]))

            my_people_folder.save_metafile(GroupMetafile(group_id=my_people_group.id))
            my_people_folder.save_metafile(PostMetafile(post_id=post.id, status=PostStatus.PUBLISHED))

        post_metafile = my_people_folder.get_metafile(PostMetafile)
        post_id = post_metafile.post_id

        post = my_people_group.get_post(post_id)

        assert post is not None

        for person_folder in my_people_folder.subfolders:
            person = context.cms.people.get(person_folder.name)

            if not person and person_folder.name.startswith("unknown"):
                person = PersonEntry(
                    folder=person_folder.name,
                    name=person_folder.name,
                    vk_id=1,
                    source=""
                )

            if not person:
                print(f"{person_folder.name} needs to be registered.")

                continue

            if not PersonEntry.is_valid(person):
                print(f"{person_folder.name} needs to be fixed.")

                continue

            if not person_folder.has_metafile(PersonMetafile):
                person_folder.save_metafile(PersonMetafile())

            person_metafile = person_folder.get_metafile(PersonMetafile)

            uploaded_images = flat_map(c.files for c in person_metafile.comments)
            images_to_upload: List[File] = []

            for image in person_folder.files:
                if image.name in uploaded_images:
                    continue

                images_to_upload.append(image)

            if not images_to_upload:
                continue

            print(f"Uploading {person_folder.name}")

            links = []

            photo = None

            for image in images_to_upload:
                print(f"Uploading {image.name}...", end="", flush=True)

                if UploadAction.check_photo_limits(image):
                    photo = my_people_group.upload_photo_to_wall(image.path)

                    link = photo.largest_link()
                    # short_link = context.pyvko.shorten_link(link)

                    links.append(link)

                    print(" done.", flush=True)
                else:
                    links.append(f"{image.name} is too big and should be file.")

                    print(" too big, skipping.", flush=True)

            name_components = []

            if person.name:
                name_components.append(person.name)
            else:
                name_components.append(person.folder)

            if person.vk_id and person.vk_id != 1:
                name_components.append(f"https://vk.com/write{person.vk_id}")

            name_components.append(f"{len(links)} total.")

            text = "\n\n".join([
                ", ".join(name_components),
                "\n".join(links),
            ]).strip()

            if photo:
                attachments = [photo]
            else:
                attachments = None

            comment = post.add_comment(CommentModel(
                text=text,
                from_group=abs(my_people_group.id),
                attachments=attachments
            ))

            comment_metafile = CommentMetafile(
                id=comment.item_id,
                files=[image.name for image in images_to_upload],
                status=PostStatus.SCHEDULED,
            )

            person_metafile.comments.append(comment_metafile)

            person_folder.save_metafile(person_metafile)

    def handle_timelapse(self, timelapse_folder: MetaFolder, context: Context, extra: Extra) -> None:
        pass

    # endregion upload strategies

    # region event

    @dataclass
    class EventParams:
        destination: str
        event_name: str
        event_date: date
        pyvko: Pyvko
        category: str | None = None

    @staticmethod
    def __upload_event(extra: Extra, folder: MetaFolder, params: EventParams) -> None:
        event = UploadAction.__get_event(
            extra=extra,
            params=params,
            folder=folder
        )

        if event is None:
            print("Event was not acquired. Aborting.")

            return

        folder.save_metafile(GroupMetafile(
            group_id=event.id
        ))

        set_name: str = extra[UploadAction.SET_NAME]
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
    def __get_event(folder: MetaFolder, extra: Extra, params: EventParams) -> Event | None:
        set_context: Extra = extra[UploadAction.__SET_CONTEXT]
        root: Photoset = extra[UploadAction.__ROOT]

        pyvko = params.pyvko
        destination = params.destination

        if params.category is not None:
            set_context = set_context[destination]
            event_key = params.category
        else:
            event_key = destination

        if event_key not in set_context:
            event_url = UploadAction.get_community_id(folder, root)

            if event_url is not None:
                event = pyvko.get(event_url)
            else:
                event = None

            if event is None:
                return None

            set_context[event_key] = event

        return set_context[event_key]

    # endregion event

    # region uploading

    @dataclass
    class UploadParams:
        album_name: str
        date_generator: Iterator[datetime]
        text: str | None = None

    @staticmethod
    def __upload_bottom(community: Community, posts_folder: MetaFolder, extra: Extra, params: UploadParams) \
            -> None:
        root_path: Path = extra[UploadAction.__ROOT_PATH]

        post_parts = folder_tree_parts(posts_folder)
        base_album_name = params.album_name

        for post_folder in post_parts:
            if UploadAction.__check_all_posted(post_folder):
                continue

            post_path = post_folder.path.relative_to(root_path)

            if post_folder.has_metafile(PostMetafile):
                print(f"{post_path} is good, skipping.")

                continue

            print(f"Uploading {post_path}...")

            if len(post_parts) > 1:
                part_index = int(post_folder.name.split(".")[0])

                params.album_name = f"{base_album_name}.{part_index}"
            else:
                params.album_name = base_album_name

            post_id = UploadAction.__upload_folder(community, post_folder, params)

            post_metafile = PostMetafile(
                post_id=post_id,
                status=PostStatus.SCHEDULED
            )

            post_folder.save_metafile(post_metafile)

    @staticmethod
    def __upload_folder(community: Community, folder: MetaFolder, params: UploadParams) -> int:
        if folder.file_count() <= 10:
            attachments = UploadAction.__get_post_attachments(community, folder)
        else:
            attachments = UploadAction.__get_album_attachments(community, folder, params)

        post_model = PostModel(
            text=params.text,
            attachments=attachments,
            date=next(params.date_generator)
        )

        post = community.add_post(post_model)

        return post.id

    @staticmethod
    def __get_post_attachments(community: Posts, folder: MetaFolder) -> [Attachment]:
        vk_photos = []

        for file in folder.files:
            print(f"{file.name}... ", end="", flush=True)

            photo = community.upload_photo_to_wall(file.path)

            vk_photos.append(photo)

            print("done")

        return vk_photos

    @staticmethod
    def __get_album_attachments(community: Albums, folder: MetaFolder, params: UploadParams) -> [Attachment]:

        if folder.has_metafile(AlbumMetafile):
            metafile = folder.get_metafile(AlbumMetafile)
            album = community.get_album_by_id(metafile.album_id)
        else:
            album = community.create_album(params.album_name)
            metafile = AlbumMetafile(album_id=album.id, images=[])

            folder.save_metafile(metafile)

        file_count = folder.file_count()

        for i, file in enumerate(sorted(folder.files, key=parse_exif), start=1):
            if file.name in metafile.images:
                continue

            success = False

            print(f"Uploading {file.name} ({i}/{file_count})...", end="")

            counter = 1

            while not success:
                # noinspection PyBroadException
                try:
                    album.add_photo(file.path)

                    success = True
                except KeyboardInterrupt:
                    raise
                except:
                    print(f"Retrying {counter}")

                    counter += 1

            metafile.images.append(file.name)

            folder.save_metafile(metafile)

            print(" done.")

        return [album]

    # endregion uploading

    @staticmethod
    def check_photo_limits(file: File) -> bool:
        if file.size > 50 * 1024 * 1024:
            return False

        with Image.open(file.path) as image:
            width = image.width
            height = image.height

        if width == 0 or height == 0:
            return False

        if width + height > 14000:
            return False

        if width / height > 20:
            return False

        if height / width > 20:
            return False

        return True
