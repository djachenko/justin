from argparse import Namespace
from typing import List

from pyvko.models.models import Post

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.shared import filesystem
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PostStatus
from justin.shared.models.photoset import Photoset


class FixMetafileAction(NamedAction):
    __POSTS_KEY = "posts"

    def get_extra(self, context: Context) -> Extra:
        return {
            **super().get_extra(context),
            **{
                FixMetafileAction.__POSTS_KEY: context.default_group.get_posts()
            },
        }

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        group = context.default_group
        posts: List[Post] = extra[FixMetafileAction.__POSTS_KEY]

        remote_posts_ids = {post.id for post in posts}

        photoset_metafile = part.get_metafile()

        local_post_info = photoset_metafile.posts.get(group.id, [])
        posted_paths = [post.path for post in local_post_info]
        local_posts_ids = {post.post_id for post in local_post_info}

        print(f"Fixing metafile for {part.name} photoset.")

        justin_folder = part.justin

        for hashtag in justin_folder.subtrees:
            parts = folder_tree_parts(hashtag)

            for hashtag_part in parts:
                hashtag_part_path = hashtag_part.path.relative_to(part.path)

                if hashtag_part_path in posted_paths:
                    continue

                while True:  # handling post loop
                    while True:  # ask loop
                        answer = input(
                            f"You have folder \"{hashtag_part_path}\" without bound post. What would you like?\n"
                            f"* Enter a number - bind to existing post\n"
                            f"* Enter a \"-\" symbol - leave it as is\n"
                            f"* Just press Enter - open folder\n"
                            f"> "
                        )

                        answer = answer.strip()

                        if answer != "":
                            break

                        filesystem.open_file_manager(hashtag_part.path)

                    if answer == "-":
                        break

                    if answer.isdecimal():
                        post_id = int(answer)

                        if post_id in local_posts_ids:
                            print("This post is already associated with other path")

                            continue

                        if post_id not in remote_posts_ids:
                            print("There is no such post")

                            continue

                        post_metafile = PostMetafile(hashtag_part_path, post_id, PostStatus.PUBLISHED)

                        local_post_info.append(post_metafile)
                        photoset_metafile.posts[group.id] = local_post_info
                        part.save_metafile(photoset_metafile)

                        break
