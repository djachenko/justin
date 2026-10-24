from selenium.webdriver.common.by import By

from justin.browser.shared import pacing
from justin.browser.shared.elements import by_css, by_testid, by_xpath, found, type_into


class FakeWait:
    def until(self, condition):
        return condition(None)


class TestLocators:
    def test_by_css(self) -> None:
        assert by_css("a.b") == (By.CSS_SELECTOR, "a.b")

    def test_by_testid(self) -> None:
        assert by_testid("save") == (By.CSS_SELECTOR, "[data-testid='save']")

    def test_by_xpath(self) -> None:
        assert by_xpath("//a") == (By.XPATH, "//a")


class TestFound:
    def test_returns_what_finder_found(self) -> None:
        assert found(FakeWait(), lambda _: "link") == "link"

    def test_nothing_found_reads_as_not_yet(self) -> None:
        assert found(FakeWait(), lambda _: None) is False


class FakeInput:
    def __init__(self) -> None:
        self.keys: list[str] = []

    def send_keys(self, value: str) -> None:
        self.keys.append(value)


class TestTypeInto:
    def test_types_character_by_character(self, monkeypatch) -> None:
        paused: list[float] = []
        monkeypatch.setattr(pacing.time, "sleep", paused.append)

        el = FakeInput()

        type_into(el, "abc")

        assert el.keys == ["a", "b", "c"]
        assert len(paused) == 3

    def test_empty_text_types_nothing(self, monkeypatch) -> None:
        monkeypatch.setattr(pacing.time, "sleep", lambda _: None)

        el = FakeInput()

        type_into(el, "")

        assert el.keys == []
