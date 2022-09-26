from argparse import Namespace
from functools import partial
from pathlib import Path
from typing import List, Callable

from justin.actions.named.destinations_aware_action import DestinationsAwareAction
from justin.actions.named.mixins import EventUtils
from justin.actions.named.named_action import Context, Extra
from justin.shared import filesystem
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts, is_part
from justin.shared.metafile import PostStatus, PostMetafile, GroupMetafile
from justin.shared.models.photoset import Photoset
from pyvko.aspects.events import Events
from pyvko.aspects.posts import Posts


class FixMetafileAction(DestinationsAwareAction, EventUtils):
    __ROOT_KEY = "root"
    __SET_PATH_KEY = "set_path"

    def __init__(self) -> None:
        super().__init__()

        self.__cache = {}

    def __warmup_cache(self, group: Posts):
        if group.id in self.__cache:
            return

        published_posts = group.get_posts()
        scheduled_posts = group.get_scheduled_posts()

        published_posts_ids = {post.id for post in published_posts}
        scheduled_posts_ids = {post.id for post in scheduled_posts}

        self.__cache[group.id] = (published_posts_ids, scheduled_posts_ids)

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        extra[FixMetafileAction.__SET_PATH_KEY] = photoset.path

        super().perform_for_photoset(photoset, args, context, extra)

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        set_path: Path = extra[FixMetafileAction.__SET_PATH_KEY]

        print(f"Fixing metafile for {part.path.relative_to(set_path.parent)} photoset.")

        extra[FixMetafileAction.__ROOT_KEY] = part

        super().perform_for_part(part, args, context, extra)

    def handle_justin(self, justin_folder: FolderTree, context: Context, extra: Extra) -> None:
        self.__fix_group(justin_folder, context.justin_group)

        self.__fix_categories(
            justin_folder.subtrees,
            lambda a, b: context.justin_group,
            extra
        )

    def handle_closed(self, closed_folder: FolderTree, context: Context, extra: Extra) -> None:
        # noinspection PyTypeChecker
        self.__fix_categories(
            closed_folder.subtrees,
            partial(self.__get_event, context.closed_group),
            extra
        )

    def handle_meeting(self, meeting_folder: FolderTree, context: Context, extra: Extra) -> None:
        # noinspection PyTypeChecker
        self.__fix_categories(
            [meeting_folder],
            partial(self.__get_event, context.meeting_group),
            extra
        )

    def handle_kot_i_kit(self, kot_i_kit_folder: FolderTree, context: Context, extra: Extra) -> None:
        skip_subtrees = [
            "logo",
            "market",
            "service",
        ]

        self.__fix_group(kot_i_kit_folder, context.kot_i_kit_group)

        self.__fix_categories(
            [tree for tree in kot_i_kit_folder.subtrees if tree.name not in skip_subtrees and not is_part(tree)],
            lambda a, b: context.kot_i_kit_group,
            extra
        )

    def handle_my_people(self, my_people_folder: FolderTree, context: Context, extra: Extra) -> None:
        # todo: notify if fixing required
        pass

    # noinspection PyMethodMayBeStatic
    def __fix_group(self, folder: FolderTree, group: Posts) -> None:
        if folder.has_metafile(GroupMetafile):
            return

        # todo: здесь групповой метафайл может записаться в папку части внутри митинга

        folder.save_metafile(GroupMetafile(
            group_id=group.id
        ))

    def __fix_categories(
            self,
            categories: List[FolderTree],
            group_provider: Callable[[FolderTree, Photoset], Posts],
            extra: Extra
    ):
        root = extra[FixMetafileAction.__ROOT_KEY]

        for category in categories:
            community = group_provider(category, root)

            if community is None:
                continue

            self.__fix_posts(
                posts_folder=category,
                root=root,
                community=community
            )

    def __get_event(self, community: Events, category: FolderTree, root: Photoset) -> Posts | None:
        event_id = FixMetafileAction.get_community_id(category, root)

        if event_id is None:
            return None

        event_id = str(abs(int(event_id)))

        event = community.get_event(event_id)

        if event is not None:
            self.__fix_group(category, event)

        return event

    def __fix_posts(self, posts_folder: FolderTree, root: Photoset, community: Posts) -> None:
        posts_folders = folder_tree_parts(posts_folder)

        self.__warmup_cache(community)

        published_posts_ids, scheduled_posts_ids = self.__cache[community.id]

        for post_folder in posts_folders:
            post_path = post_folder.path.relative_to(root.path)

            metafile = post_folder.get_metafile(PostMetafile)

            if metafile is not None:
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

                    # todo: check globally with cms
                    # if post_id in local_posts_ids:
                    #     print("This post is already associated with other path")
                    #
                    #     continue

                    if post_id in published_posts_ids:
                        status = PostStatus.PUBLISHED
                    elif post_id in scheduled_posts_ids:
                        status = PostStatus.SCHEDULED
                    else:
                        print("There is no such post")

                        continue

                    metafile = PostMetafile(
                        post_id=post_id,
                        status=status,
                    )

                    post_folder.save_metafile(metafile)

                    break
