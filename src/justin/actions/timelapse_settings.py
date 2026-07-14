from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimelapseSettings:
    fps: float = 10.0
    timeline_sounds: list[str] = field(default_factory=list)
