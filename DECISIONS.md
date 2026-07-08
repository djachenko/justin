# Архитектурные решения

Решения принятые осознанно — чтобы не переспрашивать при следующем заходе.

---

## Folder.rename() — merge при конфликте имён

Если директория с таким именем уже существует — содержимое объединяется, а не перезаписывается. Стандартный `mv` снёс бы существующую директорию. Для фото-воркфлоу merge — правильное поведение: не терять файлы.

---

## Photoset — девять одинаковых property

`return self.folder[key]` повторяется для каждого подкаталога намеренно. Даёт автодополнение в IDE и защиту от опечаток в строковых ключах. Не рефакторить в цикл.

---

## frozendict для Extra

Иммутабельность Extra намеренная — предотвращает случайную мутацию при прокидывании через пайплайн. Связано с `|=` в `run_for_photoset()` — при frozendict создаёт новый объект, не мутирует оригинал.

---

## fromdict() — частичная десериализация

Текущее поведение (глотать ошибки, ставить None) — осознанный компромисс для работы с легаси JSON. Не идеально. Запланирован рефакторинг: изучить `dacite`, сделать явный маппинг типов. До тех пор — не трогать.

---

## tag_usage_count() — O(n×m) вместо GROUP BY

SQL в коде минимизируется намеренно. Планируется узкий метод `count_by(cls, field, value)` в `SQLiteDatabase` — не переписывать пока он не появится.

---

## Structure.SET_MARKER — мутабельный class attribute

Временное состояние до переезда на `valifold`. Не трогать — всё равно переписывать.

---

## VKBrowser — URL для event-specific формы

Правильная форма создания события открывается НЕ через `https://vk.com/groups_create` (generic community wizard), а напрямую: `https://vk.com/groups/my_events?w=groups_create_new_event`. Это эквивалентно клику на "+" рядом с "My events" в левом меню. Форма — iframe `static.vk.com/community_create/#/event/1`.

---

## VKBrowser — sections/wall настройки

На странице `event{id}/settings/sections` нет опции "Limited". Нужные настройки для wall: кликнуть `[data-testid="wall"]` → выбрать `[data-testid="admins_and_editors"]` → убедиться что `[data-testid="form_wall_sharing_disabled"]` выключен → Save. Priority block (`add_square_outline_20`) — только для продуктов/сервисов, для фото не нужен.

---

## Explorer-скрипты — standalone, без Typer

Скрипты исследования браузера (`explore_edit.py`, `explore_sections.py`) живут в корне worktree и запускаются напрямую через Python, без тайпера и команд. Подход осознанный: explorers — разовые утилиты для R&D, не часть CLI. Через setup_event_command их не прокидывать.

---

## EventSettingsSettings — иерархия настроек события

Разделение `create` vs `setup` намеренное. `EventCreationSchema` — 3 шага wizard'а создания (iframe). `EventSettingsSchema` — отдельные страницы редактирования после создания. Объединять в одну схему нельзя: разные URL, разные механизмы DOM. `EventSettingsSettings` агрегирует setup + sections + cta + messages + addresses + extras — каждый блок `None` = не трогать.

---

## VKBrowser — два типа toggles на страницах настроек

- **React-чекбокс** (CTA `/settings/cta`, Extras `/settings/extras`): state из `inner input[type=checkbox].checked == "true"`, toggle кликом по label/div. Нет кнопки сохранения — auto-save через React.
- **Legacy idd_wrap** (Messages `?act=messages`, Addresses `?act=addresses`): state из текстового содержимого div ("Enabled"/"Disabled"), save через `button.group_save`.
- **Modal-toggles** (Sections `/settings/sections`): state из `aria-checked`, save через `form_modal_save`.

---

## KNOWN ISSUE: exit(1) в World.__discover_locations()

Грубо, но живём с этим. Минимальный шаг когда дойдут руки: заменить на `raise RuntimeError("Location discovery exceeded limit")`.

---

## Параллельные Claude Code-сессии — обязательно разные worktree

2026-07-01: две сессии работали в одной рабочей директории одновременно (без отдельных `git worktree`). Одна сессия выполнила `git checkout`, переключив ветку под другой сессией, у которой в этот момент были незакоммиченные изменения. Обошлось без потерь (правки не пересекались по файлам, перешли на новую ветку вместе с checkout), но это везение, не гарантия. Правило на будущее: каждая параллельная сессия — свой `git worktree` (см. скилл `/worktree`), не общий чекаут.
