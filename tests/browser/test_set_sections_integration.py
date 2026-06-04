"""
Integration tests — требуют живой браузер с активной сессией VK.
Запуск: VK_TEST_EVENT_ID=<id> pytest -m integration
"""
import os

import pytest

from justin.browser.section_settings import (
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

TEST_EVENT_ID = int(os.environ["VK_TEST_EVENT_ID"])


@pytest.fixture(scope="module")
def browser():
    with VKBrowser() as b:
        yield b


BOOLS = [True, False]


@pytest.mark.integration
@pytest.mark.parametrize("enabled", BOOLS)
@pytest.mark.parametrize("publishing", list(PostsPublishing))
@pytest.mark.parametrize("sharing_disabled", BOOLS)
def test_posts(browser: VKBrowser, enabled: bool, publishing: PostsPublishing, sharing_disabled: bool) -> None:
    browser.set_sections(TEST_EVENT_ID, SectionsConfig(
        posts=PostsSettings(enabled=enabled, publishing=publishing, sharing_disabled=sharing_disabled)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled", BOOLS)
@pytest.mark.parametrize("content_type", list(ContentType))
@pytest.mark.parametrize("add_allowed", list(AddAllowed))
def test_photos(browser: VKBrowser, enabled: bool, content_type: ContentType, add_allowed: AddAllowed) -> None:
    browser.set_sections(TEST_EVENT_ID, SectionsConfig(
        photos=PhotosSettings(enabled=enabled, content_type=content_type, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled", BOOLS)
@pytest.mark.parametrize("content_type", list(ContentType))
@pytest.mark.parametrize("add_allowed", list(AddAllowed))
def test_videos(browser: VKBrowser, enabled: bool, content_type: ContentType, add_allowed: AddAllowed) -> None:
    browser.set_sections(TEST_EVENT_ID, SectionsConfig(
        videos=VideosSettings(enabled=enabled, content_type=content_type, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled", BOOLS)
@pytest.mark.parametrize("add_allowed", list(AddAllowed))
def test_topics(browser: VKBrowser, enabled: bool, add_allowed: AddAllowed) -> None:
    browser.set_sections(TEST_EVENT_ID, SectionsConfig(
        topics=TopicsSettings(enabled=enabled, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled", BOOLS)
@pytest.mark.parametrize("content_type", list(ContentType))
@pytest.mark.parametrize("add_allowed", list(AddAllowed))
def test_music(browser: VKBrowser, enabled: bool, content_type: ContentType, add_allowed: AddAllowed) -> None:
    browser.set_sections(TEST_EVENT_ID, SectionsConfig(
        music=MusicSettings(enabled=enabled, content_type=content_type, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled", BOOLS)
@pytest.mark.parametrize("add_allowed", list(AddAllowed))
def test_files(browser: VKBrowser, enabled: bool, add_allowed: AddAllowed) -> None:
    browser.set_sections(TEST_EVENT_ID, SectionsConfig(
        files=FilesSettings(enabled=enabled, add_allowed=add_allowed)
    ))


@pytest.mark.integration
@pytest.mark.parametrize("enabled", BOOLS)
@pytest.mark.parametrize("add_allowed", list(AddAllowed))
def test_materials(browser: VKBrowser, enabled: bool, add_allowed: AddAllowed) -> None:
    browser.set_sections(TEST_EVENT_ID, SectionsConfig(
        materials=MaterialsSettings(enabled=enabled, add_allowed=add_allowed)
    ))
