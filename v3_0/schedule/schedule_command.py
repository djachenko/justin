import random
from datetime import datetime, timedelta, time, date
from pathlib import Path
from typing import List

from pyvko.photos.photo import Photo
from pyvko.post import Post
from pyvko.pyvko import Pyvko

from justin import Args
from v3_0.commands.command import Command
from v3_0.shared.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.shared.models.photoset import Photoset


class ScheduleCommand(Command):
    def configure_parser(self, parser_adder):
        pass

    def run(self, args: Args):
        ready_path = Path("D:/photos/stages/stage3.schedule")

        stage_tree = SingleFolderTree(ready_path)

        photosets = [Photoset(subtree) for subtree in stage_tree.subtrees]

        # get all scheduled
        # find last date
        # setup interval
        # 
        #

        pyvko = Pyvko(Path("config.json"))

        group = pyvko.get_group("pyvko_test2")

        scheduled_posts = group.get_scheduled_posts()

        scheduled_dates = [post.date for post in scheduled_posts]

        scheduled_dates.sort(reverse=True)

        if len(scheduled_dates) > 0:
            last_date = scheduled_dates[0].date()
        else:
            last_date = date.today()

        interval = timedelta(days=3)
        counter = 1

        photo_uploader = pyvko.get_photos_uploader()

        for photoset in photosets:
            justin_folder = photoset.justin

            for hashtag in justin_folder.subtrees:
                parts = PartingHelper.folder_tree_parts(hashtag)

                for part in parts:
                    assert len(part.subtrees) == 0

                    photo_files = part.files

                    vk_photos = [photo_uploader.upload_to_wall(group.id, file.path) for file in
                                 photo_files]

                    post_date = last_date + interval * counter
                    post_time = time(
                        hour=random.randint(8, 23),
                        minute=random.randint(0, 59),
                    )

                    post_datetime = datetime.combine(post_date, post_time)

                    counter += 1

                    post = Post(
                        text=f"#{hashtag.name}@djachenko",
                        attachments=vk_photos,
                        date=post_datetime
                    )

                    post_id = group.add_post(post)

                    print(post_id)


if __name__ == '__main__':
    ScheduleCommand().run(None)
