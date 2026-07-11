from dataclasses import dataclass


@dataclass(frozen=True)
class TimelapseSettings2:
    fps: float = 10.0
