from dataclasses import make_dataclass
from pathlib import Path

from justin.cms.google_sheets_database import GoogleSheetsDatabase, Link
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

    posts_to_tags_mapping = group_by(lambda ptt: (ptt.post_id, ptt.group_id), posts_to_tags)
    tag_id_to_tag = {tag.tag_id: tag for tag in sqlite_tags}

    google_posts = []

    for sqlite_post in sqlite_posts:
        post_id = sqlite_post.post_id
        group_id = sqlite_post.group_id
        tag_ids_of_post = [e.tag_id for e in posts_to_tags_mapping[post_id, group_id]]

        # tags_of_post = [tag.text for tag in sqlite_tags if tag.tag_id in tag_ids_of_post]

        tags_of_post = [tag_id_to_tag[tag_id].text for tag_id in tag_ids_of_post]

        params = {
                     "post_id": post_id,
                     "group_id": group_id,
                     "post_date": sqlite_post.date,
                     "link": Link(f"https://vk.com/wall{group_id}_{post_id}"),
                 } | {tag: (f"#{tag}" in tags_of_post) for tag in text_tags}

        tagged_post = TaggedPost(**params)

        google_posts.append(tagged_post)

    google_posts = google_posts[:10]
    google_posts = {(post.post_id, post.group_id): post for post in google_posts}

    sheets_db.update(*google_posts.values())
    sheets_db.open(TaggedPost)

    input()

    tagged_results = sheets_db.get_entries(TaggedPost)
    sheets_db.delete_sheet(TaggedPost)

    changed = []

    for result in tagged_results:
        pretagged_post = google_posts[result.post_id, result.group_id]

        if pretagged_post == result:
            continue
        else:
            changed.append(result)

    ptts_to_delete = []
    ptts_to_add = []

    for changed_post in changed:
        changed_post: GooglePost

        post_id = changed_post.post_id
        group_id = changed_post.group_id

        existing_tag_ids = [ptt.tag_id for ptt in posts_to_tags_mapping[post_id, group_id]]
        new_tag_ids = [tag.tag_id for tag in sqlite_tags if getattr(changed_post, tag.text.strip("#"))]

        ids_to_add = set(new_tag_ids).difference(existing_tag_ids)
        ids_to_delete = set(existing_tag_ids).difference(new_tag_ids)

        ptts_to_add += [PostToTag(group_id, post_id, tag_id) for tag_id in ids_to_add]
        ptts_to_delete += [PostToTag(group_id, post_id, tag_id) for tag_id in ids_to_delete]

    with sqlite_db.connect():
        sqlite_db.delete(ptts_to_delete)
        sqlite_db.update(ptts_to_add)


    a = 7
