# Dependency Injection

## Текущее состояние (старое, `di/`)

Ручные фабричные классы:

```
DI → ActionFactory / ChecksFactory / ExtractorFactory / SelectorFactory / StagesFactory
```

Синглтоны через `@property @cache` — **известный баг**: `functools.cache` на инстанс-методах захватывает `self` → утечка памяти. Нужно заменять на `functools.cached_property`.

Файлы: `di/app.py`, `di/actions.py`, `di/checks.py`, `di/commands.py`, `di/extractors.py`, `di/selectors.py`, `di/stages.py`.

**Старые фабрики не трогать** без понимания всей цепочки зависимостей.

---

## План (новое, `di/container.py`)

Фреймворк — **lagom** (autowiring по typehint). Один `container.py` вместо пяти фабрик.

```python
from lagom import Container, Singleton

container = Container()
container[MetadataCheck] = Singleton(MetadataCheck)
container[UnselectedCheck] = lambda: UnselectedCheck(prechecks=[container[MetadataCheck]])
# StagesFactory и выше — autowiring автоматически
```

**Исключение**: для `List[StageCheck]` (prechecks) autowiring не работает — связи прописываются вручную.

---

## Принципы

- **Никаких сайд-эффектов в `__init__`** — только сохранение зависимостей в `self`.
- **Время жизни и связи** — только в `container.py`, не внутри классов.
- **Инверсия зависимостей** — класс не знает о своём окружении.

---

## Context (не DI, но похоже)

`Context` (`shared/context.py`) — синглтон сессии, передаётся через `typer.Context.obj`:

```python
@app.callback()
def main(ctx: typer.Context, ...):
    ctx.obj = Context(pyvko=..., world=..., config=...)
```

Содержит: `pyvko` (VK API), `world` (файловая структура), `config` (загруженный конфиг).
