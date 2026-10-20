import pytest

from justin.browser.invite_link.invite_link_settings import LinkLifetime
from justin.browser.sections.section_settings import (
    PhotosSettings, PostsSettings, SectionSettings, SectionsConfig, ServicesSettings, TopicsSettings,
)


class TestDefaults:
    @pytest.mark.parametrize("settings_cls", [PostsSettings, PhotosSettings, TopicsSettings])
    def test_sections_are_enabled_by_default(self, settings_cls: type[SectionSettings]) -> None:
        assert settings_cls().enabled

    def test_sections_that_default_to_off(self) -> None:
        assert not ServicesSettings().enabled

    @pytest.mark.parametrize("section", ["posts", "main_section"])
    def test_untouched_sections_are_none(self, section: str) -> None:
        assert getattr(SectionsConfig(), section) is None


class TestLinkLifetime:
    @pytest.mark.parametrize("lifetime,seconds", [
        (LinkLifetime.HALF_HOUR, 1800),
        (LinkLifetime.HOUR, 3600),
        (LinkLifetime.SIX_HOURS, 21600),
        (LinkLifetime.TWELVE_HOURS, 43200),
        (LinkLifetime.DAY, 86400),
        (LinkLifetime.INDEFINITE, 0),
    ])
    def test_values_are_seconds(self, lifetime: LinkLifetime, seconds: int) -> None:
        assert lifetime.value == str(seconds)
