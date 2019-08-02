from pathlib import Path

from pyvko.pyvko import Pyvko


def main():
    pyvko = Pyvko(Path("pyvko_config.json"))

    group = pyvko.get_group("pyvko_test2")

    scheduled_posts = group.get_scheduled_posts()
    published_posts = group.get_posts()

    all_post_ids = [post.id for post in scheduled_posts + published_posts]

    for post_id in all_post_ids:
        group.delete_post(post_id)

        print(post_id)


if __name__ == '__main__':
    main()
