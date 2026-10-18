from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimelapseSettings:
    """What the user chose for the project: the frame rate and which sounds go on the timeline.

    ``timeline_sounds`` holds sound names (with or without extension); the rest of
    the folder's sounds land in the panel only.
    """

    fps: float = 10.0
    timeline_sounds: list[str] = field(default_factory=list)
