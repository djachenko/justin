from argparse import Namespace
from collections import defaultdict
from typing import List
from urllib.parse import urlparse

from justin.actions.group_action import GroupAction
from justin.shared.context import Context
from justin_utils.cli import Parameter
from justin_utils.util import stride
from pyvko.aspects.albums import Album
from pyvko.aspects.groups import Group


class GetLikersAction(GroupAction):
    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("posts", nargs="+"),
        ]

    def perform_for_group(self, group: Group, args: Namespace, context: Context) -> None:
        post_ids = []

        for post in args.posts:
            parse_result = urlparse(post)

            path = parse_result.path
            path = path.strip("/")

            assert path.startswith("wall")

            path = path.strip("wall")

            _, post_id = path.split("_")

            post_id = int(post_id)

            post_ids.append(post_id)

        posts = group.get_posts(*post_ids)
        group_id = group.id

        likers = defaultdict(lambda: 0)

        pyvko = context.pyvko

        for post in posts:
            for like in post.get_likes():
                likers[like.author_id] += 1

            for attachment in post.attachments:
                if not isinstance(attachment, Album):
                    continue

                for photo_chunk in stride(attachment.get_photos(), 25):
                    photo_ids = [photo.id for photo in photo_chunk]

                    calls = []

                    for photo_id in photo_ids:
                        calls.append("\n".join([
                            f"\t\"{photo_id}\": API.likes.getList({{",
                            f"\t\t\"item_id\": {photo_id},",
                            f"\t\t\"owner_id\": {group_id},",
                            f"\t\t\"type\": \"photo\", ",
                            f"\t\t\"v\": 5.199",
                            f"\t}})",
                        ]))

                    code = "\n".join([
                        "return {",
                        ",\n".join(calls),
                        "};"
                    ])

                    response = pyvko.execute(code)

                    for likers_list in response.values():
                        for liker_id in likers_list["items"]:
                            likers[liker_id] += 1

        for liker_id in sorted(likers, key=lambda x: likers[x], reverse=True):
            liker = pyvko.get_user(liker_id)
            likes_count = likers[liker_id]

            print(f"{liker.first_name} {liker.last_name} ({liker.url}): {likes_count}")
