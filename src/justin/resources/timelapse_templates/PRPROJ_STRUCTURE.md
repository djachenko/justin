# Premiere Pro `.prproj` — разобранная структура

Реверс-инжиниринг формата, накопленный при написании генератора таймлапсов
(`justin/actions/timelapse_prproj.py`). Не полная спецификация — только то, что
пощупали руками и проверили открытием в Premiere. Данные дорогие (каждая проверка
= ручное открытие проекта), поэтому фиксируем.

Версия Premiere: проект собран в Premiere Pro 2024-эпохи, шаблон — `step_12`.

---

## Файл

- `.prproj` — это **gzip-сжатый XML** (одна строка `<?xml ...?>` + дерево).
- Разжать: `gzip.decompress(bytes)`. Сжать обратно тем же gzip.
- Корень — `<PremiereData Version="3">`, внутри плоский список **top-level блоков**,
  каждый с отступом в один таб (`\t<Tag ...>`).

## Блоки

Каждый значимый объект — top-level блок вида:

```xml
	<TagName ObjectID="88" ClassID="064ec682-..." Version="11">
		...
	</TagName>
```

или самозакрывающийся `\t<Tag .../>`.

Парсинг: [`Xml.toplevel_blocks()`](#структура-кода-генератора) режет по `^\t<Tag` и находит закрывающий `\n\t</Tag>`.
Блоки правятся вырезанием/вставкой по байтовым офсетам в сырой строке.
Подробно про `ObjectID` / `ClassID` — см. [Две системы идентификаторов](#две-системы-идентификаторов--критично).

## Две системы идентификаторов — КРИТИЧНО

| Атрибут | Тип | Уникальность | Назначение |
|---------|-----|--------------|------------|
| `ObjectID` | целое (маленькое) | **только внутри своего ClassID** | id объекта |
| `ObjectRef` | целое | ссылка на `ObjectID` | ссылка |
| `ObjectUID` | uuid | глобально | id объекта |
| `ObjectURef` | uuid | ссылка на `ObjectUID` | ссылка |
| `ClassID` | uuid | **константа типа** | какого класса блок |

**Грабли №1 — ObjectID НЕ глобально уникален.** Одно и то же число (напр. `56`) может
быть разными блоками разных классов. Проверка «висячих» ссылок по голому числу
даёт ложные срабатывания. Резолвить надо с учётом типа.

**Грабли №2 — ClassID это uuid, но его НЕЛЬЗЯ перегенерировать.** ClassID — константа
типа класса (у всех `AudioClipTrackItem` она одинаковая). При клонировании звука
ремапить надо только идентичность объекта (`ObjectUID`/`ObjectURef` + `<ID>`), а
ClassID и `ESP.PresetGuid` оставлять как есть. Если перегенерить ClassID — Premiere
не узнаёт класс блока и **молча отказывается открывать проект**. Это был главный баг.
Логика клонирования: [`clone_sound_blocks`](#структура-кода-генератора).

**Грабли №3 — ссылки идут через обёртки.** Не всегда `<TypeName ObjectRef=.../>`.
Бывает `<Clip ObjectRef="56"/>` (тег `Clip`, а цель — VideoClip или AudioClip),
`<Item ObjectURef=.../>`, `<TrackItem ObjectRef=.../>`, `<Source ObjectRef=.../>`,
`<Content ObjectRef=.../>`, `<Components ObjectRef=.../>`, `<Markers ObjectRef=.../>`.
Тег ссылки = роль, не обязательно тип цели.

**Грабли №4 — `<TrackItem` это префикс `<TrackItems`.** Регекс `<TrackItem[^/]*` жадно
хватает и `<TrackItems Version="1">`. В правках требовать пробел: `<TrackItem `,
`<Item ` — иначе можно снести открывающий тег контейнера и получить битый XML.

## Время

- Всё в **тиках**: `PREMIERE_TIMEBASE = 254_016_000_000` тик/сек.
- Кадр при 10 fps = `254_016_000_000 / 10 = 25_401_600_000` тик.
- Длительность аудио в тиках = `секунды_ffprobe * PREMIERE_TIMEBASE`.
- Длительность клипа хранится в НЕСКОЛЬКИХ местах, должны быть согласованы:
  `TrackItem <End>` (позиция конца на дорожке), `AudioClip <OutPoint>` (длина клипа),
  `MasterClip <OriginalDuration>`, `Media`, `AudioStream`.

---

## Граф одного звука (аудио-подграф)

Клип звука — это ~11–20 блоков, связанных ссылками (не по имени файла!).
Имя файла (`<Name>x.mp3</Name>`, путь `./sound/x.mp3`) содержат только несколько
из них; остальные достижимы только обходом ссылок ([`collect_sound_closure`](#структура-кода-генератора)).

```
ClipProjectItem            ← элемент панели проекта, <Name>, ObjectUID (на него ссылается BinProjectItem)
  └─ MasterClip            ← <Clip Index="0">VideoClip, <Clip Index="1">AudioClip
       ├─ VideoClip        (у mp4; у mp3 отсутствует)
       │    ├─ Markers
       │    └─ VideoMediaSource ← <Source ObjectRef>
       ├─ AudioClip
       │    ├─ Markers            (МОЖЕТ БЫТЬ ОБЩИМ с VideoClip!)
       │    ├─ AudioComponentChain
       │    └─ SecondaryContent ← <Content ObjectRef> → AudioMediaSource
       ├─ Media
       │    ├─ VideoStream  (у mp4)
       │    └─ AudioStream → AudioMediaSource
       ├─ SubClip          ← <Clip ObjectRef> на AudioClip, <MasterClip ObjectURef>
       └─ ClipLoggingInfo
```

Плюс сериализаторы каналов: `ClipChannelSerializer`, `ClipChannelGroupVectorSerializer`,
`ClipChannelVectorSerializer` — тоже часть подграфа, тоже без имени файла.

**Грабли №5 — общий `Markers`.** В шаблоне (mp4-звук) блок `Markers` бывает
разделён между `VideoClip` и `AudioClip` (оба содержат `<Markers ObjectRef="65"/>`).
При срезании видео-части нельзя удалять блоки, на которые ещё ссылается выживший
AudioClip. Подробно про срезание: [mp4 → mp3](#mp4--mp3-audio-only).

**Типы блоков медиа-подграфа** (для обхода замыкания, `_CLIP_MEDIA_TYPES`):
ClipProjectItem, MasterClip, AudioClip, VideoClip, SubClip, Media, AudioStream,
VideoStream, AudioMediaSource, VideoMediaSource, Markers, AudioComponentChain,
ClipLoggingInfo, SecondaryContent, ClipChannelSerializer,
ClipChannelGroupVectorSerializer, ClipChannelVectorSerializer.

## mp4 → mp3 (audio-only)

Шаблонный звук — mp4 (видеопоток + аудиопоток). Для mp3/wav и т.п. срезать видео-часть
(см. [граф подграфа](#граф-одного-звука-аудио-подграф) и [Грабли №5](#граф-одного-звука-аудио-подграф) про общий Markers):
1. убрать `<VideoStream ObjectRef>` из `Media` и сам top-level `VideoStream`;
2. удалить `VideoClip` и его sub-блоки (Markers, VideoMediaSource), КРОМЕ общих с AudioClip;
3. в `MasterClip` убрать `<Clip Index="0">` (VideoClip), переиндексировать AudioClip на Index 0.

Реализация: [`AudioSound.adapt`](#структура-кода-генератора).

---

## Панель проекта vs таймлайн

**Панель проекта** (project panel / bin):
- `BinProjectItem` содержит `<Items>` со списком `<Item Index="N" ObjectURef="uuid"/>`,
  каждый указывает на `ClipProjectItem` (по [ObjectUID](#две-системы-идентификаторов--критично)).
- Чтобы звук был виден в панели — его `ClipProjectItem` должен быть зарегистрирован Item'ом.
- Структура `ClipProjectItem` внутри подграфа: [Граф одного звука](#граф-одного-звука-аудио-подграф).

**Таймлайн** (sequence):
- Дорожки: `VideoClipTrack` (кадры + cover) и `AudioClipTrack` (звук).
- Внутри `ClipTrack → ClipItems → TrackItems` со списком `<TrackItem Index="N" ObjectRef="id"/>`,
  указывающих на `*ClipTrackItem` блоки.
- **`AudioClipTrackItem`** — экземпляр звука на дорожке:
  ```
  AudioClipTrackItem
    ├─ ComponentOwner → <Components ObjectRef> → AudioComponentChain
    ├─ TrackItem → <Start> (позиция, у первого опущена = 0), <End> (= Start + длина)
    ├─ SubClip ObjectRef  → SubClip (у него <Name>, <Clip>→AudioClip)
    └─ <ID> (instance guid)
  ```
- У таймлайн-инстанса **свой** SubClip/AudioClip/AudioComponentChain, отдельный от
  панельного MasterClip. Диффом: один звук в timeline+panel добавляет к «только панель»
  +1 AudioClipTrackItem, +1 SubClip, +1 AudioClip, +1 AudioComponentChain, +2 SecondaryContent.

**Последовательная раскладка звуков встык:** звук N начинается там, где кончился N-1.
`TrackItem <Start> = Σ длин предыдущих`, `<End> = Start + длина`, `AudioClip <OutPoint> = длина`.

**Порядок дорожек:** первый populated `<TrackItems>` в документе — видеодорожка. Чтобы
попасть в аудиодорожку при вставке, искать по id уже существующего аудио-TrackItem'а.

---

## Каскадное удаление висячих ссылок (`remove_dangling_refs`)

При вырезании блоков (cover, звук) выжившие ссылки надо чистить. Каскад за проход:
- [top-level блок](#блоки) удаляется, если его `<Media|VideoClip|AudioClip|MasterClip ObjectURef>`
  указывает на несуществующий [uuid](#две-системы-идентификаторов--критично);
- ...или его `<SubClip|Source|Content ObjectRef>` указывает на несуществующий id
  (так каскадом уходят VideoClip/AudioClip/SecondaryContent, чей MediaSource удалён по имени;
  структуру связей см. [Граф одного звука](#граф-одного-звука-аудио-подграф));
- из `<Items>` ([панель](#панель-проекта-vs-таймлайн)) и `<TrackItems>` ([таймлайн](#панель-проекта-vs-таймлайн))
  вычищаются осиротевшие записи, TrackItems переиндексируются.

Повторять до стабилизации (в коде — до 10 итераций).

---

## Лишний cover

Cover — лишний кадр перед последовательностью, занимает 1 fps_ticks в начале.
Удаление: вырезать блоки с `cover.jpg` по имени (ClipProjectItem/MasterClip/Media/
SubClip), остальное (VideoClip, VideoClipTrackItem, запись в TrackItems) уходит
[каскадом](#каскадное-удаление-висячих-ссылок-remove_dangling_refs).
Затем сдвинуть клип кадров с `[fps_ticks → seq_dur]` на `[0 → frames_dur]`.

---

## Родословная шаблона (wolfday step-снепшоты)

Шаблон собран пошагово вручную в Premiere, каждый шаг сохранён отдельным `.prproj`.
Эти снепшоты — в этой же папке `resources/timelapse_templates/`:

| Шаг | Файл | Состояние |
|-----|------|-----------|
| 0 | `26.04.17.wolfday_0_empty.prproj` | пустой проект |
| 1 | `step_1_frames_import` | импорт кадров |
| 2 | `step_2_frames_setup` | настройка кадров |
| 3 | `step_3_sound_import` | импорт звука |
| 4 | `step_4_sequence` | кадры в секвенцию |
| 7 | `step_7_cover_import` | импорт cover |
| 8 | `step_8_cover_in_sequence` | cover в секвенцию |
| 10 | `step_10_cover_in_timeline` | cover на таймлайн перед кадрами |
| **12** | **`step_12_sound_in_timeline`** | **звук на таймлайне, видеодорожка звука удалена — РАБОЧИЙ ШАБЛОН** |

`step_12` = кадры + cover + 1 mp4-звук на таймлайне, 106 кадров @ 10 fps. Байт-в-байт
равен реальному `26.04.17.wolfday_12_delete_sound_video_track.prproj`. Генератор
использует именно его (`_TEMPLATE_DATA`) и подстановкой заменяет вшитые wolfday-значения
(путь, имя первого кадра, имя фотосета, имя звука, тики) на целевые.

Промежуточные шаги (5,6,9,11) в родословной есть в исходном wolfday, но для генератора
не нужны.

---

## Структура кода генератора

Генератор разбит на несколько модулей в `justin/actions/`:

```
timelapse_re.py        — regex-константы (ObjectID/UID/URef/Ref, uuid-паттерны)
timelapse_tags.py      — Tag (StrEnum): имена top-level тегов Premiere Pro
timelapse_block.py     — Block (NamedTuple): один top-level блок + свойства .header/.id/.span
timelapse_xml.py       — Xml: работа с сырым XML; collect_sound_closure; clone_sound_blocks
timelapse_sound.py     — Sound (ABC) → AudioSound / VideoSound: адаптация mp3/mp4-структуры
timelapse_settings.py  — TimelapseSettings: параметры генерации (fps, timeline_sounds и др.)
timelapse_sources.py   — TimelapseSources: пути к исходникам (кадры, cover, звуки)
timelapse_prproj.py    — TimelapseSchema: основная логика; generate_prproj: точка входа
```

### Зависимости (снизу вверх)

```
timelapse_re
    └─ timelapse_block   (импортирует _OBJECT_ID_RE)
    └─ timelapse_xml     (импортирует все регекспы)

timelapse_tags
    └─ timelapse_xml     (Tag используется в _CLIP_MEDIA_TYPES)
    └─ timelapse_sound   (Tag.Media / MasterClip / VideoClip / AudioClip)
    └─ timelapse_prproj  (Tag.AudioClipTrackItem / ClipProjectItem / SubClip / AudioClip)

timelapse_block
    └─ timelapse_xml     (Block — результат Xml.toplevel_blocks())
    └─ timelapse_prproj  (через timelapse_xml)

timelapse_xml
    └─ timelapse_sound   (Xml передаётся в Sound.adapt())
    └─ timelapse_prproj  (Xml — центральный объект TimelapseSchema)

timelapse_sound
    └─ timelapse_prproj  (Sound.adapt() вызывается при клонировании)

timelapse_settings + timelapse_sources
    └─ timelapse_prproj  (аргументы generate_prproj)
```

### Ключевые типы

**`Block`** (`timelapse_block.py`)  
NamedTuple: `start`, `end`, `tag`, `text`.  
- `.header` — первые 120 символов (`text[:120]`), достаточно для открывающего тега с ObjectID/UID.  
- `.id` — значение `ObjectID` из заголовка, `None` если нет.  
- `.span` — `(start, end)`, передаётся в `Xml.remove_blocks_by_positions`.

**`Tag`** (`timelapse_tags.py`)  
`StrEnum` — имена всех top-level тегов, которые встречаются в коде (сравнение через `b.tag == Tag.AudioClip`).  
Так как `StrEnum` наследует `str`, работает без изменений там, где ожидается строка.

**`Xml`** (`timelapse_xml.py`)  
Обёртка над сырым XML-текстом. Мутабельная: все правки меняют `_xml` строку на месте.  
Ключевые методы:
- `from_gzip_bytes(data)` — загрузка из байтов (шаблон через `importlib.resources`)
- `to_prproj(path)` — сжатие обратно в `.prproj`
- `toplevel_blocks()` — парсинг в список `Block`
- `replace_range(start, end, text)` / `insert(pos, text)` — точечная правка по офсетам
- `remove_blocks_by_positions([(start, end), ...])` — вырезание блоков с конца, чтобы офсеты не съезжали
- `remove_dangling_refs()` — каскадная очистка висячих ссылок (до 10 итераций до стабилизации)

**`collect_sound_closure`** (`timelapse_xml.py`)  
Обход графа ссылок от seed-блоков (нашли по имени файла) до полного замыкания кластера.  
Нужен потому что большинство блоков клипа не содержат имя файла — только id-ссылки.  
Структура обходимого графа: [Граф одного звука](#граф-одного-звука-аудио-подграф).

**`clone_sound_blocks`** (`timelapse_xml.py`)  
Копирует кластер блоков одного звука, давая копии свежие id:
- числовые ObjectID/Ref сдвигаются на `id_offset` (больше любого существующего id);
- ObjectUID/ObjectURef и `<ID>` заменяются на новые `uuid4()`;
- ClassID и `ESP.PresetGuid` — **не трогать**: это константы типа, общие для всех блоков класса.  
  Подробно: [Грабли №2](#две-системы-идентификаторов--критично).

**`Sound`** (`timelapse_sound.py`)  
ABC с методом `adapt(xml)`. Вызывается после клонирования, пока клон ещё содержит mp4-структуру шаблона:
- `AudioSound.adapt` — срезает видео-часть (VideoStream, VideoClip, их sub-блоки). Подробно: [mp4 → mp3](#mp4--mp3-audio-only).
- `VideoSound.adapt` — ничего не делает (mp4 совпадает с шаблоном)

**`TimelapseSchema`** (`timelapse_prproj.py`)  
Центральный класс. Последовательность операций над `Xml`:
1. `_substitute_paths` — заменяет wolfday-пути и имена на целевые
2. `_substitute_ticks` — fps, длительности кадров, аудио, всей последовательности. Подробно: [Время](#время).
3. `_apply_sounds` — клонирует шаблонный звук N раз, адаптирует (`Sound.adapt`), регистрирует в [панели и таймлайне](#панель-проекта-vs-таймлайн)
4. `_layout_sounds_in_timeline` / `_remove_sounds_from_timeline` — управление раскладкой. Подробно: [Панель проекта vs таймлайн](#панель-проекта-vs-таймлайн).
5. `_remove_cover` — вырезает cover и сдвигает кадровый клип в ноль. Подробно: [Лишний cover](#лишний-cover).
6. `xml.remove_dangling_refs()` — финальная уборка. Подробно: [Каскадное удаление](#каскадное-удаление-висячих-ссылок-remove_dangling_refs).

### Поток данных

```
TimelapseSources + TimelapseSettings
        │
        ▼
TimelapseSchema.__init__
        │
        ▼
Xml.from_gzip_bytes(_TEMPLATE_DATA)   ← importlib.resources → template.prproj
        │
   _substitute_*        ← заменяем wolfday-заглушки на реальные значения
        │
   _apply_sounds        ← clone_sound_blocks × N → Sound.adapt × N → вставка в XML
        │
   _layout / _remove    ← управляем тем, что на таймлайне
        │
   _remove_cover        ← если cover отсутствует
        │
   remove_dangling_refs ← итеративная очистка
        │
        ▼
Xml.to_prproj(output_path)            ← gzip → .prproj
```
