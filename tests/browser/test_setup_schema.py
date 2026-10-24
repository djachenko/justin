import pytest

from justin.browser.event_setup.event_setup_schema import (
    _clear_and_type, _classes_of, _has_label, _is_day, _is_number, _value_of,
)

pytestmark = pytest.mark.usefixtures("no_pauses")


class FakeField:
    def __init__(self, attributes: dict[str, str | None]) -> None:
        self.attributes = attributes
        self.keys: list[str] = []
        self.cleared = 0

    def get_attribute(self, name: str) -> str | None:
        return self.attributes.get(name)

    def send_keys(self, value: str) -> None:
        self.keys.append(value)

    def clear(self) -> None:
        self.cleared += 1


class FakeCell(FakeField):
    def __init__(self, text: str, classes: str = "day", displayed: bool = True) -> None:
        super().__init__({"class": classes})

        self.text = text
        self.displayed = displayed

    def is_displayed(self) -> bool:
        return self.displayed


class TestValueOf:
    def test_value_is_read(self) -> None:
        assert _value_of(FakeField({"value": "Moscow"})) == "Moscow"

    def test_missing_value_names_the_field(self) -> None:
        field = FakeField({"id": "group_start_date_date_input"})

        with pytest.raises(ValueError, match="group_start_date_date_input"):
            _value_of(field)


class TestClassesOf:
    def test_missing_class_reads_as_empty(self) -> None:
        assert _classes_of(FakeField({})) == ""

    def test_classes_are_read(self) -> None:
        assert _classes_of(FakeField({"class": "day prev_month_day"})) == "day prev_month_day"


class TestClearAndType:
    def test_field_is_cleared_before_typing(self) -> None:
        field = FakeField({})

        _clear_and_type(field, "ab")

        assert field.cleared == 1
        assert field.keys == ["a", "b"]


class TestIsDay:
    def test_day_of_the_shown_month_matches(self) -> None:
        assert _is_day(FakeCell(" 15 "), 15)

    @pytest.mark.parametrize("cell", [
        FakeCell("15", classes="day prev_month_day"),
        FakeCell("15", classes="day next_month_day"),
        FakeCell("16"),
    ], ids=["previous_month", "next_month", "another_day"])
    def test_other_cells_do_not_match(self, cell: FakeCell) -> None:
        assert not _is_day(cell, 15)


class TestIsNumber:
    def test_number_matches_by_value(self) -> None:
        assert _is_number(FakeCell(" 7 "), 7)

    @pytest.mark.parametrize("cell", [
        FakeCell("7", displayed=False),
        FakeCell("Hour"),
    ], ids=["hidden", "non_digit"])
    def test_other_cells_do_not_match(self, cell: FakeCell) -> None:
        assert not _is_number(cell, 7)


class TestHasLabel:
    def test_label_matches_trimmed(self) -> None:
        assert _has_label(FakeCell(" Москва "), "Москва")

    @pytest.mark.parametrize("cell", [
        FakeCell("Москва", displayed=False),
        FakeCell("Казань"),
    ], ids=["hidden", "another_label"])
    def test_other_cells_do_not_match(self, cell: FakeCell) -> None:
        assert not _has_label(cell, "Москва")
