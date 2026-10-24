"""Each-choice: coverage is kept, length drops to the longest list."""
from typing import Any

import pytest

from justin.browser.sections.section_settings import AddAllowed
from tests.browser.each_choice import each_choice

BOOLS = [True, False]
THREE = ["a", "b", "c"]
FIELDS: list[list[Any]] = [BOOLS, THREE, list(AddAllowed)]


class TestEachChoice:
    def test_length_is_the_longest_list(self) -> None:
        assert len(each_choice(*FIELDS)) == 3

    @pytest.mark.parametrize("position", range(len(FIELDS)))
    def test_every_value_appears(self, position: int) -> None:
        used = {row[position] for row in each_choice(*FIELDS)}

        assert used == set(FIELDS[position])

    def test_single_field(self) -> None:
        assert each_choice(BOOLS) == [(True,), (False,)]

    def test_empty_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            each_choice(BOOLS, [])
