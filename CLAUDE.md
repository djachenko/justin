# justin — CLAUDE.md

Контекстный файл для Claude Code. Читай его перед любой работой с проектом.

---

## Что это

CLI-инструмент для автоматизации фотоворкфлоу: от карты памяти до публикации в VK.
Личный проект, используется в продакшене каждый день.

**Точка входа:** `src/justin/typer/app/console_runner.py`  
**Установка:** `pip install -e ".[dev]"`  
**Запуск:** `justin <command> [pattern]`

---

## Стек

- **Python 3.12+**, Typer (переезд с argparse в процессе), SQLite
- **Selenium** — автоматизация настроек VK там, где их нет в API
- **pyvko** — самописная обёртка над VK API (`pip install -e ../pyvko`)
- **justin_utils** — общие утилиты экосистемы (`pip install -e ../justin_utils`)
- **valifold** — валидация файловых структур (PyPI: `pip install valifold`)

---

## Структура проекта

```
src/justin/
├── actions/                  # Старые Action-классы (argparse-era, в процессе замены)
│   └── stage/
│       └── logic/            # СТАРАЯ иерархия: Selector → Extractor → Check
│       └── logic2/           # НОВАЯ иерархия (активная разработка — см. /patterns)
├── browser/                  # Настройки VK через Selenium — то, чего нет в API
│   ├── vk_browser.py         # VKBrowser — фасад: create_event, apply_settings, invite link
│   ├── event_creation/       # Визард создания события (iframe, три шага)
│   ├── event_setup/          # Страница ?act=edit: название, даты, категория, доступ
│   ├── event_settings/       # Верхняя схема: секции, сообщения, CTA, адреса, extras
│   ├── sections/             # Секции события и главный блок
│   ├── invite_link/          # Инвайт-ссылки
│   ├── explorers/            # Разведка разметки (дампы страниц)
│   └── shared/               # elements (сахар над локаторами), page, save_button,
│                             # custom_select, react_select, captcha, pacing, waiting, run_mode
├── cms/                      # JSON-based CMS (устарел, не трогать)
├── cms_2/                    # SQLite-based CMS (текущий) — см. /cms
│   └── storage/sqlite/
│   └── sub_cms/
├── di/                       # СТАРЫЙ DI: фабричные классы (в процессе замены) — см. /di
├── shared/
│   ├── config.py             # Загрузка конфига через importlib.util
│   ├── context.py            # Context — передаётся в команды через typer.Context.obj
│   ├── metafiles/            # Метафайлы (_meta.json) — см. /metafiles
│   ├── models/photoset.py    # Photoset — центральная модель
│   └── structure.py          # Structure, StructureVisitor (будет заменён valifold)
├── typer/                    # Typer-команды (новый слой) — см. /cli
│   ├── app/app.py            # Сборка Typer-приложения
│   └── base_commands/        # PatternCommand, DestinationsAwareCommand
└── postmypost/               # Telegram crossposting (pyrogram/MTProto)
```

Работа с файлами — `justin_utils.filesystem` (`Folder`, `File`), не в этом репозитории.

Пакеты в `browser/` сгруппированы по фичам: схема и настройки одной страницы лежат
рядом, потому что VK переверстывает страницы поодиночке и правится всегда пара.
Под отладчиком (`run_mode.is_debug`) браузер виден и дампит страницу при таймауте;
в обычном запуске — headless и без дампов. Живые тесты требуют браузера с сессией VK
и отобраны маркерами — см. `addopts` в `pyproject.toml`.

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

**`Folder`** (`justin_utils.filesystem`) — обёртка над Path с удобным доступом к подпапкам (`folder["justin"]`).

**`Context`** (`shared/context.py`) — синглтон сессии. Содержит `pyvko`, `world`, конфиг. Передаётся в команды через `typer.Context.obj`.
