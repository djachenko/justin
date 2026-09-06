"""Паузы между действиями в браузере.

Числа эмпирические: пришли из первой версии визарда и подбирались на глаз,
измерений за ними нет. Каждая пауза берётся из своего генератора, поэтому
одинаковые по смыслу задержки всё равно получаются разной длины — прогон не
выглядит метрономом.
"""
import random
import time
from typing import Iterator

PACE = 1.0  # общий множитель: 0 — без задержек, 1 — норма, 2 — вдвое медленнее

SPREAD = 0.5  # насколько пауза может отклониться от базовой в обе стороны


def durations(base: float, spread: float = SPREAD) -> Iterator[float]:
    while True:
        yield base * random.uniform(1 - spread, 1 + spread)


BETWEEN_FIELDS = durations(0.3)  # соседние поля одной формы
AFTER_ACTION = durations(0.5)  # клик или ввод, на который страница отвечает перерисовкой
PAGE_SETTLE = durations(2.0)  # переход между страницами и шагами визарда


def pause(source: Iterator[float]) -> None:
    if PACE <= 0:
        return

    time.sleep(PACE * next(source))
