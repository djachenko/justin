"""Паузы между действиями в браузере."""
import random
import time

PACE = 1.0  # global pause multiplier: 0 = no delays, 1 = normal, 2 = slow


def pause(seconds: float = 1.0, jitter: float = 0.5) -> None:
    """Randomised so a run is not metronomic, and scalable in one place when VK throttles."""
    if PACE <= 0:
        return

    time.sleep(PACE * seconds * random.uniform(1 - jitter, 1 + jitter))
