from functools import partial
from pathlib import Path
from typing import List, Callable, Annotated

import typer
from typer import Typer, Argument

from justin.actions.mixins import EventUtils
from justin.shared.helpers.parts import folder_tree_parts, is_part
from justin.shared.metafiles.metafile import PostStatus, PostMetafile, GroupMetafile, NoPostMetafile
from justin.shared.models.photoset import Photoset
from justin.typer.base_commands.destinations_aware_command import DestinationsAwareCommand
from justin.typer.base_commands.pattern_command import Extra
from justin.typer.fix_metafile_output import FixMetafileOutput, make_fix_metafile_output
from justin_utils.filesystem import Folder
from justin_utils.util import bfs
from pyvko.aspects.events import Event, Events
from pyvko.aspects.groups import Group
from pyvko.aspects.posts import Posts


class FixMetafileCommand(DestinationsAwareCommand, EventUtils):
    __ROOT_KEY = "root"
    __SET_PATH_KEY = "set_path"

    def __init__(self, context, patterns, output: FixMetafileOutput) -> None:
        super().__init__(context, patterns)

        self.__cache: dict[int, tuple[set[int], set[int]]] = {}
        self.__output = output

    def __warmup_cache(self, group: Posts) -> None:
        if group.id in self.__cache:
            return

        published_posts_ids = {post.id for post in group.get_posts()}
        scheduled_posts_ids = {post.id for post in group.get_scheduled_posts()}

        self.__cache[group.id] = (published_posts_ids, scheduled_posts_ids)

    def run_for_photoset(self, photoset: Photoset, extra: Extra) -> None:
        super().run_for_photoset(photoset, extra | {
            FixMetafileCommand.__SET_PATH_KEY: photoset.path,
        })

    def run_for_part(self, part: Photoset, extra: Extra) -> None:
        set_path: Path = extra[FixMetafileCommand.__SET_PATH_KEY]

        self.__output.on_fixing_part(str(part.path.relative_to(set_path.parent)))

        super().run_for_part(part, extra | {
            FixMetafileCommand.__ROOT_KEY: part,
        })

    def handle_closed(self, closed_folder: Folder, extra: Extra) -> None:
        self.__fix_categories(
            closed_folder.subfolders,
            partial(self.__get_event, self.context.closed_group),
            extra
        )

    def handle_drive(self, drive_folder: Folder, extra: Extra) -> None:
        pass

    def handle_justin(self, justin_folder: Folder, extra: Extra) -> None:
        self.__fix_group(justin_folder, self.context.justin_group)

        self.__fix_categories(
            justin_folder.subfolders,
            lambda folder, root: self.context.justin_group,
            extra
        )

    def handle_meeting(self, meeting_folder: Folder, extra: Extra) -> None:
        self.__fix_categories(
            [meeting_folder],
            partial(self.__get_event, self.context.meeting_group),
            extra
        )

    def handle_kot_i_kit(self, kot_i_kit_folder: Folder, extra: Extra) -> None:
        skip_subtrees = ["logo", "market", "service"]

        self.__fix_group(kot_i_kit_folder, self.context.kot_i_kit_group)

        self.__fix_categories(
            [tree for tree in kot_i_kit_folder.subfolders if tree.name not in skip_subtrees and not is_part(tree)],
            lambda folder, root: self.context.kot_i_kit_group,
            extra
        )

    def handle_my_people(self, my_people_folder: Folder, extra: Extra) -> None:
        pass

    def handle_timelapse(self, timelapse_folder: Folder, extra: Extra) -> None:
        if NoPostMetafile.has(timelapse_folder):
            return

        if timelapse_metafile := GroupMetafile.get(timelapse_folder):
            group_id = str(timelapse_metafile.group_id)
            group = self.context.pyvko.get(group_id)
        else:
            root = timelapse_folder.parent
            group_ids = []

            def collect_group_ids(folder: Folder) -> List[Folder]:
                if group_metafile := GroupMetafile.get(folder):

                    group_ids.append(group_metafile.group_id)

                    return []
                else:
                    return folder.subfolders

            bfs(root, collect_group_ids)

            communities = [self.context.pyvko.get(group_id) for group_id in group_ids]
            # noinspection PyUnresolvedReferences
            names_mapping = {community.name: community for community in communities}
            other = "Other community"
            no_post = "Wasn't published"

            name = self.__output.ask_timelapse_community(list(names_mapping.keys()) + [other, no_post])

            if name == other:
                group_id = self.__output.ask_community_id()
                group = self.context.pyvko.get(group_id)
            elif name == no_post:
                NoPostMetafile().save(timelapse_folder)

                return
            else:
                group = names_mapping[name]

        assert isinstance(group, Group | Event)

        self.__fix_group(timelapse_folder, group)
        self.__fix_posts(timelapse_folder, extra[FixMetafileCommand.__ROOT_KEY], group)

    def handle_common(self, folder: Folder, extra: Extra) -> None:
        pass

    @staticmethod
    def __fix_group(folder: Folder, group: Posts) -> None:
        if GroupMetafile.has(folder):
            return

        GroupMetafile(group_id=group.id).save(folder)

    def __fix_categories(
            self,
            categories: List[Folder],
            group_provider: Callable[[Folder, Photoset], Posts | None],
            extra: Extra
    ) -> None:
        root = extra[FixMetafileCommand.__ROOT_KEY]

        for category in categories:
            community = group_provider(category, root)

            if community is None:
                continue

            self.__fix_posts(category, root, community)

    def __get_event(self, community: Events, category: Folder, root: Photoset) -> Posts | None:
        event_id = FixMetafileCommand.get_community_id(category, root)

        if event_id is None:
            return None

        event = community.get_event(event_id)

        if event is not None:
            self.__fix_group(category, event)

        return event

    def __fix_posts(self, posts_folder: Folder, root: Photoset, community: Posts) -> None:
        self.__warmup_cache(community)

        published_posts_ids, scheduled_posts_ids = self.__cache[community.id]

        for post_folder in folder_tree_parts(posts_folder):
            if PostMetafile.get(post_folder) is not None:
                continue

            post_path = post_folder.path.relative_to(root.path)

            while True:
                answer = self.__output.ask_post_action(post_path)

                if answer == "-":
                    break

                if answer.isdecimal():
                    post_id = int(answer)

                    if post_id in published_posts_ids:
                        status = PostStatus.PUBLISHED
                    elif post_id in scheduled_posts_ids:
                        status = PostStatus.SCHEDULED
                    else:
                        self.__output.on_no_such_post()

                        continue

                    PostMetafile(post_id=post_id, status=status).save(post_folder)

                    break


app = Typer()


@app.command()
def fix_metafile(
        context: Annotated[typer.Context, Argument()],
        pattern: Annotated[List[Path], Argument()] = (Path.cwd(),)  # type: ignore[assignment]
) -> None:
    FixMetafileCommand(context.obj, pattern, make_fix_metafile_output()).run()
