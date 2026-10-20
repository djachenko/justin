"""Section settings against live VK."""
import pytest

from justin.browser.sections.section_settings import (
    AddAllowed,
    FilesSettings,
    MaterialsSettings,
    MusicSettings,
    PhotosSettings,
    PostsPublishing,
    PostsSettings,
    SectionsConfig,
    TopicsSettings,
    VideosSettings,
)
from justin.browser.vk_browser import VKBrowser
from tests.browser.each_choice import each_choice

BOOLS = [True, False]


@pytest.mark.integration
class TestSetSections:
    @pytest.mark.parametrize("enabled,publishing,sharing_disabled",
                             each_choice(BOOLS, list(PostsPublishing), BOOLS))
    def test_posts(self, browser: VKBrowser, event_id: int, enabled: bool, publishing: PostsPublishing, sharing_disabled: bool) -> None:
        browser.set_sections(event_id, SectionsConfig(
            posts=PostsSettings(
                enabled=enabled,
                publishing=publishing,
                sharing_disabled=sharing_disabled,
            )
        ))


    @pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
    def test_photos(self, browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
        browser.set_sections(event_id, SectionsConfig(
            photos=PhotosSettings(
                enabled=enabled,
                add_allowed=add_allowed,
            )
        ))


    @pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
    def test_videos(self, browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
        browser.set_sections(event_id, SectionsConfig(
            videos=VideosSettings(
                enabled=enabled,
                add_allowed=add_allowed,
            )
        ))


    @pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
    def test_topics(self, browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
        browser.set_sections(event_id, SectionsConfig(
            topics=TopicsSettings(
                enabled=enabled,
                add_allowed=add_allowed,
            )
        ))


    @pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
    def test_music(self, browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
        browser.set_sections(event_id, SectionsConfig(
            music=MusicSettings(
                enabled=enabled,
                add_allowed=add_allowed,
            )
        ))


    @pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
    def test_files(self, browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
        browser.set_sections(event_id, SectionsConfig(
            files=FilesSettings(
                enabled=enabled,
                add_allowed=add_allowed,
            )
        ))


    @pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
    def test_materials(self, browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
        browser.set_sections(event_id, SectionsConfig(
            materials=MaterialsSettings(
                enabled=enabled,
                add_allowed=add_allowed,
            )
        ))
