"""Page readiness: skeletons gone means the content is there."""
from typing import cast

import pytest
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from justin.browser.shared.page import content_rendered


class FakeSkeleton:
    def __init__(self, displayed: bool = True, stale: bool = False) -> None:
        self.displayed = displayed
        self.stale = stale

    def is_displayed(self) -> bool:
        if self.stale:
            raise StaleElementReferenceException("repainted")

        return self.displayed


class FakeDriver:
    def __init__(self, skeletons: list[FakeSkeleton]) -> None:
        self.skeletons = skeletons

    def find_elements(self, by: str, selector: str) -> list[FakeSkeleton]:
        assert (by, selector) == (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
        return self.skeletons


class TestContentRendered:
    @pytest.mark.parametrize("skeletons,rendered", [
        ([], True),
        ([FakeSkeleton(displayed=False)], True),
        ([FakeSkeleton(displayed=False), FakeSkeleton()], False),
        ([FakeSkeleton(stale=True)], False),
    ], ids=["no_skeletons", "hidden_skeletons", "visible_skeleton", "stale_skeleton_is_not_ready"])
    def test_rendered(self, skeletons: list[FakeSkeleton], rendered: bool) -> None:
        assert content_rendered(cast(WebDriver, FakeDriver(skeletons))) == rendered
