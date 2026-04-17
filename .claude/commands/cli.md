# CLI (Typer)

## Точка входа

```
justin/typer/app/console_runner.py  →  run()
```

Запуск: `justin <command> [pattern]`  
Установка: `pip install -e ".[dev]"`

## Команды

| Команда | Что делает | Переход |
|---|---|---|
| `filter` | Начальный отбор | → stage1.filter |
| `develop` | Обработка в Lightroom | stage1 → stage2.develop |
| `ourate` | Поиск необработанных | stage1 → stage2.ourate |
| `ready` | Готово к публикации | stage2 → stage3.ready |
| `schedule` | Запланировать пост VK | stage3.ready → stage3.schedule |
| `publish` | Пометить опубликованным | stage3.schedule → stage4.published |
| `gif` | Извлечь GIF-кадры | |
| `archive` | Архивировать фотосет | |
| `date-split` | Разбить сет по датам | |
| `sequence` | Последовательная обработка | |
| `upload` | Загрузить в VK | |
| `register-people` | Зарегистрировать людей в БД | |
| `web-sync` | Синхронизировать с вебом | |

## Структура Typer-команды

```python
# typer/base_commands/pattern_command.py
class PatternCommand(ABC):
    def __init__(self, context: Context): ...

    @abstractmethod
    def perform(self, photoset: Photoset) -> None: ...

    def run(self, pattern: str) -> None:
        photosets = self._context.world.find(pattern)
        for photoset in photosets:
            self.perform(photoset)
```

Каждая команда — отдельный файл в `typer/`. Регистрируется в `typer/app/app.py` через `app.command()`.

## Сборка приложения

`typer/app/app.py` — `build_app(home: Path) -> typer.Typer`:
1. Загружает конфиг из `~/justin_config.py` через `importlib.util`
2. Создаёт `Context` с `pyvko`, `world`, конфигом
3. Регистрирует команды через callback (передаёт `ctx.obj = context`)

## Context

`shared/context.py` — синглтон сессии:

```python
@dataclass(frozen=True)
class Context:
    pyvko: Pyvko
    world: World
    config: Config
```

Доступен во всех командах через `typer.Context.obj`.

## Паттерн Pattern

`pattern` — glob или имя фотосета, фильтрует по `World.find(pattern)`. Большинство команд принимают опциональный `pattern: str = ""`.
