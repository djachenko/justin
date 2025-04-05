from pathlib import Path

from justin.cms.people_cms import PeopleCMS


class CMS(PeopleCMS):
    def __init__(self, root: Path) -> None:
        super().__init__()

        self.__root = root

    @property
    def root(self) -> Path:
        return self.__root
