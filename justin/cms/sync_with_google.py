from collections import defaultdict
from dataclasses import make_dataclass
from pathlib import Path

from justin.cms.google_sheets_database import GoogleSheetsDatabase
from justin.cms.google_sheets_entries import PostEntry as GooglePost
from justin.cms_2.sqlite_database import SQLiteDatabase
from justin.cms_2.sqlite_entries import Post as SqlitePost, PostToTag, Tag
from justin_utils.util import group_by

if __name__ == '__main__':
    config_root = Path("../../.justin")

    sheets_db = GoogleSheetsDatabase(
        spreadsheet_id="1wpjgMa8PIsi7uVzkVG9G1Q_kP_lOnCgbBLKzZYssKzc",
        root=config_root / "google_sheets"
    )

    sqlite_db = SQLiteDatabase(config_root / "cms")

    with sqlite_db.connect():
        sqlite_posts = sqlite_db.get_entries(SqlitePost)
        posts_to_tags = sqlite_db.get_entries(PostToTag)
        sqlite_tags = sqlite_db.get_entries(Tag)

    text_tags = [tag.text.strip("#") for tag in sqlite_tags]

    TaggedPost = make_dataclass(
        "TaggedPost",
        fields=[(tag, bool) for tag in text_tags],
        bases=(GooglePost,)
    )

    google_posts = []

    for sqlite_post in sqlite_posts:
        tag_ids_of_post = [e.tag_id for e in posts_to_tags
                           if e.post_id == sqlite_post.post_id and e.group_id == sqlite_post.group_id]

        tags_of_post = [tag.text for tag in sqlite_tags if tag.tag_id in tag_ids_of_post]

        params = {
                     "post_id": sqlite_post.post_id,
                     "group_id": sqlite_post.group_id,
                     "post_date": sqlite_post.date,
                     # "link": sqlite_post.text,
                 } | {tag: f"#{tag}" in tags_of_post for tag in text_tags}

        tagged_post = TaggedPost(**params)

        google_posts.append(tagged_post)

    google_posts = google_posts[:10]
    google_posts = {(post.post_id, post.group_id): post for post in google_posts}

    sheets_db.update(*google_posts.values())
    sheets_db.open(TaggedPost)

    input()

    tagged_results = sheets_db.get_entries(TaggedPost)

    for result in tagged_results:
        pretagged_post = google_posts[result.post_id, result.group_id]

        if pretagged_post == result:
            continue
        else:
            a = 7

    sheets_db.delete_sheet(TaggedPost)

    a = 7
