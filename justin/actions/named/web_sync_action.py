from argparse import Namespace

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.shared.metafile import PostStatus
from justin.shared.models.photoset import Photoset


class WebSyncAction(NamedAction):
    __SCHEDULED_IDS = "scheduled_ids"
    __PUBLISHED_IDS = "published_ids"
    __TIMED_IDS = "timed_ids"
    __PUBLISHED_MAPPING = "published_mapping"

    def get_extra(self, context: Context) -> Extra:
        scheduled_posts = context.default_group.get_scheduled_posts()
        published_posts = context.default_group.get_posts()

        scheduled_ids = [post.id for post in scheduled_posts]

        published_ids = [post.id for post in published_posts]
        published_timed_ids = [post.timer_id for post in published_posts]
        published_mapping = dict(zip(published_timed_ids, published_ids))

        return {
            **super().get_extra(context),
            **{
                WebSyncAction.__SCHEDULED_IDS: scheduled_ids,
                WebSyncAction.__PUBLISHED_IDS: published_ids,
                WebSyncAction.__TIMED_IDS: published_timed_ids,
                WebSyncAction.__PUBLISHED_MAPPING: published_mapping,
            },
        }

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        scheduled_ids = extra[WebSyncAction.__SCHEDULED_IDS]

        published_ids = extra[WebSyncAction.__PUBLISHED_IDS]
        published_timed_ids = extra[WebSyncAction.__TIMED_IDS]
        published_mapping = extra[WebSyncAction.__PUBLISHED_MAPPING]

        group = context.default_group

        print(f"Web syncing {part.name}...")

        part_metafile = part.get_metafile()

        existing_posts = []

        for post_metafile in part_metafile.posts[group.url]:
            post_id = post_metafile.post_id

            print(f"Syncing post with id {post_id}... ", end="")

            if post_metafile.status is PostStatus.SCHEDULED:

                if post_id in scheduled_ids:
                    print("still scheduled")

                    existing_posts.append(post_metafile)

                elif post_id in published_timed_ids:
                    post_metafile.status = PostStatus.PUBLISHED
                    post_metafile.post_id = published_mapping[post_id]

                    print(f"was published, now has id {post_metafile.post_id}")

                    existing_posts.append(post_metafile)
                elif post_id in published_ids:
                    # scheduled id can't become an id for published post

                    print("somehow ended in posted array, aborting...")

                    assert False

                else:
                    print("was deleted")

            elif post_metafile.status is PostStatus.PUBLISHED:
                assert post_id not in scheduled_ids
                assert post_id not in published_timed_ids

                if post_id in published_ids:
                    print("still published")

                    existing_posts.append(post_metafile)
                else:
                    print("was deleted")

        part_metafile.posts[group.url] = existing_posts
        part.save_metafile(part_metafile)

        print("Performed successfully")
