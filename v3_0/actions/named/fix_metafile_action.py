from argparse import Namespace

from pyvko.models.group import Group

from v3_0.actions.named.named_action import NamedAction
from v3_0.shared.filesystem import fs
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.shared.metafiles.post_metafile import PostMetafile, PostStatus
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class FixMetafileAction(NamedAction):
    def perform_for_photoset(self, photoset: Photoset, args: Namespace, world: World, group: Group) -> None:
        justin_folder = photoset.justin

        photoset_metafile = photoset.get_metafile()

        local_post_info = photoset_metafile.posts[group.url]
        posted_paths = [post.path for post in local_post_info]
        local_post_ids = {post.post_id for post in local_post_info}

        parts_to_upload = []

        print(f"Fixing metafile for {photoset.name} photoset.")

        for hashtag in justin_folder.subtrees:
            parts = PartingHelper.folder_tree_parts(hashtag)

            for part in parts:
                part_path = part.path.relative_to(photoset.path)

                if part_path not in posted_paths:
                    parts_to_upload.append(part)

        posts = group.get_posts()

        posts_id_mapping = {post.id: post for post in posts}

        for part in parts_to_upload:
            part_path = part.path.relative_to(photoset.path)

            while True:  # handling post loop
                while True:  # ask loop
                    answer = input(f"You have folder \"{part_path}\" without corresponding post. What would you like?\n"
                                   f"* Enter a number - bind to existing post\n"
                                   f"* Enter a \"-\" symbol - leave it as is\n"
                                   f"* Just press Enter - open folder\n"
                                   f"> ")

                    answer = answer.strip()

                    if answer != "":
                        break

                    fs.open_file_manager(part.path)

                if answer == "-":
                    break

                elif answer.isdecimal():
                    post_id = int(answer)

                    if post_id in local_post_ids:
                        print("This post is already associated with other path")

                        continue

                    if post_id not in posts_id_mapping:
                        print("There is no such post")

                        continue

                    post_metafile = PostMetafile(part_path, post_id, PostStatus.PUBLISHED)

                    local_post_info.append(post_metafile)
                    photoset_metafile.posts[group.url] = local_post_info
                    photoset.save_metafile(photoset_metafile)

                    break
