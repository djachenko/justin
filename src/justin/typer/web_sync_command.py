from pathlib import Path
from typing import Annotated, List, Iterable

import typer

from justin_utils.filesystem import Folder
from justin_utils.pylinq import Sequence
from typer import Typer, Argument

from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafiles.metafile import GroupMetafile, PostMetafile, PostStatus, PersonMetafile, AlbumMetafile, \
    RootMetafile
from justin.shared.models.photoset import Photoset
from justin.typer.base_commands.destinations_aware_command import DestinationsAwareCommand


class WebSyncCommand(DestinationsAwareCommand):
    def __init__(self, context: Context, patterns: Iterable[Path]):
        super().__init__(context, patterns)

        self.__cache = {}

    def run_for_part(self, part: Photoset, extra: Extra) -> None:
        print(f"Web syncing {extra[WebSyncCommand.PART_FULL_NAME]}...")

        super().run_for_part(part, extra)

        print("Performed successfully")

    def handle_justin(self, justin_folder: Folder, extra: Extra) -> None:
        self.__handle_tagged(justin_folder)

    def handle_closed(self, closed_folder: Folder, extra: Extra) -> None:
        for name_folder in closed_folder.subfolders:
            if not GroupMetafile.has(name_folder):
                continue

            group_metafile = GroupMetafile.get(name_folder)
            group_id = group_metafile.group_id

            self.__warmup_cache(group_id)

            for post_folder in folder_tree_parts(name_folder):
                self.__handle_post(post_folder, group_id)

    def handle_meeting(self, meeting_folder: Folder, extra: Extra) -> None:
        if not GroupMetafile.has(meeting_folder):
            return

        group_metafile = GroupMetafile.get(meeting_folder)
        group_id = group_metafile.group_id

        self.__warmup_cache(group_id)

        for post_folder in folder_tree_parts(meeting_folder):
            self.__handle_post(post_folder, group_id)

    def handle_kot_i_kit(self, kot_i_kit_folder: Folder, extra: Extra) -> None:
        self.__handle_tagged(kot_i_kit_folder)

    def handle_my_people(self, my_people_folder: Folder, extra: Extra) -> None:
        self.__warmup_cache(self.context.my_people_group.id)

        if not PostMetafile.has(my_people_folder):
            return

        post_metafile = PostMetafile.get(my_people_folder)

        _, _, published_ids, _ = self.__cache[self.context.my_people_group.id]

        if post_metafile.post_id not in published_ids:
            for subfolder in my_people_folder.subfolders:
                RootMetafile.remove(subfolder)

            RootMetafile.remove(my_people_folder)

            print("Post was deleted")

            return

        post = self.context.my_people_group.get_post(post_metafile.post_id)

        if post.is_liked():
            for person_folder in my_people_folder.subfolders:
                if not PersonMetafile.has(person_folder):
                    continue

                person_metafile = PersonMetafile.get(person_folder)

                for comment_metafile in person_metafile.comments:
                    comment_metafile.status = PostStatus.PUBLISHED

                person_metafile.save(person_folder)

            print("All people sent.")

            return

        comments = {comment.item_id: comment for comment in post.get_comments()}

        print("Syncing my people...")

        all_sent = True

        for person_folder in my_people_folder.subfolders:
            if not PersonMetafile.has(person_folder):
                continue

            print(f"Syncing {person_folder.name}...", end="", flush=True)

            person_metafile = PersonMetafile.get(person_folder)
            total_count = len(person_folder.files)

            for comment_metafile in person_metafile.comments:
                if comment_metafile.status == PostStatus.PUBLISHED:
                    continue

                if comment_metafile.id not in comments:
                    print(f"Comment #{comment_metafile.id} for {person_folder.name} was deleted.")

                    person_metafile.comments.remove(comment_metafile)

                else:
                    comment = comments[comment_metafile.id]

                    if comment.has_likes():
                        comment_metafile.status = PostStatus.PUBLISHED

                person_metafile.save(person_folder)

            person_metafile.save(person_folder)

            publish_count = sum(len(comment_metafile.files) for comment_metafile in person_metafile.comments if
                                comment_metafile.status == PostStatus.PUBLISHED)

            if publish_count >= total_count:
                print(" all sent.")
            else:
                print(f" {publish_count}/{total_count} sent.")

                all_sent = False

        if all_sent:
            post.like()

    def handle_timelapse(self, timelapse_folder: Folder, extra: Extra) -> None:
        pass

    def handle_drive(self, drive_folder: Folder, extra: Extra) -> None:
        pass

    def __warmup_cache(self, group_id: int):
        if group_id in self.__cache:
            return

        group = self.context.pyvko.get(str(group_id))

        scheduled_posts = group.get_scheduled_posts()
        published_posts = group.get_posts()

        scheduled_ids = [post.id for post in scheduled_posts]
        published_timer_ids = [post.timer_id for post in published_posts]
        published_ids = [post.id for post in published_posts]

        timed_to_published_mapping = {post.timer_id: post.id for post in published_posts if post.timer_id}

        self.__cache[group_id] = (scheduled_ids, published_timer_ids, published_ids, timed_to_published_mapping)

    def __handle_tagged(self, folder: Folder) -> None:
        if not GroupMetafile.has(folder):
            return

        group_metafile = GroupMetafile.get(folder)
        group_id = group_metafile.group_id

        if group_id > 0:
            group_metafile.group_id = -group_id

            group_metafile.save(folder)

        self.__warmup_cache(group_id)

        post_folders = Sequence \
            .with_single(folder) \
            .flat_map(lambda f: f.subfolders) \
            .flat_map(lambda htf: folder_tree_parts(htf))

        for post_folder in post_folders:
            self.__handle_post(post_folder, group_id)

    def __handle_post(self, post_folder: Folder, group_id: int) -> None:
        if not PostMetafile.has(post_folder):
            return

        scheduled_ids, published_timed_ids, published_ids, timed_to_published_mapping = self.__cache[group_id]

        post_metafile = PostMetafile.get(post_folder)
        post_id = post_metafile.post_id

        print(f"Syncing post with id {post_id}... ", end="")

        if post_metafile.status is PostStatus.SCHEDULED:
            if post_id in scheduled_ids:
                print("still scheduled")
            elif post_id in published_timed_ids:
                post_metafile.status = PostStatus.PUBLISHED
                post_metafile.post_id = timed_to_published_mapping[post_id]

                print(f"was published, now has id {post_metafile.post_id}")

                post_metafile.save(post_folder)
                AlbumMetafile.remove(post_folder)

            elif post_id in published_ids:
                # scheduled id can't become an id for published post

                print("somehow ended in posted array, aborting...")
            else:
                print("was deleted")

                PostMetafile.remove(post_folder)
                AlbumMetafile.remove(post_folder)

        elif post_metafile.status is PostStatus.PUBLISHED:
            # assert post_id not in scheduled_ids
            # assert post_id not in published_timed_ids

            if post_id in published_ids:
                print("still published")
            else:
                print("was deleted")

                PostMetafile.remove(post_folder)
        else:
            assert False


app = Typer()


@app.command()
def web_sync(
        context: Annotated[typer.Context, Argument()],
        pattern: Annotated[List[Path], Argument()] = (Path.cwd(),)
) -> None:
    WebSyncCommand(context.obj, pattern).run()
