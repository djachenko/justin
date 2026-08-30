# Git: workflow и соглашения

## Модель: GitHub Flow

Один постоянный `master`. Все фичи, рефакторинги и чоры — в отдельных ветках.

**Правила:**
- Ветка всегда стартует от актуального `master`
- Мёрдж в master — всегда `--no-ff` (обязательный merge commit)
- Подтянуть изменения master в ветку — `git merge master` (не rebase)

## Именование веток

```
feature/<name>   # новая функциональность
refactor/<name>  # рефакторинг без изменения поведения
fix/<name>       # исправление бага
chore/<name>     # инфраструктура, документация, зависимости
```

## Semantic commits

Формат: `<type>: <что сделано>`

| Тип | Когда |
|---|---|
| `feat` | новая функциональность |
| `fix` | исправление бага |
| `refactor` | изменение кода без изменения поведения |
| `chore` | сборка, зависимости, конфиги, документация |
| `style` | форматирование, переименования без смысловых изменений |
| `test` | тесты |
| `revert` | откат коммита |

**Правила:**
- Строчная буква после `:`
- Без точки в конце
- Без `Co-Authored-By:` и других мета-строк от инструментов
- Императив, совершенный вид: *Added*, *Fixed*, *Refactored* — не *Add*, не *Adding*

## Автор

Все коммиты — один автор:

```bash
git config user.name "Igor Djachenko"
git config user.email "i.s.djachenko@gmail.com"
```

Перед коммитом проверять `git config user.name`. Если не совпадает — исправить.

## Слияние ветки в master

```bash
git checkout master
git merge --no-ff feature/xxx -m "Merge branch 'feature/xxx'"
```

## Старые ветки

Не удалять — переносить в `archive/`:

```bash
git branch -m feature/old archive/feature/old
```

## Worktrees

Активные рабочие деревья — в `.claude/worktrees/` (в `.gitignore`).

```bash
git worktree add .claude/worktrees/<name> -b <branch>
git worktree remove .claude/worktrees/<name> --force
```

Переключить worktree на другую ветку — через `git -C .claude/worktrees/<name> checkout <branch>`. Если есть незакоммиченные изменения — сначала уточнить у пользователя, что с ними делать. Не стэшить самовольно.
