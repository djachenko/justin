from argparse import Namespace

from justin_utils.pylinq import Sequence

from justin.actions.named.destinations_aware_action import DestinationsAwareAction
from justin.actions.pattern_action import Context, Extra
from justin.shared.filesystem import Folder
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import GroupMetafile, PostMetafile, PostStatus, PersonMetafile
from justin.shared.models.photoset import Photoset


class WebSyncAction(DestinationsAwareAction):
    def __init__(self) -> None:
        super().__init__()

        self.__cache = {}

        self.checked = []

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        print(f"Web syncing {part.name}...")

        super().perform_for_part(part, args, context, extra)

        print("Performed successfully")

    def handle_justin(self, justin_folder: Folder, context: Context, extra: Extra) -> None:
        self.__handle_tagged(justin_folder, context)

    def handle_closed(self, closed_folder: Folder, context: Context, extra: Extra) -> None:
        for name_folder in closed_folder.subfolders:
            if not name_folder.has_metafile():
                continue

            group_metafile: GroupMetafile = name_folder.get_metafile(GroupMetafile)
            group_id = group_metafile.group_id

            self.__warmup_cache(group_id, context)

            for post_folder in folder_tree_parts(name_folder):
                self.__handle_post(post_folder, group_id)

    def handle_meeting(self, meeting_folder: Folder, context: Context, extra: Extra) -> None:
        if not meeting_folder.has_metafile(GroupMetafile):
            return

        group_metafile: GroupMetafile = meeting_folder.get_metafile(GroupMetafile)
        group_id = group_metafile.group_id

        self.__warmup_cache(group_id, context)

        for post_folder in folder_tree_parts(meeting_folder):
            self.__handle_post(post_folder, group_id)

    def handle_kot_i_kit(self, kot_i_kit_folder: Folder, context: Context, extra: Extra) -> None:
        self.__handle_tagged(kot_i_kit_folder, context)

    def handle_my_people(self, my_people_folder: Folder, context: Context, extra: Extra) -> None:
        if not my_people_folder.has_metafile(PostMetafile):
            return

        post_metafile = my_people_folder.get_metafile(PostMetafile)

        post = context.my_people_group.get_post(post_metafile.post_id)

        comments = {comment.item_id: comment for comment in post.get_comments()}

        print("Syncing my people...")

        for person_folder in my_people_folder.subfolders:
            if not person_folder.has_metafile(PersonMetafile):
                continue

            print(f"Syncing {person_folder.name}...", end="", flush=True)

            person_metafile = person_folder.get_metafile(PersonMetafile)
            total_count = len(person_folder.files)

            for comment_metafile in person_metafile.comments:
                if comment_metafile.status == PostStatus.PUBLISHED:
                    continue

                if comment_metafile.id not in comments:
                    print(f"Comment #{comment_metafile.id} for {person_folder.name} was deleted.")

                    person_metafile.comments.remove(comment_metafile)

                else:
                    comment = comments[comment_metafile.id]

                    if comment.is_liked():
                        comment_metafile.status = PostStatus.PUBLISHED

                person_folder.save_metafile(person_metafile)

            person_folder.save_metafile(person_metafile)

            publish_count = sum(len(comment_metafile.files) for comment_metafile in person_metafile.comments if
                                comment_metafile.status == PostStatus.PUBLISHED)

            if publish_count == total_count:
                print(" all sent.")
            else:
                print(f" {publish_count}/{total_count} sent.")

    def handle_timelapse(self, timelapse_folder: Folder, context: Context, extra: Extra) -> None:
        pass

    def __warmup_cache(self, group_id: int, context: Context):
        if group_id in self.__cache:
            return

        group = context.pyvko.get(str(group_id))

        scheduled_posts = group.get_scheduled_posts()
        published_posts = group.get_posts()

        scheduled_ids = [post.id for post in scheduled_posts]
        published_timed_ids = [post.timer_id for post in published_posts]
        published_ids = [post.id for post in published_posts]

        timed_to_published_mapping = {post.timer_id: post.id for post in published_posts if post.timer_id}

        self.__cache[group_id] = (scheduled_ids, published_timed_ids, published_ids, timed_to_published_mapping)

    def __handle_tagged(self, folder: Folder, context: Context) -> None:
        if not folder.has_metafile():
            return

        group_metafile = folder.get_metafile(GroupMetafile)
        group_id = group_metafile.group_id

        if group_id > 0:
            group_metafile.group_id = -group_id

            folder.save_metafile(group_metafile)

        self.__warmup_cache(group_id, context)

        post_folders = Sequence \
            .with_single(folder) \
            .flat_map(lambda f: f.subfolders) \
            .flat_map(lambda htf: folder_tree_parts(htf))

        for post_folder in post_folders:
            self.__handle_post(post_folder, group_id)

    def __handle_post(self, post_folder: Folder, group_id: int) -> None:
        if not post_folder.has_metafile(PostMetafile):
            return

        scheduled_ids, published_timed_ids, published_ids, timed_to_published_mapping = self.__cache[group_id]

        post_metafile: PostMetafile = post_folder.get_metafile(PostMetafile)
        post_id = post_metafile.post_id

        print(f"Syncing post with id {post_id}... ", end="")

        if post_metafile.status is PostStatus.SCHEDULED:
            if post_id in scheduled_ids:
                print("still scheduled")
            elif post_id in published_timed_ids:
                post_metafile.status = PostStatus.PUBLISHED
                post_metafile.post_id = timed_to_published_mapping[post_id]

                print(f"was published, now has id {post_metafile.post_id}")

                post_folder.save_metafile(post_metafile)

            elif post_id in published_ids:
                # scheduled id can't become an id for published post

                print("somehow ended in posted array, aborting...")
            else:
                print("was deleted")

                post_folder.remove_metafile()

        elif post_metafile.status is PostStatus.PUBLISHED:
            # assert post_id not in scheduled_ids
            # assert post_id not in published_timed_ids

            if post_id in published_ids:
                print("still published")
            else:
                print("was deleted")

                post_folder.remove_metafile(PostMetafile)
        else:
            assert False

        self.checked.append(post_metafile.post_id)
