from dataclasses import dataclass
from pathlib import Path
from typing import Self

from justin.actions.timelapse_sound import Sound, AUDIO_ONLY_EXTENSIONS, VIDEO_AS_AUDIO_EXTENSIONS

JPEG_EXTENSIONS = {
    ".jpg",
    ".jpeg",
}


@dataclass(frozen=True)
class TimelapseSources:
    """What a timelapse folder holds: the frames, the optional cover and the sounds."""

    name: str
    folder: Path

    frames: list[Path]
    cover: Path | None

    sounds: list[Sound]

    @property
    def frames_count(self) -> int:
        """How many frames the image sequence has."""
        return len(self.frames)

    @property
    def first_frame(self) -> Path:
        """The sequence's first frame — Premiere locates an image sequence by its first file."""
        return self.frames[0]

    @classmethod
    def from_folder(cls, name: str, path: Path) -> Self:
        """Collect the sources from a timelapse folder.

        The layout is ``frames/`` (required), ``cover.jpg`` and ``sound/`` (both
        optional). ``name`` names the project and its sequence.
        """
        return cls(
            name=name,
            folder=path,
            frames=cls.get_frames(path),
            cover=cls.get_cover(path),
            sounds=cls.get_sounds(path),
        )

    @classmethod
    def get_frames(cls, path: Path) -> list[Path]:
        """The JPEGs in ``frames/``, sorted by name — that order is the sequence order.

        Raises ``ValueError`` if the folder is missing or holds no JPEGs: a
        timelapse without frames has nothing to build.
        """
        frames_dir = path / "frames"

        if not frames_dir.exists():
            raise ValueError(f"No frames in {path}")

        frames = sorted(f for f in frames_dir.iterdir() if f.is_file() and f.suffix.lower() in JPEG_EXTENSIONS)

        if not frames:
            raise ValueError(f"No frames in {path}")

        return frames

    @classmethod
    def get_cover(cls, path: Path) -> Path | None:
        """``cover.jpg`` in the folder, or ``None`` — the project then has no cover frame."""
        cover_path = path / "cover.jpg"

        if cover_path.exists():
            return cover_path
        else:
            return None

    @classmethod
    def get_sounds(cls, path: Path) -> list[Sound]:
        """The supported sound files in ``sound/``, sorted by name; ``[]`` without the folder.

        Files of other formats are skipped rather than rejected, so stray files in
        the folder don't stop the build.
        """
        sounds_dir = path / "sound"

        if not sounds_dir.exists():
            return []

        return [
            Sound.from_path(f)
            for f in sorted(sounds_dir.iterdir())
            if f.is_file() and f.suffix.lower() in AUDIO_ONLY_EXTENSIONS | VIDEO_AS_AUDIO_EXTENSIONS
        ]
