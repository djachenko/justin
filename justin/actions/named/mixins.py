from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.models.photoset import Photoset
from justin_utils.util import same


class EventUtils:
    @staticmethod
    def get_community_id(posts_folder: FolderTree, root: Photoset) -> str:
        photoset_metafile = root.get_metafile()

        reverse_mapping = {}

        for community_id, post_metafiles in photoset_metafile.posts.items():
            for post_metafile in post_metafiles:
                reverse_mapping[post_metafile.path] = community_id

        ids_from_folder = []

        for part in folder_tree_parts(posts_folder):
            if part.path.relative_to(root.path) in reverse_mapping:
                ids_from_folder.append(reverse_mapping[part.path])

        if same(ids_from_folder):
            return str(ids_from_folder[0])

        answer = input(
            f"Which event contents of {posts_folder.path.relative_to(root.path)} belong to?\n"
            f"Enter event url: ",
        )

        answer = answer.strip()

        return answer
