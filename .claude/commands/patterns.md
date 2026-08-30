# Паттерны реализации: StageCheck, Hook, Stage

## Иерархия чеков (logic2/)

```
StageCheck (ABC)              base.py
├── SimpleCheck (ABC)         — только читает, не двигает файлы
│   ├── MetadataCheck         metadata.py
│   ├── GifSourcesCheck       gif_sources.py
│   ├── EverythingIsPublishedCheck  everything_published.py
│   ├── ProgressResultsCheck  progress.py
│   └── DestinationsAwareCheck (ABC)  metafile_state.py
│       ├── MetafilesExistCheck
│       └── MetafilesPublishedCheck
├── ExtractingCheck (ABC)     — двигает файлы в папку-карантин
│   └── StemExtractingCheck (ABC)
│       ├── UnselectedCheck   unselected.py    → "to_select/"
│       ├── OddSelectionCheck odd_selection.py → "odd_selection/"
│       └── EditedCheck       edited.py        → "edited/"
│   └── StructureCheck        structure.py     → "unexpected_structures/"
└── StageHook (ABC)           — безусловный, не блокирует
    ├── CandidatesHook        candidates.py    → "candidates/"
    └── ProgressHook          progress.py      → "progress/"
```

## Ключевые принципы

### prechecks

`ExtractingCheck.__init__` принимает `prechecks: List[StageCheck]`. Логика прогона prechecks реализована **только в базовом классе** — наследники не переопределяют.

### Problem

Датакласс. Текст сообщения — свойство/константа класса Problem, не строка в месте создания. Каждый модуль содержит свои классы проблем рядом с чеком:

```python
@dataclass
class UnselectedProblem:
    files: List[Path]

    def __str__(self):
        return f"Unselected: {self.files}"
```

### StageCheckError

```python
@dataclass
class StageCheckError(Exception):
    problems: List[Problem]
```

Кидается везде, ловится один раз в `Stage`. Никаких `if problems: return problems` по цепочке.

### should_fix

```python
def should_fix(self, reporter: ChecksReporter) -> bool: ...
```

Принимает `ChecksReporter`, не вызывает `input()` напрямую. `StageHook.should_fix` всегда возвращает `True`.

---

## Stage

`Stage` (`logic2/stage.py`) владеет чеками и хуками. Логика перехода:

```python
# При переходе A → B:
problems = stage_a.exit(part, reporter)   # unfix хуков A + outcoming_checks A
if not problems:
    problems = stage_b.enter(part, reporter)  # incoming_checks B + fix хуков B
if not problems:
    stage_b.transfer(photoset, root)
```

`ChecksRunner` как отдельный класс упразднён — логика внутри `Stage.__run_checks`.

---

## ChecksReporter

Абстрактный протокол вывода. `TyperChecksReporter` — реализация через `typer.secho` / `typer.confirm`.

Весь пользовательский вывод идёт **только через репортер**. `Stage` не печатает ничего напрямую.

---

## Добавление нового чека

1. Определиться с типом: `SimpleCheck` (только читает) или `ExtractingCheck` (двигает файлы)
2. Создать файл в `actions/stage/logic2/checks/simple/` или `checks/extracting/`
3. Объявить классы проблем рядом с чеком в том же файле
4. Добавить `prechecks` если нужен порядок выполнения
5. Зарегистрировать в `di/container.py`

---

## Стейдж-пайплайн (папки)

```
stage1.filter/    ← импортировано с карты
stage2.develop/   ← отобрано, идёт в Lightroom
stage2.ourate/    ← поиск необработанных
stage3.ready/     ← готово к публикации
stage3.schedule/  ← загружено, запланировано
stage4.published/ ← опубликовано
```

Имена фотосетов: `YY.M.D.event_name_in_snake_case`.
