# Backlog — текущий фокус

## Активная разработка: logic2/

**Главный рефакторинг прямо сейчас.** Новая иерархия чеков в `actions/stage/logic2/` параллельно со старой `logic/`. Старая не трогается пока новая не протестирована.

Детали иерархии и принципов — `/patterns`.

---

## Технический долг (из `justin_review_todo.md`)

- [ ] `@property @cache` → `@cached_property` везде в `di/` (утечка памяти — `functools.cache` захватывает `self`)
- [ ] `path.strip("wall")` → `path.removeprefix("wall")` в `GetLikersAction`
- [ ] Spreadsheet ID захардкожен в `app.py` → вынести в конфиг
- [ ] `group_id` и знак в `WebSyncCommand.__handle_tagged` — перепроверить логику кэша
- [ ] `assert False` → `raise NotImplementedError(f"{type(self).__name__} must implement ...")`

---

## Следующие эпики (по приоритету)

1. **Завершить logic2/** — подключить новые чеки, убрать старую `logic/` и ручные фабрики `di/`
2. **DI на lagom** — `di/container.py`, убрать пять фабрик — детали: `/di`
3. **Переезд оставшихся экшенов на Typer** — каждый экшен в отдельной ветке, дропается из master, мержится по мере надобности
   - `refactor/migrate-attach-album-to-typer`
   - `refactor/migrate-check-ratios-to-typer`
   - `refactor/migrate-cms-to-typer`
   - `refactor/migrate-delay-to-typer`
   - `refactor/migrate-delete-posts-to-typer`
   - `refactor/migrate-drone-to-typer`
   - `refactor/migrate-event-to-typer`
   - `refactor/migrate-fix-metafile-to-typer`
   - `refactor/migrate-get-empty-groups-to-typer`
   - `refactor/migrate-get-likers-to-typer`
   - `refactor/migrate-location-to-typer`
   - `refactor/migrate-manage-tags-to-typer`
   - `refactor/migrate-move-to-typer`
   - `refactor/migrate-people-to-typer`
   - `refactor/migrate-populate-to-typer`
   - `refactor/migrate-rearrange-to-typer`
   - `refactor/migrate-split-to-typer`
   - `refactor/migrate-step-sources-to-typer`
4. **Typer output delegates** — каждая команда в отдельной ветке (разбить на задачи перед стартом)
   - `refactor/output-delegates-date-split`
   - `refactor/output-delegates-populate`
   - `refactor/output-delegates-register-people`
   - `refactor/output-delegates-sequence`
   - `refactor/output-delegates-upload`
   - `refactor/output-delegates-web-sync`
   - `refactor/output-delegates-stage` (stage_command)
5. **Тесты** — покрыть logic2/ чеки (сейчас тесты не запускаются в CI)
6. **mypy cleanup** — `refactor/mypy-cleanup` — 278 pre-existing ошибок, подавлены через `[[tool.mypy.overrides]]` в `pyproject.toml`. Чинить пофайлово: убрать модуль из списка → починить ошибки → коммит. Трекинг: xfail-тест `tests/test_mypy_debt.py`.
   Файлы по приоритету (много ошибок → мало):
   `metafile.py` (50), `web_sync_command.py` (24), `photoset_migration.py` (18),
   `upload_command.py` (16), `migrations.py` (14), `google_sheets_database.py` (12),
   `manage_tags_action.py` (9), `filesystem.py` (8), `people_cms.py` (8),
   `stage.py` (7), `sqlite_entries.py` (6), `photoset.py` (5), `structure.py` (4),
   `extracting/structure.py` (4), `populate_command.py` (4), `readwriters.py` (4),
   `photosets_cms.py` (4), `event.py` (4), остальные ≤3
6. **Вынести общую логику в justin_utils** — `refactor/justin-utils-extract`
7. **repokit** — `feat/repokit`
8. **Стабильные релизы на стабильный pyvko** — `feat/pyvko-stable-releases`

---

## Смежные репо в экосистеме

| Проект | Что это |
|--------|---------|
| **pyvko** | VK API wrapper |
| **justin_utils** | Общие утилиты CLI |
| **valifold** | Валидация файловых структур |
| **Cullen** | iOS-приложение для отбора (stage1.filter) |
| **clinject** | DI для Typer (Depends-паттерн) |
