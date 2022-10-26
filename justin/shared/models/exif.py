from abc import abstractmethod
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from justin.shared.filesystem import File


class Exif:
    @property
    @abstractmethod
    def date_taken(self) -> datetime:
        pass

    @property
    @abstractmethod
    def available_names(self):
        pass

    def __lt__(self, other: 'Exif'):
        return self.date_taken < other.date_taken


class PillowExif(Exif):
    from PIL import ExifTags
    from PIL.Image import Exif as PilExif

    __reverse_mapping = {v: k for k, v in ExifTags.TAGS.items()}

    @property
    @lru_cache()
    def date_taken(self) -> datetime:
        return datetime.strptime(
            self.__get_tag_value("DateTimeOriginal") or self.__get_tag_value("DateTime"),
            "%Y:%m:%d %H:%M:%S"
        )

    @property
    def available_names(self):
        return [k for k, v in PillowExif.__reverse_mapping.items() if v in self.source_exif]

    def __get_tag_value(self, tag: str) -> str | None:
        return self.source_exif.get(PillowExif.__reverse_mapping[tag])

    def __init__(self, exif: PilExif) -> None:
        super().__init__()

        self.source_exif = exif

    @classmethod
    def from_path(cls, path: Path) -> 'PillowExif':
        from PIL import Image

        return PillowExif(Image.open(path).getexif())


class NativeExif(Exif):
    from exif import Image

    @property
    @lru_cache()
    def date_taken(self) -> datetime:
        return datetime.strptime(
            self.source_exif.datetime_original,
            "%Y:%m:%d %H:%M:%S"
        )

    @property
    def available_names(self):
        return self.source_exif.list_all()

    def __init__(self, exif: Image) -> None:
        super().__init__()

        self.source_exif = exif

    @classmethod
    def from_path(cls, path: Path) -> 'NativeExif':
        with path.open("rb") as image_file:
            from exif import Image

            my_image = Image(image_file)

            return NativeExif(my_image)


def parse_exif(path: Path | File) -> Exif | None:
    if path is None:
        return None

    if isinstance(path, File):
        path = path.path

    if path.is_dir():
        return None

    suffix = path.suffix.lower()

    if suffix in [".nef", ".dng", ]:
        return PillowExif.from_path(path)
    elif suffix in [".jpg", ]:
        return NativeExif.from_path(path)

    return None


def exif_sorted(seq: Iterable[File]) -> Iterable[File]:
    class Comparator:
        def __init__(self, o: File) -> None:
            super().__init__()

            self.exif = parse_exif(o.path)
            self.name = o.name

        def __lt__(self, other: 'Comparator') -> bool:
            if other.exif and self.exif:
                return self.exif.date_taken < other.exif.date_taken

            return self.name < other.name

    return sorted(seq, key=Comparator)
