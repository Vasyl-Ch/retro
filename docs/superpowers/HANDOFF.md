# HANDOFF — состояние работ (на 2026-06-25)

Документ для передачи в новую сессию. Что сделано, как проверить, что осталось.

---

## 1. Общая картина: 3 направления

Проект `d:\retro` — Django 5.2 (`distributor/`) + Vite/Tailwind (`ada-frontend/`), мульти-вертикальный
сайт. Работа ведётся в 3 последовательных направлениях (каждое: брейншторм → спека → план →
subagent-driven исполнение → ревью → мёрж):

| # | Направление | Статус |
|---|-------------|--------|
| 1 | **Ремедиация** (безопасность/корректность/производительность) | ✅ влито в `main` (merge `2983824`) |
| 2a | **Билингва: статический UI + админка** | ✅ влито в `main` (merge `1cb7c73`) |
| 2b | **Билингва: контент** (modeltranslation) | ✅ влито в `main` (merge `61db8c0`) |
| 3 | **Конструктор** (цвета/прозрачность/позиции/фоны + живое превью) | ✅ влито в `main` (merge `964e181`) |

**Все 3 направления завершены и влиты в `main`.** Полный сьют — 89/89. В remote не пушилось.

Дорожная карта и заметки — в памяти проекта (`remediation-roadmap.md`, `summernote-readmask.md`).

---

## 2. Где мы сейчас (git)

- **Активная ветка:** `main`. Ветки `bilingua-2b` больше нет (влита `--no-ff` и удалена).
- Рабочее дерево чистое (кроме `.claude/settings.local.json` — служебный, не коммитить, и этого HANDOFF).
- Последние коммиты 2b: `354e18f`, `1407972`, `740394e`, `50030b3`, `4911942`, `c47b1ad`, merge `61db8c0`.

---

## 3. Что сделано в 2b (готово)

Контентные поля двуязычны (`_en`/`_uk` через modeltranslation):
- **Переводимые:** catalog `Brand(name,description)`, `Category(name)`,
  `Product(name,description,location)`, `VehicleSpec(color)`, `ProductSpec(label,value)`;
  content `Banner(title,subtitle,button_text)`, `News(title,preview,content)`, `Promo(title,description)`;
  vacancies `Vacancy(title,city,short_tagline,description,requirements,conditions)`, `VacancyImage(caption)`.
- Существующий украинский бэкфилл-нут в `_uk` сырым SQL (`_en` пустой → fallback en→uk).
- Админки на `TabbedTranslationAdmin` + translated inlines; rich-text санитизируется по всем языкам
  через `apps/core/sanitizer.py::sanitize_instance_html`.
- **Баг-фикс:** `django_summernote.SummernoteTextField.to_python` падал на `None`
  (`bleach.clean(None)`) — и при миграции, и при runtime save. Починено None-safe подклассом
  `apps/core/fields.py::SummernoteTextField` (используется в News/Promo/Vacancy). Покрыто тестами.
- **Важно (исправлено в памяти):** у поля НЕТ `from_db_value` → маскирования при чтении НЕТ;
  санитизация происходит на `save()` (strip). Тесты санитизации проверяют **in-memory** экземпляр.

**Артефакты 2b:** спека `docs/superpowers/specs/2026-06-23-bilingua-2b-design.md`,
план `docs/superpowers/plans/2026-06-23-bilingua-2b.md`, ledger `.git/sdd/progress.md` (секция 2b + FINAL REVIEW).

---

## 4. Как проверить (в Docker)

```
docker compose -f docker-compose.dev.yml exec -T web python manage.py test --settings=config.settings.development
```
Ожидается **89/89**, `check` чисто, `makemigrations --check --dry-run` → No changes detected.

> ⚠️ Из Git Bash для docker exec с абсолютными путями контейнера используй префикс `MSYS_NO_PATHCONV=1`
> (иначе `/app/...` манглится в `C:/Program Files/Git/...`). Стек поднимать с `WEB_PORT=8008 DB_PORT=5438`.
> Docker Desktop может потребовать ручного старта.

---

## 5. Направление 3 (Конструктор) — готово

Админ-редактор внешнего вида (`apps/core/appearance/` — чистый домен `palette.py` + сервис
`services.py`; поля на `SiteSettings`/`PageBackground`; **coloraide** + **django-colorfield**):
кастомный акцент → палитра `--primary-*` (перекрывает тему), прозрачность шапки/футера
(`--chrome-alpha` через CSS `color-mix`), позиция/размер фона, живое превью в `<iframe>`
(postMessage). Спека/план: `docs/superpowers/{specs,plans}/2026-06-25-constructor*`.

**Будущие под-проекты (не начаты):** drag-drop конструктор блоков, несколько сохранённых тем,
поэлементное редактирование лейаута, шрифты.

## 5a. Нюансы окружения (Docker)
- Веб-контейнер сам выполняет `migrate` при старте (см. `command` в `docker-compose.dev.yml`) —
  **НЕ** запускать `migrate` вручную параллельно (был race → duplicate pg_type). Для сброса грязной
  dev-БД: `docker compose -f docker-compose.dev.yml down -v`, затем подъём заново.
- Зависимости (`coloraide`, `django-colorfield`) ставятся при билде образа — после добавления новых
  зависимостей нужен `docker compose -f docker-compose.dev.yml build`, иначе пересозданный контейнер
  не стартует.
- Jazzmin-админка тянет внешние CDN-ассеты — в песочнице страница админки может «висеть» на загрузке
  (UI-автоматизация админки затруднена); публичный фронт грузится нормально.

## 6. Процесс/нюансы
- subagent-driven (свежий имплементер на задачу + ревью; финальное ревью на opus). Прогресс — в
  `.git/sdd/progress.md`. Проверять реальный git-стейт, а не только текст отчёта субагента.
- modeltranslation: `MODELTRANSLATION_DEFAULT_LANGUAGE="en"`, fallback `("en","uk")`. **НЕ** запускать
  `update_translation_fields`. В remote **не пушим** без явной просьбы (1/2a/2b мёржились локально).
