

from abc import abstractmethod
from dataclasses import dataclass
from typing import List

from justin.typer.stage_command.abstracts.simple_check import SimpleCheck
from justin.typer.stage_command.problems.problem import Problem
from justin.typer.stage_command.problems.path_problem import PathProblem
from justin.shared.filesystem import Folder
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafiles.metafile import PostMetafile, GroupMetafile, PostStatus, PersonMetafile, NoPostMetafile
from justin.shared.models.photoset import Photoset


# region Problems

class MissingPostMetafileProblem(PathProblem):
    def __str__(self) -> str:
        return f"Folder {self.path} doesn't have post metafile"


class MissingGroupMetafileProblem(PathProblem):
    def __str__(self) -> str:
        return f"Folder {self.path} doesn't have group metafile"


class MissingPersonMetafileProblem(PathProblem):
    def __str__(self) -> str:
        return f"Folder {self.path} doesn't have person metafile"


class UnpublishedPostProblem(PathProblem):
    def __str__(self) -> str:
        return f"Post at {self.path} is not published"


@dataclass(frozen=True)
class UnsentPersonPhotosProblem(Problem):
    name: str

    def __str__(self) -> str:
        return f"{self.name}'s photos not fully sent"


# endregion


# region Base

class DestinationsAwareCheck(SimpleCheck):
    """
    Базовый класс для чеков которые знают о структуре destinations
    (justin, closed, meeting, my_people и т.д.).
    """

    @abstractmethod
    def check_post_metafile(self, folder: Folder) -> List[Problem]:
        pass

    @abstractmethod
    def check_group_metafile(self, folder: Folder) -> List[Problem]:
        pass

    @abstractmethod
    def check_person_metafile(self, folder: Folder) -> List[Problem]:
        pass

    def get_problems(self, photoset: Photoset) -> List[Problem]:
        problems = []

        if photoset.justin is not None:
            problems += self.check_group_metafile(photoset.justin)

            for name_folder in photoset.justin.subfolders:
                for post_folder in folder_tree_parts(name_folder):
                    problems += self.check_post_metafile(post_folder)

        if photoset.timelapse and not NoPostMetafile.has(photoset.timelapse):
            problems += self.check_post_metafile(photoset.timelapse)

        def check_event(event_folder: Folder) -> List[Problem]:
            local_problems = self.check_group_metafile(event_folder)

            for post_folder in folder_tree_parts(event_folder):
                local_problems += self.check_post_metafile(post_folder)

            return local_problems

        if photoset.closed is not None:
            for name_folder in photoset.closed.subfolders:
                problems += check_event(name_folder)

        if photoset.meeting is not None:
            problems += check_event(photoset.meeting)

        if photoset.my_people is not None:
            problems += self.check_post_metafile(photoset.my_people)

            for person_folder in photoset.my_people.subfolders:
                problems += self.check_person_metafile(person_folder)

        return problems


# endregion


# region Concrete checks

class MetafilesExistCheck(DestinationsAwareCheck):
    @property
    def name(self) -> str:
        return "metafiles exist check"

    def check_post_metafile(self, folder: Folder) -> List[Problem]:
        if not PostMetafile.has(folder):
            return [MissingPostMetafileProblem(folder.path)]

        return []

    def check_group_metafile(self, folder: Folder) -> List[Problem]:
        if not GroupMetafile.has(folder):
            return [MissingGroupMetafileProblem(folder.path)]

        return []

    def check_person_metafile(self, folder: Folder) -> List[Problem]:
        if not PersonMetafile.has(folder):
            return [MissingPersonMetafileProblem(folder.path)]

        return []


class MetafilesPublishedCheck(DestinationsAwareCheck):
    @property
    def name(self) -> str:
        return "metafiles published check"

    def check_group_metafile(self, folder: Folder) -> List[Problem]:
        return []

    def check_post_metafile(self, folder: Folder) -> List[Problem]:
        post_metafile = PostMetafile.get(folder)

        if post_metafile.status != PostStatus.PUBLISHED:
            return [UnpublishedPostProblem(folder.path)]

        return []

    def check_person_metafile(self, folder: Folder) -> List[Problem]:
        person_metafile = PersonMetafile.get(folder)

        for comment_metafile in person_metafile.comments:
            if comment_metafile.status != PostStatus.PUBLISHED:
                return [UnsentPersonPhotosProblem(folder.name)]

        return []


# endregion
