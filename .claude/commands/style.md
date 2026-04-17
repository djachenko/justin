# Code Style & Принципы

## Naming Conventions

```python
# Классы — PascalCase
class StageCheck:
class UnselectedCheck(StemExtractingCheck):
class TyperChecksReporter(ChecksReporter):

# Методы/функции — snake_case
def should_fix(self, reporter: ChecksReporter) -> bool:
def run_checks(self, photoset: Photoset) -> None:

# Приватные методы — одно подчёркивание
def _extract_files(self) -> List[Path]:

# Приватные атрибуты класса — одно подчёркивание
self._prechecks = prechecks

# Константы модульного уровня — UPPER_SNAKE_CASE
MAX_RETRIES = 3
```

## Файловая структура

Один публичный тип = один файл (как правило). Файл содержит класс + его классы проблем:

```python
# unselected.py
@dataclass
class UnselectedProblem:
    files: List[Path]
    def __str__(self): ...

class UnselectedCheck(StemExtractingCheck):
    ...
```

Абстрактные базовые классы — в `abstracts/` или отдельном файле `base.py`.

## Принципы

**DRY — религия.** Любое дублирование в иерархии недопустимо. Общая логика — строго в базовом классе.

**Никаких сайд-эффектов в `__init__`.** Только `self.x = x`. Никакого создания других объектов, открытия файлов, сетевых вызовов.

**Exception вместо railway.** Вместо `if problems: return problems` на каждом уровне — `raise StageCheckError(problems)`. Ловится один раз наверху.

**Строки — в классе, не в месте вызова.** Тексты ошибок живут как свойство/метод класса Problem. Grep по тексту → находишь класс сразу.

**Параллельные директории для рискованных миграций.** `logic2/` рядом с `logic/`. Старое сносится только когда новое протестировано и подключено.

**Инверсия зависимостей.** Класс не знает о своём контексте. Связи — только в `container.py`.

## Форматирование

- **ruff** для линтинга, **black** для форматирования — через `pyproject.toml`
- Type hints обязательны в новом коде
- Датаклассы (`@dataclass`) для простых value objects
- `@cached_property` вместо `@property @cache` (последнее = утечка памяти на инстансах)

## Чего не делать

- `print()` в новом коде — только через `ChecksReporter`
- `assert False` как заглушка → `raise NotImplementedError(f"{type(self).__name__} must implement ...")`
- `@property @cache` на инстанс-методах → `@cached_property`
- `path.strip("wall")` → `path.removeprefix("wall")`
- Смешивать `logic/` и `logic2/` — это параллельные миры
- Добавлять логику в `__init__`
- Трогать `cms/` (JSON-based, устарел)
