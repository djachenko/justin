"""Метод уникальных значений: покрытие сохраняется, длина падает до самого длинного списка."""
import pytest

from justin.browser.sections.section_settings import AddAllowed, ContentType
from tests.browser.each_choice import each_choice

BOOLS = [True, False]


def test_length_is_the_longest_list() -> None:
    assert len(each_choice(BOOLS, list(ContentType), list(AddAllowed))) == 3


def test_every_value_appears() -> None:
    fields = [BOOLS, list(ContentType), list(AddAllowed)]
    rows = each_choice(*fields)

    for position, values in enumerate(fields):
        used = {row[position] for row in rows}

        assert used == set(values), f"поле {position}: не покрыты {set(values) - used}"


def test_single_field() -> None:
    assert each_choice(BOOLS) == [(True,), (False,)]


def test_empty_is_rejected() -> None:
    with pytest.raises(ValueError):
        each_choice(BOOLS, [])
