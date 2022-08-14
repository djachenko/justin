from abc import abstractmethod
from datetime import datetime
from functools import lru_cache
from pathlib import Path


class Exif:
    @property
    @abstractmethod
    def date_taken(self) -> datetime:
        pass

    @property
    @abstractmethod
    def available_names(self):
        pass


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


def parse_exif(path: Path) -> Exif | None:
    suffix = path.suffix.lower()

    if suffix in [".nef", ".dng", ]:
        return PillowExif.from_path(path)
    elif suffix in [".jpg", ]:
        return NativeExif.from_path(path)

    return None
