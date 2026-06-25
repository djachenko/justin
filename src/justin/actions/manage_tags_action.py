from abc import abstractmethod
from argparse import Namespace
from dataclasses import make_dataclass, dataclass
from functools import cache
from typing import Type, List

from justin.cms_2.storage.google_sheets.google_sheets_database import Link
from justin.cms_2.storage.google_sheets.google_sheets_entries import PostEntry as GooglePost
from justin.cms_2.storage.sqlite.sqlite_entries import Tag, Post
from justin.shared.context import Context
from justin_utils.cli import Action, Parameter
from pyvko.aspects.groups import Group
from pyvko.aspects.posts import Post as VKPost

SourcePost = Post
GoogleClass = Type[GooglePost] | dataclass


class PostStrategy:
    def __init__(self, context: Context):
        super().__init__()

        self.__context = context

    @property
    @cache
    def tags(self) -> List[Tag]:
        sqlite_tags = self.__context.sqlite_cms.get_tags()
        sqlite_tags.sort(
            key=lambda tag: self.context.sqlite_cms.tag_usage_count(tag.tag_id),
            reverse=True
        )

        return sqlite_tags

    @property
    @cache
    def context(self) -> Context:
        return self.__context

    @cache
    def build_google_class(self) -> GoogleClass:
        return make_dataclass(
            "TaggedPost",
            fields=[(tag.clean_text, bool) for tag in self.tags],
            bases=(GooglePost,)
        )

    @abstractmethod
    def build_google_posts(self) -> List[GooglePost]:
        pass

    @abstractmethod
    def handle_changed_posts(self, changed_posts: List[GooglePost]) -> None:
        pass


class SqliteStrategy(PostStrategy):
    def __get_source_posts(self) -> List[SourcePost]:
        return self.context.sqlite_cms.get_indexed_posts()

    def build_google_posts(self) -> List[GooglePost]:
        source_posts = self.__get_source_posts()

        # noinspection PyPep8Naming
        TaggedPost = self.build_google_class()
        google_posts = []

        for sqlite_post in source_posts:
            is_already_synced = self.context.sqlite_cms.is_synced(sqlite_post.post_id, sqlite_post.group_id)

            if is_already_synced:
                continue

            post_id = sqlite_post.post_id
            group_id = sqlite_post.group_id

            tag_ids_of_post = self.context.sqlite_cms.get_tag_ids_of_post(post_id, group_id)

            params = {
                         "post_id": post_id,
                         "group_id": group_id,
                         "post_date": sqlite_post.date,
                         "synced": is_already_synced,
                         "link": Link(f"https://vk.com/wall{group_id}_{post_id}"),
                     } | {tag.clean_text: (tag.tag_id in tag_ids_of_post) for tag in self.tags}

            tagged_post = TaggedPost(**params)

            google_posts.append(tagged_post)

        return google_posts

    def handle_changed_posts(self, changed_posts: List[GooglePost]) -> None:
        for changed_post in changed_posts:
            post_id = changed_post.post_id
            group_id = changed_post.group_id

            existing_tag_ids = self.context.sqlite_cms.get_tag_ids_of_post(post_id, group_id)
            new_tag_ids = [tag.tag_id for tag in self.tags if getattr(changed_post, tag.clean_text)]

            ids_to_add = set(new_tag_ids).difference(existing_tag_ids)
            ids_to_delete = set(existing_tag_ids).difference(new_tag_ids)

            self.context.sqlite_cms.link_post_to_tags(post_id, group_id, *ids_to_add)
            self.context.sqlite_cms.unlink_post_to_tags(post_id, group_id, *ids_to_delete)

            if changed_post.synced:
                self.context.sqlite_cms.mark_synced(post_id, group_id)


class ScheduledStrategy(PostStrategy):
    @property
    def group(self) -> Group:
        return self.context.default_group

    @property
    @cache
    def scheduled_posts(self) -> List[VKPost]:
        return self.group.get_scheduled_posts()

    def build_google_posts(self) -> List[GooglePost]:
        # noinspection PyPep8Naming
        TaggedPost = self.build_google_class()

        google_posts = []
        group_id = self.group.id

        for scheduled_post in self.scheduled_posts:
            is_already_synced = self.context.sqlite_cms.is_synced(scheduled_post.post_id, group_id)

            if is_already_synced:
                continue

            post_id = scheduled_post.post_id
            group_id = group_id

            post_text = scheduled_post.text
            tags_in_text = [word for word in post_text.split() if Tag.is_tag(word)]
            tags_in_text = [tag.split("@")[0] for tag in tags_in_text]

            params = {
                         "post_id": post_id,
                         "group_id": group_id,
                         "post_date": scheduled_post.date,
                         "synced": is_already_synced,
                         "link": Link(f"https://vk.com/wall{group_id}_{post_id}"),
                     } | {tag.clean_text: (tag.text in tags_in_text) for tag in self.tags}

            tagged_post = TaggedPost(**params)

            google_posts.append(tagged_post)

        return google_posts

    def handle_changed_posts(self, changed_posts: List[GooglePost]) -> None:
        scheduled_posts_mapping = {post.post_id: post for post in self.scheduled_posts}

        for changed_post in changed_posts:
            scheduled_post = scheduled_posts_mapping[changed_post.post_id]

            post_text = scheduled_post.text
            tags_in_text = [word for word in post_text.split() if Tag.is_tag(word)]

            if tags_in_text:
                first_tag_position = post_text.find(tags_in_text[0])
                post_text = post_text[:first_tag_position]

            post_text = post_text.strip()

            new_tags = [tag for tag in self.tags if getattr(changed_post, tag.clean_text)]

            tags_string = " ".join(f"{tag.text}@{self.group.url}" for tag in new_tags)

            post_text = f"{post_text}\n\n{tags_string}"

            post_text.strip()

            scheduled_post.text = post_text

            self.group.update_post(scheduled_post)


class ManageTagsAction(Action):
    __POSTS = "posts"
    __SCHEDULED = "scheduled"
    __OLD = "old"

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(
                name=f"--{ManageTagsAction.__POSTS}",
                choices=[
                    ManageTagsAction.__SCHEDULED,
                    ManageTagsAction.__OLD,
                ],
            )
        ]

    def perform(self, args: Namespace, context: Context) -> None:
        post_type = getattr(args, ManageTagsAction.__POSTS, None)

        if post_type == ManageTagsAction.__SCHEDULED:
            strategy = ScheduledStrategy(context)
        elif post_type == ManageTagsAction.__OLD:
            strategy = SqliteStrategy(context)
        else:
            assert False

        google_posts = strategy.build_google_posts()

        if not google_posts:
            print("There is nothing to sync.")

            return

        google_posts_type = strategy.build_google_class()

        google_posts = google_posts[:20]

        sheets_db = context.sheets_db

        sheets_db.update(*google_posts)
        sheets_db.open(google_posts_type)

        input("> ")

        modified_posts = sheets_db.get_entries(google_posts_type)
        sheets_db.delete_sheet(google_posts_type)

        google_posts = {(post.post_id, post.group_id): post for post in google_posts}
        changed_posts = []

        for modified_post in modified_posts:
            original_post = google_posts[modified_post.post_id, modified_post.group_id]

            if original_post != modified_post:
                changed_posts.append(modified_post)

        strategy.handle_changed_posts(changed_posts)
