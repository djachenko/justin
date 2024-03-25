from pathlib import Path

from justin.cms.people_cms import PeopleCMS
from justin.cms.posts_cms import PostsCMS
from justin.cms_old.photosets_cms import PhotosetsCMS


class CMS(PostsCMS, PhotosetsCMS, PeopleCMS):
    def __init__(self, root: Path) -> None:
        super().__init__()

        self.__root = root

    @property
    def root(self) -> Path:
        return self.__root
