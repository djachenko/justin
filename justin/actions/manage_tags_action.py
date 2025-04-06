from argparse import Namespace
from dataclasses import make_dataclass
from typing import Type

from justin.cms_2.storage.google_sheets.google_sheets_database import Link
from justin.cms_2.storage.google_sheets.google_sheets_entries import PostEntry as GooglePost
from justin.shared.context import Context
from justin_utils.cli import Action


class ManageTagsAction(Action):
    def perform(self, args: Namespace, context: Context) -> None:
        sqlite_posts = context.sqlite_cms.get_indexed_posts()
        sqlite_tags = context.sqlite_cms.get_tags()

        sqlite_tags.sort(key=lambda tag: context.sqlite_cms.tag_usage_count(tag.tag_id), reverse=True)

        # noinspection PyPep8Naming,PyTypeChecker
        TaggedPost: Type[GooglePost] = make_dataclass(
            "TaggedPost",
            fields=[(tag.clean_text, bool) for tag in sqlite_tags],
            bases=(GooglePost,)
        )

        google_posts = []

        for sqlite_post in sqlite_posts:
            is_already_synced = context.sqlite_cms.is_synced(sqlite_post.post_id, sqlite_post.group_id)

            if is_already_synced:
                continue

            post_id = sqlite_post.post_id
            group_id = sqlite_post.group_id

            tag_ids_of_post = context.sqlite_cms.get_tag_ids_of_post(post_id, group_id)

            params = {
                         "post_id": post_id,
                         "group_id": group_id,
                         "post_date": sqlite_post.date,
                         "synced": is_already_synced,
                         "link": Link(f"https://vk.com/wall{group_id}_{post_id}"),
                     } | {tag.clean_text: (tag.tag_id in tag_ids_of_post) for tag in sqlite_tags}

            tagged_post = TaggedPost(**params)

            google_posts.append(tagged_post)

        if not google_posts:
            print("There is nothing to sync.")

            return

        google_posts = google_posts[:20]

        context.sheets_db.update(*google_posts)
        context.sheets_db.open(TaggedPost)

        input()

        modified_posts = context.sheets_db.get_entries(TaggedPost)
        context.sheets_db.delete_sheet(TaggedPost)

        google_posts = {(post.post_id, post.group_id): post for post in google_posts}
        changed_posts = []

        for modified_post in modified_posts:
            original_post = google_posts[modified_post.post_id, modified_post.group_id]

            if original_post != modified_post:
                changed_posts.append(modified_post)

        for changed_post in changed_posts:
            changed_post: GooglePost

            post_id = changed_post.post_id
            group_id = changed_post.group_id

            existing_tag_ids = context.sqlite_cms.get_tag_ids_of_post(post_id, group_id)
            new_tag_ids = [tag.tag_id for tag in sqlite_tags if getattr(changed_post, tag.clean_text)]

            ids_to_add = set(new_tag_ids).difference(existing_tag_ids)
            ids_to_delete = set(existing_tag_ids).difference(new_tag_ids)

            context.sqlite_cms.link_post_to_tags(post_id, group_id, *ids_to_add)
            context.sqlite_cms.unlink_post_to_tags(post_id, group_id, *ids_to_delete)

            if changed_post.synced:
                context.sqlite_cms.mark_synced(post_id, group_id)
