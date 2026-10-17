from dataclasses import dataclass
from pathlib import Path
from typing import Self

from justin.actions.timelapse_sound import Sound, AUDIO_ONLY_EXTENSIONS, VIDEO_AS_AUDIO_EXTENSIONS

JPEG_EXTENSIONS = {".jpg", ".jpeg"}


@dataclass(frozen=True)
class TimelapseSources:
    name: str
    folder: Path

    frames: list[Path]
    cover: Path | None

    sounds: list[Sound]

    @property
    def frames_count(self) -> int:
        return len(self.frames)

    @property
    def first_frame(self) -> Path:
        return self.frames[0]

    @classmethod
    def from_folder(cls, name: str, path: Path) -> Self:
        return cls(
            name=name,
            folder=path,
            frames=cls.get_frames(path),
            cover=cls.get_cover(path),
            sounds=cls.get_sounds(path),
        )

    @classmethod
    def get_frames(cls, path: Path) -> list[Path]:
        frames_dir = path / "frames"

        if not frames_dir.exists():
            raise ValueError(f"No frames in {path}")

        frames = sorted(f for f in frames_dir.iterdir() if f.is_file() and f.suffix.lower() in JPEG_EXTENSIONS)

        if not frames:
            raise ValueError(f"No frames in {path}")

        return frames

    @classmethod
    def get_cover(cls, path: Path) -> Path | None:
        cover_path = path / "cover.jpg"

        if cover_path.exists():
            return cover_path
        else:
            return None

    @classmethod
    def get_sounds(cls, path: Path) -> list[Sound]:
        sounds_dir = path / "sound"

        if not sounds_dir.exists():
            return []

        return [
            Sound.from_path(f)
            for f in sorted(sounds_dir.iterdir())
            if f.is_file() and f.suffix.lower() in AUDIO_ONLY_EXTENSIONS | VIDEO_AS_AUDIO_EXTENSIONS
        ]
