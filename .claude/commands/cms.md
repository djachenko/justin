# CMS_2 — Content Management System

## Архитектура

```
cms_2/
├── storage/
│   ├── sqlite/         # SQLiteDatabase, SQLiteEntry — текущий бэкенд
│   └── google_sheets/  # Google Sheets бэкенд (альтернативный)
└── sub_cms/            # Доменные CMS для разных сущностей
    ├── PeopleCMS
    ├── PhotosetsCMS
    ├── PostsCMS
    ├── TagsCMS
    └── ...
```

## Использование

`cms/` (JSON-based) — **устарел, не трогать**.  
`cms_2/` — текущий, SQLite-based.

## Бэкенды хранения

**SQLite** (`storage/sqlite/`):
- `SQLiteDatabase` — подключение, создание таблиц
- `SQLiteEntry` — строка таблицы, сериализация/десериализация

**Google Sheets** (`storage/google_sheets/`):
- Используется через `google-api-python-client`
- Требует OAuth-токен (`google-auth-oauthlib`)
- Spreadsheet ID сейчас захардкожен в `app.py` — TODO: вынести в конфиг

## Sub-CMS

Каждый тип сущности — отдельный `SubCMS`. Паттерн: абстрактный базовый класс + реализация поверх бэкенда. Entry — сериализуемый объект с методами `to_row()` / `from_row()`.

## DI

`cms_2` собирается через `Context` / `di/`. Бэкенд выбирается при сборке приложения.
