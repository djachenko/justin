"""Pauses between browser actions.

The numbers are empirical — picked by eye in the first version of the wizard, with no
measurements behind them. Every pause deviates by a share of itself, so pauses that mean
the same thing still come out different: the run does not tick like a metronome.
"""
import random
import time

PACE = 1.0  # overall multiplier: 0 — no delays, 1 — normal, 2 — twice as slow

SPREAD = 0.5  # share of the value a pause may deviate by, both ways

BETWEEN_FIELDS = 0.3  # neighbouring fields of one form
AFTER_SCROLL = 0.3  # scrolled to an element, the page has to arrive
AFTER_ACTION = 0.5  # a click or input the page answers with a repaint
BETWEEN_KEYS = 0.08  # neighbouring characters while typing
PAGE_SETTLE = 2.0  # moving between pages and wizard steps


def varied(seconds: float) -> float:
    """seconds give or take a share of itself: 0.4 with SPREAD=0.5 gives 0.2…0.6.

    The deviation is a share of the value rather than a fixed amount: a short pause does
    not need a wide spread, and for a long one a fixed spread would be too narrow.
    """
    return seconds * random.uniform(1 - SPREAD, 1 + SPREAD)


def pause(seconds: float) -> None:
    if PACE <= 0:
        return

    time.sleep(PACE * varied(seconds))
