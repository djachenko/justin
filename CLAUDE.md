# justin — CLAUDE.md

Контекстный файл для Claude Code. Читай его перед любой работой с проектом.

---

## Что это

CLI-инструмент для автоматизации фотоворкфлоу: от карты памяти до публикации в VK.
Личный проект, используется в продакшене каждый день.

**Точка входа:** `justin/typer/app/console_runner.py`  
**Установка:** `pip install -e ".[dev]"`  
**Запуск:** `justin <command> [pattern]`

---

## Стек

- **Python 3.10+**, Typer (переезд с argparse в процессе), SQLite
- **pyvko** — самописная обёртка над VK API (`pip install -e ../pyvko`)
- **justin_utils** — общие утилиты экосистемы (`pip install -e ../justin_utils`)
- **valifold** — валидация файловых структур (PyPI: `pip install valifold`)

---

## Структура проекта

```
justin/
├── actions/                  # Старые Action-классы (argparse-era, в процессе замены)
│   └── stage/
│       └── logic/            # СТАРАЯ иерархия: Selector → Extractor → Check
│       └── logic2/           # НОВАЯ иерархия (активная разработка — см. /patterns)
├── cms/                      # JSON-based CMS (устарел, не трогать)
├── cms_2/                    # SQLite-based CMS (текущий) — см. /cms
│   └── storage/sqlite/
│   └── sub_cms/
├── di/                       # СТАРЫЙ DI: фабричные классы (в процессе замены) — см. /di
├── shared/
│   ├── config.py             # Загрузка конфига через importlib.util
│   ├── context.py            # Context — передаётся в команды через typer.Context.obj
│   ├── filesystem.py         # Folder, File, RelativeFileset, PathBased
│   ├── metafiles/            # Метафайлы (_meta.json) — см. /metafiles
│   ├── models/photoset.py    # Photoset — центральная модель
│   └── structure.py          # Structure, StructureVisitor (будет заменён valifold)
├── typer/                    # Typer-команды (новый слой) — см. /cli
│   ├── app/app.py            # Сборка Typer-приложения
│   └── base_commands/        # PatternCommand, DestinationsAwareCommand
└── postmypost/               # Telegram crossposting (pyrogram/MTProto)
```

---

## Стейдж-пайплайн

Фотосеты именуются `YY.M.D.event_name_in_snake_case` и живут в `stages/`:

```
stage1.filter/    ← импортировано с карты, нужен отбор (Cullen)
stage2.develop/   ← отобрано, обрабатывается в Lightroom
stage2.ourate/    ← поиск необработанных для личной рассылки
stage3.ready/     ← обработано, готово к публикации
stage3.schedule/  ← загружено, запланировано
stage4.published/ ← опубликовано
```

Переход между стейджами — через команды. Каждый переход проходит чеки. Если чек не пройден — переход блокируется.

---

## Ключевые модели

**`Photoset`** (`shared/models/photoset.py`) — центральная модель. Свойства: `sources` (RAW), `results` (JPEG), `not_signed` (отбор), `justin`, `closed`, `meeting`, `my_people`, `parts`.

**`Folder`** (`shared/filesystem.py`) — обёртка над Path с удобным доступом к подпапкам (`folder["justin"]`).

**`Context`** (`shared/context.py`) — синглтон сессии. Содержит `pyvko`, `world`, конфиг. Передаётся в команды через `typer.Context.obj`.

---

## Скиллы (детальные гайды)

### Архитектура
- `/patterns` — StageCheck/Hook/Stage иерархия, Problem, StageCheckError, добавление нового чека
- `/di` — DI: текущие фабрики, план на lagom, принципы
- `/cms` — CMS_2: SQLite/Google Sheets бэкенды, Sub-CMS паттерн
- `/metafiles` — _meta.json: типы, накопление контекста, миграции

### Стиль & Качество
- `/style` — Naming conventions, code style, принципы, чего не делать

### Фичи & Инфраструктура
- `/cli` — Typer команды, структура команды, Context, Pattern
- `/backlog` — текущий фокус, технический долг, следующие эпики
- `/git` — GitHub Flow, semantic commits, worktrees, автор
