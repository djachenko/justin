import json
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import time, date, datetime, timedelta
from pathlib import Path
from typing import List, Iterator, Annotated

import typer
from PIL import Image

from justin_utils.exif import parse_exif
from justin_utils.filesystem import Folder, File
from justin_utils.pylinq import Sequence
from justin_utils.util import flat_map
from vk_api import ApiError, VkToolsException

from pyvko.aspects.albums import Albums, Album
from pyvko.aspects.comments import CommentModel
from pyvko.aspects.events import Event
from pyvko.aspects.posts import Post, PostModel, Posts
from pyvko.attachment.attachment import Attachment
from pyvko.pyvko_main import Pyvko
from typer import Typer, Argument

from justin.actions.mixins import EventUtils
from justin.actions.pattern_action import Extra
from justin.actions.rearrange_action import RearrangeAction
from justin.cms_2.storage.sqlite.sqlite_entries import Person
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafiles.metafile import PostMetafile, PostStatus, GroupMetafile, PersonMetafile, CommentMetafile, \
    AlbumMetafile, DriveMetafile
from justin.shared.models.photoset import Photoset
from justin.shared.proxy import Proxy
from justin.typer.base_commands.destinations_aware_command import DestinationsAwareCommand

Community = Posts | Albums


class UploadCommand(DestinationsAwareCommand, EventUtils):
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
            post_date = start_date + UploadCommand.__STEP * counter
            post_time = time(
                hour=random.randint(17, 23),
                minute=random.randint(0, 59),
            )

            post_datetime = datetime.combine(post_date, post_time)

            counter += 1

            yield post_datetime

    @staticmethod
    def __generator_for_group(group: Posts):
        try:
            scheduled_posts = group.get_scheduled_posts()
        except VkToolsException: # todo: wrap in pyvko
            scheduled_posts = []

        last_date = UploadCommand.__get_start_date(scheduled_posts)
        date_generator = UploadCommand.__date_generator(last_date)

        return date_generator

    @property
    def extra(self) -> Extra:
        return super().extra | {
            UploadCommand.__JUSTIN_DATE_GENERATOR:
                Proxy(lambda: UploadCommand.__generator_for_group(self.context.justin_group))
        }

    # endregion date generator

    def run_for_photoset(self, photoset: Photoset, extra: Extra) -> None:
        only_one_closed_name = Sequence \
            .with_single(photoset) \
            .flat_map(lambda ps: ps.parts) \
            .map(lambda pt: pt.closed) \
            .not_null() \
            .flat_map(lambda pt: pt.subfolders) \
            .is_distinct(lambda sf: sf.name)

        super().run_for_photoset(photoset, extra | {
            UploadCommand.__SET_CONTEXT: defaultdict(lambda: {}),
            UploadCommand.__SINGLE_NAME: only_one_closed_name,
        })

    def run_for_part(self, part: Photoset, extra: Extra) -> None:
        set_name = extra[UploadCommand.SET_NAME]

        if part.name != set_name:
            set_name = set_name + "/" + part.name

        print(f"Scheduling {set_name}... ")

        super().run_for_part(part, extra | {
            UploadCommand.__ROOT: part,
            UploadCommand.__ROOT_PATH: part.path,
            UploadCommand.__PART_NAME: part.name,
            UploadCommand.SET_NAME: set_name,
        })

    # region utils

    @staticmethod
    def __check_all_posted(*posts_folders: Folder) -> bool:
        for post_folder in posts_folders:
            if not PostMetafile.has(post_folder):
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

    def handle_drive(self, drive_folder: Folder, extra: Extra) -> None:
        set_name = extra[UploadCommand.SET_NAME]
        part_name = extra[UploadCommand.__PART_NAME]

        if set_name != part_name:
            folder_name = f"{set_name}_{part_name}"
        else:
            folder_name = set_name

        if len(drive_folder.subfolders) > 1:
            for subfolder in drive_folder.subfolders:
                sub_name = f"{folder_name}@{subfolder.name}"

                UploadCommand.__copy_folder(
                    subfolder,
                    self.context.drive_path,
                    sub_name
                )
        else:
            UploadCommand.__copy_folder(
                drive_folder.subfolders[0],
                self.context.drive_path,
                folder_name
            )

    def handle_justin(self, justin_folder: Folder, extra: Extra) -> None:
        justin_group = self.context.justin_group
        set_name = extra[UploadCommand.SET_NAME]
        part_name = extra[UploadCommand.__PART_NAME]

        date_generator = extra[UploadCommand.__JUSTIN_DATE_GENERATOR]

        if set_name != part_name:
            album_name = f"{set_name}_{part_name}"
        else:
            album_name = set_name

        GroupMetafile(
            group_id=justin_group.id
        ).save(justin_folder)

        for hashtag_folder in justin_folder.subfolders:
            hashtag_name = hashtag_folder.name

            if UploadCommand.__check_all_posted(*folder_tree_parts(hashtag_folder)):
                continue

            UploadCommand.__upload_bottom(
                community=justin_group,
                posts_folder=hashtag_folder,
                extra=extra,
                params=UploadCommand.UploadParams(
                    album_name=album_name,
                    text=f"#{hashtag_name}@{justin_group.url}",
                    date_generator=date_generator
                )
            )

    def handle_closed(self, closed_folder: Folder, extra: Extra) -> None:
        set_name: str = extra[UploadCommand.SET_NAME]
        only_one_name: bool = extra[UploadCommand.__SINGLE_NAME]

        event_date = UploadCommand.__get_date(set_name)

        for name_folder in closed_folder.subfolders:
            if UploadCommand.__check_all_posted(*folder_tree_parts(name_folder)):
                continue

            closed_name = name_folder.name

            print(f"Handling closed for {closed_name}...")

            if not only_one_name:
                event_name = f"{set_name}_{closed_name}"
            else:
                event_name = set_name

            UploadCommand.__upload_event(
                extra=extra,
                folder=name_folder,
                params=UploadCommand.EventParams(
                    destination=closed_folder.name,
                    category=closed_name,
                    event_name=event_name,
                    event_date=event_date,
                    pyvko=self.context.pyvko,
                )
            )

    def handle_meeting(self, meeting_folder: Folder, extra: Extra) -> None:
        if UploadCommand.__check_all_posted(*folder_tree_parts(meeting_folder)):
            return

        print("Handling meeting...")

        set_name: str = extra[UploadCommand.SET_NAME]

        event_date = UploadCommand.__get_date(set_name)

        UploadCommand.__upload_event(
            extra=extra,
            folder=meeting_folder,
            params=UploadCommand.EventParams(
                destination=meeting_folder.name,
                event_name=set_name,
                event_date=event_date,
                pyvko=self.context.pyvko,
            )
        )

    def handle_kot_i_kit(self, kot_i_kit_folder: Folder, extra: Extra) -> None:
        kot_i_kit_group = self.context.kot_i_kit_group

        skip_subtrees = [
            "logo",
            "market",
            "service",
        ]

        GroupMetafile(
            group_id=kot_i_kit_group.id
        ).save(kot_i_kit_folder)

        for hashtag_folder in kot_i_kit_folder.subfolders:
            hashtag_name = hashtag_folder.name

            if hashtag_name in skip_subtrees or hashtag_name.isdecimal():
                continue

            if UploadCommand.__check_all_posted(*folder_tree_parts(hashtag_folder)):
                continue

            UploadCommand.__upload_bottom(
                community=kot_i_kit_group,
                posts_folder=hashtag_folder,
                extra=extra,
                params=UploadCommand.UploadParams(
                    album_name="",
                    text=f"#{hashtag_name}@{kot_i_kit_group.url}",
                    date_generator=UploadCommand.__generator_for_group(kot_i_kit_group)
                )
            )

    def handle_my_people(self, my_people_folder: Folder, extra: Extra) -> None:
        my_people_group = self.context.my_people_group

        if not PostMetafile.has(my_people_folder):
            post = my_people_group.add_post(PostModel(text=extra[UploadCommand.SET_NAME]))

            GroupMetafile(group_id=my_people_group.id).save(my_people_folder)
            PostMetafile(
                post_id=post.id,
                status=PostStatus.PUBLISHED
            ).save(my_people_folder)

        post_metafile = PostMetafile.get(my_people_folder)
        post_id = post_metafile.post_id

        post = my_people_group.get_post(post_id)

        assert post is not None

        for person_folder in my_people_folder.subfolders:
            person = self.context.sqlite_cms.get_person(person_folder.name)

            if not person and person_folder.name.startswith("unknown"):
                person = Person(
                    folder=person_folder.name,
                    name=person_folder.name,
                    vk_id=None,
                )

            if not person:
                print(f"{person_folder.name} needs to be registered.")

                continue

            if not PersonMetafile.has(person_folder):
                PersonMetafile().save(person_folder)

            person_metafile = PersonMetafile.get(person_folder)

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

                if UploadCommand.check_photo_limits(image):
                    photo = my_people_group.upload_photo_to_wall(image.path)

                    link = photo.largest_link()
                    # short_link = self.context.pyvko.shorten_link(link)

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

            if person.vk_id:
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

            person_metafile.save(person_folder)

    def handle_timelapse(self, timelapse_folder: Folder, extra: Extra) -> None:
        pass

    def handle_cullen(self, cullen_folder: Folder, extra: Extra) -> None:
        cullen_group = self.context.cullen_group

        set_name = extra[UploadCommand.SET_NAME]
        part_name = extra[UploadCommand.__PART_NAME]

        if set_name != part_name:
            album_name = f"{set_name}_{part_name}"
        else:
            album_name = set_name

        album = UploadCommand.__get_album(
            cullen_group,
            cullen_folder,
            UploadCommand.UploadParams(
                album_name=album_name,
                date_generator=iter([]),
            )
        )

        photos = album.get_photos()

        album_metafile = AlbumMetafile.get(cullen_folder)

        assert len(photos) == len(album_metafile.images)

        links = [photo.largest_link() for photo in photos]

        links_mapping = list()

        for name, link in zip(album_metafile.images, links):
            links_mapping.append({
                "name": name.removesuffix(".jpg"),
                "url": link,
            })

        self.context.cullen_path.mkdir(parents=True, exist_ok=True)
        cullen_json_path = self.context.cullen_path / f"{set_name}.json"

        with cullen_json_path.open(mode="w") as cullen_json:
            json.dump(links_mapping, cullen_json, indent=4)

        current_jsons = [item for item in self.context.cullen_path.iterdir() if item.is_file() and item.suffix == ".json" and item.stem != "index"]
        current_jsons = [item.name for item in current_jsons]
        current_jsons.sort()

        with (self.context.cullen_path / "index.json").open(mode="w") as index_json:
            json.dump(current_jsons, index_json, indent=4)




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
    def __upload_event(extra: Extra, folder: Folder, params: EventParams) -> None:
        event = UploadCommand.__get_event(
            extra=extra,
            params=params,
            folder=folder
        )

        if event is None:
            print("Event was not acquired. Aborting.")

            return

        GroupMetafile(
            group_id=event.id
        ).save(folder)

        set_name: str = extra[UploadCommand.SET_NAME]
        date_generator = UploadCommand.__generator_for_group(event)

        UploadCommand.__upload_bottom(
            community=event,
            posts_folder=folder,
            extra=extra,
            params=UploadCommand.UploadParams(
                album_name=set_name,
                date_generator=date_generator
            )
        )

    @staticmethod
    def __get_event(folder: Folder, extra: Extra, params: EventParams) -> Event | None:
        set_context: Extra = extra[UploadCommand.__SET_CONTEXT]
        root: Photoset = extra[UploadCommand.__ROOT]

        pyvko = params.pyvko
        destination = params.destination

        if params.category is not None:
            set_context = set_context[destination]
            event_key = params.category
        else:
            event_key = destination

        if event_key not in set_context:
            event_url = UploadCommand.get_community_id(folder, root)

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
    def __upload_bottom(community: Community, posts_folder: Folder, extra: Extra, params: UploadParams) \
            -> None:
        root_path: Path = extra[UploadCommand.__ROOT_PATH]

        post_parts = folder_tree_parts(posts_folder)
        base_album_name = params.album_name

        for post_folder in post_parts:
            if UploadCommand.__check_all_posted(post_folder):
                continue

            post_path = post_folder.path.relative_to(root_path)

            if PostMetafile.has(post_folder):
                print(f"{post_path} is good, skipping.")

                continue

            print(f"Uploading {post_path}...")

            if len(post_parts) > 1:
                part_index = int(post_folder.name.split(".")[0])

                params.album_name = f"{base_album_name}.{part_index}"
            else:
                params.album_name = base_album_name

            post_id = UploadCommand.__upload_folder(community, post_folder, params)

            post_metafile = PostMetafile(
                post_id=post_id,
                status=PostStatus.SCHEDULED
            )

            post_metafile.save(post_folder)

    @staticmethod
    def __upload_folder(community: Community, folder: Folder, params: UploadParams) -> int:
        text = params.text or ""

        if folder.file_count() <= 10:
            attachments = UploadCommand.__get_post_attachments(community, folder)
        else:
            album = UploadCommand.__get_album(community, folder, params)

            attachments = []
            text = text.strip()
            text += f"\n\nА фотки лежат [{album.url}|вот здесь]."
            text = text.strip()

        post_model = PostModel(
            text=text,
            attachments=attachments,
            date=next(params.date_generator, None)
        )

        post = community.add_post(post_model)

        return post.id

    @staticmethod
    def __get_post_attachments(community: Posts, folder: Folder) -> List[Attachment]:
        vk_photos = []

        for file in folder.files:
            print(f"{file.name}... ", end="", flush=True)

            photo = community.upload_photo_to_wall(file.path)

            vk_photos.append(photo)

            print("done")

        return vk_photos

    @staticmethod
    def __get_album(community: Albums, folder: Folder, params: UploadParams) -> Album:
        if AlbumMetafile.has(folder):
            metafile = AlbumMetafile.get(folder)
            album = community.get_album_by_id(metafile.album_id)
        else:
            album = community.create_album(params.album_name)
            metafile = AlbumMetafile(album_id=album.id, images=[])

            metafile.save(folder)

        file_count = folder.file_count()

        not_uploaded_files = [file for file in folder.files if file.name not in metafile.images]
        not_uploaded_files.sort(key=lambda file: parse_exif(file.path))

        print(f"Uploading {file_count} photos...")

        batch_size = 10

        while not_uploaded_files:
            try:
                uploaded_photos = album.add_photos([file.path for file in not_uploaded_files[:batch_size]])
            except ApiError as e:
                if e.code != 100:
                    raise

                print("Error, retrying this particular batch")

                continue
            except json.JSONDecodeError:
                # pu.vk.com periodically returns HTTP 504 with an HTML body instead of JSON;
                # requests.Response.json() then raises JSONDecodeError instead of ApiError,
                # so it isn't caught by the except ApiError above. Treat it the same way: retry the batch.
                print("Error, retrying this particular batch")
                continue

            uploaded_count = len(uploaded_photos)

            uploaded_files = not_uploaded_files[:uploaded_count]
            not_uploaded_files = not_uploaded_files[uploaded_count:]

            uploaded_names = [file.name for file in uploaded_files]

            metafile.images += uploaded_names
            metafile.save(folder)

            print(f"Uploaded {uploaded_count} photos: " + ", ".join(uploaded_names) + f" ({len(metafile.images)} / {len(folder.files)})")

        print("done")

        return album

    @staticmethod
    def __copy_folder(folder: Folder, root: Path, name: str) -> None:
        drive_metafile = DriveMetafile.get(folder)

        # exists
        # renamed
        # new

        destination_path = root / name

        if not drive_metafile:
            destination_path.mkdir(exist_ok=True)

            for file in folder.files:
                file.copy(destination_path)

            drive_metafile = DriveMetafile(
                folder_name=name
            )
        elif drive_metafile.folder_name != name:
            current_path = root / drive_metafile.folder_name

            current_path.rename(destination_path)

            drive_metafile.folder_name = name

        drive_metafile.save(folder)

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


app = Typer()


@app.command()
def upload(
        context: Annotated[typer.Context, Argument()],
        pattern: Annotated[List[Path], Argument()] = (Path.cwd(),)
) -> None:
    UploadCommand(context.obj, pattern).run()
