"""Premiere Pro's time unit: ticks.

Premiere measures all time in "ticks" — a fixed, very fine subdivision of a
second (chosen so common frame rates divide evenly). One second is
``PREMIERE_TIMEBASE`` ticks. Everything time-shaped in a ``.prproj`` — clip
lengths, frame durations, in/out points — is stored in ticks, so every
seconds/fps → ticks conversion goes through here.
"""

PREMIERE_TIMEBASE = 254_016_000_000  # ticks per second


def seconds_to_ticks(seconds: float) -> int:
    """``seconds`` in Premiere ticks, truncated to a whole tick."""
    return int(seconds * PREMIERE_TIMEBASE)


def ticks_per_frame(fps: float) -> int:
    """How many ticks one frame lasts at ``fps``, truncated to a whole tick.

    Premiere stores frame rates this way (``<FrameRate>``), not as frames per second.
    """
    return int(PREMIERE_TIMEBASE / fps)
