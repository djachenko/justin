from dataclasses import fields

import pytest

from justin.browser.sections.section_schema import (
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
from justin.browser.sections.section_settings import (
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

ELEMENTS: list[tuple[SectionSchema, str]] = [
    (schema, f.name)
    for schema, _ in PAIRS
    for f in fields(schema)
    if f.name not in ("test_id", "_SECTION_PAUSE")
]


class TestSectionSchemas:
    @pytest.mark.parametrize("schema,settings_cls", PAIRS, ids=[type(s).__name__ for s, _ in PAIRS])
    def test_covers_all_settings_fields(self, schema: SectionSchema, settings_cls: type) -> None:
        settings_fields = {f.name for f in fields(settings_cls) if f.name != "enabled"}

        schema_attrs = {
            f.name for f in fields(schema)
            if f.name not in ("test_id", "enabled", "_SECTION_PAUSE")
        }

        assert schema_attrs == settings_fields

    @pytest.mark.parametrize("schema,settings_cls", PAIRS, ids=[type(s).__name__ for s, _ in PAIRS])
    def test_enabled_is_toggle_with_testid(self, schema: SectionSchema, settings_cls: type) -> None:
        assert isinstance(schema.enabled, Toggle)
        assert schema.enabled.test_id

    @pytest.mark.parametrize("schema,name", ELEMENTS,
                             ids=[f"{type(s).__name__}.{name}" for s, name in ELEMENTS])
    def test_element_types(self, schema: SectionSchema, name: str) -> None:
        assert isinstance(getattr(schema, name), (Toggle, Radio, Dropdown))
