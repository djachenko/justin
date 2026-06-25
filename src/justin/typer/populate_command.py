from pathlib import Path
from random import shuffle
from typing import Annotated, List

import typer
from typer import Typer, Argument

from justin.actions.pattern_action import Extra
from justin.shared.filesystem import Folder
from justin.shared.metafiles.metafile import PostMetafile, AlbumMetafile, GroupMetafile
from justin.typer.base_commands.pattern_command import PatternCommand


class PopulateCommand(PatternCommand):
    def run_for_folder(self, folder: Folder, extra: Extra) -> None:
        post_metafile = PostMetafile.get(folder)
        album_metafile = AlbumMetafile.get(folder)
        group_metafile = GroupMetafile.get(folder)

        group = self.context.pyvko.get(group_metafile.group_id)
        album = group.get_album_by_id(album_metafile.album_id)
        post = group.get_post(post_metafile.post_id)

        photos = album.get_photos()
        photo_indices = list(range(len(photos)))

        existing_attachments = post.attachments

        while True:
            shuffle(photo_indices)

            indices_for_post = photo_indices[:9 - len(existing_attachments)]
            indices_for_post.sort()
            photos_for_post = [photos[i] for i in indices_for_post]

            post.attachments = existing_attachments + photos_for_post

            group.update_post(post)

            if input("ok? > "):
                break


app = Typer()


@app.command()
def populate(
    context: Annotated[typer.Context, Argument()],
    pattern: Annotated[List[Path], Argument()] = (Path.cwd(),)
) -> None:
    PopulateCommand(context.obj, pattern).run()


