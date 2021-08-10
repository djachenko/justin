from argparse import Namespace

from pyvko.shared.mixins import Wall

from justin.actions.named.mixins import EventUtils
from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.shared import filesystem
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PostStatus
from justin.shared.models.photoset import Photoset


class FixMetafileAction(NamedAction, EventUtils):

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        mapping = [
            (part.justin, context.justin_group),
            (part.closed, context.closed_group),
            (part.meeting, context.meeting_group),
        ]

        print(f"Fixing metafile for {part.name} photoset.")

        for destination, group in mapping:
            if destination is None:
                continue

            if destination.name == "meeting":
                categories = [destination]
            else:
                categories = destination.subtrees

            for category in categories:
                community = None

                if destination.name == "justin":
                    community = group
                else:
                    while community is None:
                        community = group.get_event(FixMetafileAction.get_community_id(destination, part))

                FixMetafileAction.__handle_direct(category, part, community)

    @staticmethod
    def __handle_direct(posts_folder: FolderTree, root: Photoset, community: Wall) -> None:
        posts_folders = folder_tree_parts(posts_folder)

        published_posts = community.get_posts()
        published_posts_ids = {post.id for post in published_posts}

        scheduled_posts = community.get_scheduled_posts()
        scheduled_posts_ids = {post.id for post in scheduled_posts}

        photoset_metafile = root.get_metafile()

        local_post_info = photoset_metafile.posts[community.id]
        posted_paths = {post.path for post in local_post_info}
        local_posts_ids = {post.post_id for post in local_post_info}

        for post_folder in posts_folders:
            post_path = post_folder.path.relative_to(root.path)

            if post_path in posted_paths:
                continue

            while True:  # handling post loop
                while True:  # ask loop
                    answer = input(
                        f"You have folder \"{post_path}\" without bound post. What would you like?\n"
                        f"* Enter a number - bind to existing post\n"
                        f"* Enter a \"-\" symbol - leave it as is\n"
                        f"* Just press Enter - open folder\n"
                        f"> "
                    )

                    answer = answer.strip()

                    if answer != "":
                        break

                    filesystem.open_file_manager(post_folder.path)

                if answer == "-":
                    break

                if answer.isdecimal():
                    post_id = int(answer)

                    if post_id in local_posts_ids:
                        print("This post is already associated with other path")

                        continue

                    if post_id in published_posts_ids:
                        status = PostStatus.PUBLISHED
                    elif post_id in scheduled_posts_ids:
                        status = PostStatus.SCHEDULED
                    else:
                        print("There is no such post")

                        continue

                    post_metafile = PostMetafile(post_path, post_id, status)

                    photoset_metafile.posts[community.id].append(post_metafile)
                    root.save_metafile(photoset_metafile)

                    break
