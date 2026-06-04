from dataclasses import fields

import pytest

from justin.browser.section_schema import (
    Dropdown,
    FilesSchema,
    MaterialsSchema,
    MusicSchema,
    PhotosSchema,
    PostsSchema,
    Radio,
    SectionSchema,
    Toggle,
    TopicsSchema,
    VideosSchema,
)
from justin.browser.section_settings import (
    FilesSettings,
    MaterialsSettings,
    MusicSettings,
    PhotosSettings,
    PostsSettings,
    TopicsSettings,
    VideosSettings,
)

PAIRS: list[tuple[SectionSchema, type]] = [
    (PostsSchema("wall"),        PostsSettings),
    (PhotosSchema("photos"),     PhotosSettings),
    (VideosSchema("videos"),     VideosSettings),
    (TopicsSchema("discussions"), TopicsSettings),
    (MusicSchema("audios"),      MusicSettings),
    (FilesSchema("files"),       FilesSettings),
    (MaterialsSchema("wiki"),    MaterialsSettings),
]


@pytest.mark.parametrize("schema,settings_cls", PAIRS, ids=[type(s).__name__ for s, _ in PAIRS])
def test_schema_covers_all_settings_fields(schema: SectionSchema, settings_cls: type) -> None:
    settings_fields = {f.name for f in fields(settings_cls) if f.name != "enabled"}

    schema_attrs = {
        f.name for f in fields(schema)
        if f.name not in ("test_id", "enabled", "_SECTION_PAUSE")
    }

    assert schema_attrs == settings_fields


@pytest.mark.parametrize("schema,settings_cls", PAIRS, ids=[type(s).__name__ for s, _ in PAIRS])
def test_schema_enabled_is_toggle_with_testid(schema: SectionSchema, settings_cls: type) -> None:
    assert isinstance(schema.enabled, Toggle)
    assert schema.enabled.test_id


@pytest.mark.parametrize("schema,settings_cls", PAIRS, ids=[type(s).__name__ for s, _ in PAIRS])
def test_schema_element_types(schema: SectionSchema, settings_cls: type) -> None:
    for f in fields(schema):
        if f.name in ("test_id", "_SECTION_PAUSE"):
            continue
        el = getattr(schema, f.name)
        assert isinstance(el, (Toggle, Radio, Dropdown)), (
            f"{type(schema).__name__}.{f.name} is {type(el).__name__}, expected Toggle/Radio/Dropdown"
        )
