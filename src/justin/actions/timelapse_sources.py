from dataclasses import dataclass
from pathlib import Path
from typing import Self

JPEG_EXTENSIONS = {".jpg", ".jpeg"}
AUDIO_EXTENSIONS = {".mp3", ".mp4", ".wav", ".aac", ".m4a", ".flac", ".ogg"}


@dataclass(frozen=True)
class TimelapseSources:
    name: str
    folder: Path

    frames: list[Path]
    cover: Path | None

    sounds: list[Path] | None

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

        frames = []

        for frame in frames_dir.iterdir():
            if not frame.is_file():
                continue
                # raise

            if frame.suffix not in JPEG_EXTENSIONS:
                continue

            frames.append(frame)

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
    def get_sounds(cls, path: Path) -> list[Path] | None:
        sounds_dir = path / "sounds"

        if not sounds_dir.exists():
            return None

        sounds = []

        for sound in sounds_dir.iterdir():
            if not sound.is_file():
                continue
                # raise

            if sound.suffix.lower() not in AUDIO_EXTENSIONS:
                continue

            sounds.append(sound)

        if not sounds:
            return None

        return sounds
