from justin.shared import filesystem
from justin.shared.filesystem import Folder
from justin.shared.metafile import GroupMetafile
from justin.shared.models.photoset import Photoset


class EventUtils:
    @staticmethod
    def get_community_id(posts_folder: Folder, root_photoset: Photoset) -> str | None:
        root_path = root_photoset.path

        group_metafile = GroupMetafile.get(posts_folder)

        if group_metafile is not None:
            return str(group_metafile.group_id)

        print(f"Which community contents of {posts_folder.path.relative_to(root_path)} belong to?")

        while True:
            answer = input(
                f"Enter event url: ",
            )

            if not answer:
                filesystem.open_file_manager(posts_folder.path)
            elif not EventUtils.__validate(answer):
                print("This was not event url. Try another.")
            else:
                break

        if answer == "-":
            return None
        else:
            return answer

    @staticmethod
    def __validate(event_url: str) -> bool:
        return event_url is not None
