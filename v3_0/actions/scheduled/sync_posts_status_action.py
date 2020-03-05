from argparse import Namespace

from pyvko.models.group import Group

from v3_0.actions.scheduled.scheduled_action import ScheduledAction
from v3_0.shared.metafiles.post_metafile import PostStatus
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class SyncPostsStatusAction(ScheduledAction):
    def perform(self, args: Namespace, world: World, group: Group) -> None:
        stage_tree = self.tree_with_sets(world)

        photosets = [Photoset(subtree) for subtree in stage_tree.subtrees]

        scheduled_posts = group.get_scheduled_posts()
        published_posts = group.get_posts()

        scheduled_ids = [post.id for post in scheduled_posts]

        published_ids = [post.id for post in published_posts]
        published_timed_ids = [post.timer_id for post in published_posts]
        published_mapping = dict(zip(published_timed_ids, published_ids))

        print("Performing sync of local state with web...")

        for photoset in photosets:
            photoset_metafile = photoset.get_metafile()

            existing_posts = []

            for post_metafile in photoset_metafile.posts[group.url]:
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

            photoset_metafile.posts[group.url] = existing_posts
            photoset.save_metafile(photoset_metafile)

        print("Performed successfully")
