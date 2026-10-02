"""Метод уникальных значений: покрытие сохраняется, длина падает до самого длинного списка."""
from typing import Any

import pytest

from justin.browser.sections.section_settings import AddAllowed
from tests.browser.each_choice import each_choice

BOOLS = [True, False]
THREE = ["a", "b", "c"]


def test_length_is_the_longest_list() -> None:
    assert len(each_choice(BOOLS, THREE, list(AddAllowed))) == 3


def test_every_value_appears() -> None:
    fields: list[list[Any]] = [BOOLS, THREE, list(AddAllowed)]
    rows = each_choice(*fields)

    for position, values in enumerate(fields):
        used = {row[position] for row in rows}

        assert used == set(values), f"поле {position}: не покрыты {set(values) - used}"


def test_single_field() -> None:
    assert each_choice(BOOLS) == [(True,), (False,)]


def test_empty_is_rejected() -> None:
    with pytest.raises(ValueError):
        each_choice(BOOLS, [])
