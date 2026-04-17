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
3. **Переезд оставшихся команд на Typer** — всё из `actions/` перенести в `typer/`
4. **Тесты** — покрыть logic2/ чеки (сейчас тесты не запускаются в CI)

---

## Смежные репо в экосистеме

| Проект | Что это |
|--------|---------|
| **pyvko** | VK API wrapper |
| **justin_utils** | Общие утилиты CLI |
| **valifold** | Валидация файловых структур |
| **Cullen** | iOS-приложение для отбора (stage1.filter) |
| **clinject** | DI для Typer (Depends-паттерн) |
