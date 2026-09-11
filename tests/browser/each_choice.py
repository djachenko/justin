"""Метод уникальных значений для параметризации живых тестов."""
from itertools import cycle
from typing import Any


def each_choice(*options: list[Any]) -> list[tuple]:
    """Набор, в котором каждое значение каждого поля встречается хотя бы раз.

    Декартово произведение проверяет комбинации, а браузерным тестам нужны значения:
    каждое из них — отдельный селектор на странице. Длина набора равна длине самого
    длинного списка, короткие добираются по кругу. 2 × 3 × 2 = 12 сжимается в 3.

    Порядок значений в кортеже — порядок аргументов; он же должен стоять в argnames.
    """
    if not options or any(not values for values in options):
        raise ValueError("each_choice needs a non-empty list per field")

    length = max(len(values) for values in options)
    wheels = [cycle(values) for values in options]

    return [tuple(next(wheel) for wheel in wheels) for _ in range(length)]
