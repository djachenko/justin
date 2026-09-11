"""
Integration tests — требуют живой браузер с активной сессией VK.
Запуск: pytest -m integration tests/browser/test_set_sections_integration.py
"""
import pytest

from justin.browser.sections.section_settings import (
    AddAllowed,
    ContentType,
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
@pytest.mark.parametrize("enabled,publishing,sharing_disabled",
                         each_choice(BOOLS, list(PostsPublishing), BOOLS))
def test_posts(browser: VKBrowser, event_id: int, enabled: bool, publishing: PostsPublishing, sharing_disabled: bool) -> None:
    browser.set_sections(event_id, SectionsConfig(
        posts=PostsSettings(enabled=enabled, publishing=publishing, sharing_disabled=sharing_disabled)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled,content_type,add_allowed",
                         each_choice(BOOLS, list(ContentType), list(AddAllowed)))
def test_photos(browser: VKBrowser, event_id: int, enabled: bool, content_type: ContentType, add_allowed: AddAllowed) -> None:
    browser.set_sections(event_id, SectionsConfig(
        photos=PhotosSettings(enabled=enabled, content_type=content_type, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled,content_type,add_allowed",
                         each_choice(BOOLS, list(ContentType), list(AddAllowed)))
def test_videos(browser: VKBrowser, event_id: int, enabled: bool, content_type: ContentType, add_allowed: AddAllowed) -> None:
    browser.set_sections(event_id, SectionsConfig(
        videos=VideosSettings(enabled=enabled, content_type=content_type, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
def test_topics(browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
    browser.set_sections(event_id, SectionsConfig(
        topics=TopicsSettings(enabled=enabled, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled,content_type,add_allowed",
                         each_choice(BOOLS, list(ContentType), list(AddAllowed)))
def test_music(browser: VKBrowser, event_id: int, enabled: bool, content_type: ContentType, add_allowed: AddAllowed) -> None:
    browser.set_sections(event_id, SectionsConfig(
        music=MusicSettings(enabled=enabled, content_type=content_type, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
def test_files(browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
    browser.set_sections(event_id, SectionsConfig(
        files=FilesSettings(enabled=enabled, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled,add_allowed", each_choice(BOOLS, list(AddAllowed)))
def test_materials(browser: VKBrowser, event_id: int, enabled: bool, add_allowed: AddAllowed) -> None:
    browser.set_sections(event_id, SectionsConfig(
        materials=MaterialsSettings(enabled=enabled, add_allowed=add_allowed)
    ))
