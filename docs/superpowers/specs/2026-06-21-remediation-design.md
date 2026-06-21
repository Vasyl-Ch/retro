# Ремедиация — фокусный безопасный проход (дизайн-спека)

**Дата:** 2026-06-21
**Направление:** 1 из 3 (Ремедиация → Билингва → Конструктор)
**Статус:** на ревью

## Контекст

Проект `d:\retro` — Django 5.2 (`distributor/`) + Vite/Tailwind/Tailus (`ada-frontend/`),
мульти-вертикальный конфигурируемый сайт с пресетами и настройками в админке.

Аудит выявил набор проблем безопасности, корректности и производительности. Этот проход —
**первый из трёх** и сознательно узкий: закрыть подтверждённые проблемы быстро и безопасно,
не трогая модель данных глубоко (это сделает направление «Билингва») и без крупных
рефакторингов. Каждый поведенческий фикс — через TDD (сначала падающий тест, затем код).

## Цели

- Устранить подтверждённые риски безопасности.
- Закрыть подтверждённый дефект корректности (пагинация вакансий).
- Добавить дешёвые индексы и микро-оптимизацию запросов.
- Покрыть тестами все поведенческие изменения.

## Вне рамок (осознанно отложено)

- Перевод контента (товары/новости/вакансии) и английская админка → **Билингва** (направление 2).
- Визуальный редактор цветов/позиций/фонов → **Конструктор** (направление 3).
- Расширение тестового покрытия contacts/content/vacancies сверх затронутого этим проходом.
- Рефакторинги: `CartMixin`, дробление крупных view, кэш context-процессоров.

## Подтверждённые находки (после прямой проверки)

Отсеяны как ложные/некритичные после верификации:
- `global_nav` корректен — берёт только корневые категории с `prefetch_related("children")`; N+1 нет.
- `Order.total` и снапшот цены при checkout — корректны by design.
- `production.py` уже содержит хардненинг (HSTS, SSL-redirect, secure-cookies, NOSNIFF, `X_FRAME_OPTIONS=DENY`).

Подтверждены и берутся в работу:

| # | Проблема | Где | Severity |
|---|----------|-----|----------|
| S1 | `SECRET_KEY` дефолтит на `"django-insecure-change-me"`, в проде не валидируется | `config/settings/base.py:27`, `production.py` | HIGH |
| S2 | Summernote-HTML рендерится через `|safe` без санитизации (stored XSS, staff-only) | `news_detail.html:26`, `promo_detail.html:35`, `vacancies/detail.html:127,132,137` | HIGH |
| S3 | `ImageField` без валидации расширения/размера (15 полей) | все `*/models.py` | MEDIUM |
| C1 | `VacancyListView` без пагинации | `apps/vacancies/views.py:6` | MEDIUM |
| P1 | 8 полей `is_active` без `db_index` (фильтруются в каждом запросе) | catalog/content/vacancies/core models | MEDIUM |
| P2 | `page_background` грузит все записи `PageBackground` вместо 2 нужных | `apps/core/context_processors.py:27` | LOW |

## Решения по развилкам

- **Санитизация:** на `save()` модели (не при рендере). База хранит уже безопасный HTML.
  Для старых записей — одноразовая data-миграция, прогоняющая существующий контент через санитайзер.
- **SVG:** разрешён только для брендинга (лого/favicon). Контентные картинки — растровые.

## Дизайн фиксов

### S1. Guard конфигурации production
- В `config/settings/production.py`: после импорта `base` проверять `SECRET_KEY`.
  Если пуст или равен дефолту `"django-insecure-change-me"` → `raise ImproperlyConfigured`.
- Там же: при пустом `ALLOWED_HOSTS` (а `DEBUG=False`) → `ImproperlyConfigured` с понятным сообщением.
- Вынести проверку в маленькую чистую функцию (тестируемую юнит-тестом), напр.
  `apps/core/conf_checks.py: assert_production_secret(secret_key)`.

### S2. Санитизация Summernote-HTML
- Новый модуль `apps/core/sanitizer.py`:
  - `ALLOWED_TAGS` / `ALLOWED_ATTRIBUTES` — whitelist (заголовки h2–h4, p, br, ul/ol/li,
    strong/em/u, a[href,title,target,rel], blockquote, img[src,alt,width,height], table-набор).
  - `sanitize_html(value: str) -> str` на основе `bleach.clean(..., strip=True)`;
    ссылки прогонять через `bleach.linkify`/защиту `rel="noopener"` для `target="_blank"`.
- Применение в `save()` соответствующих моделей **до** `super().save()`:
  - `content.News.content`
  - `content.Promo.description`
  - `vacancies.Vacancy.description`, `requirements`, `conditions`
- Шаблоны не меняем (`|safe` остаётся — контент уже очищен).
- **Forward-compat с modeltranslation:** билингва позже добавит `_en/_uk` колонки. Санитайзер
  писать так, чтобы в `save()` можно было пройтись по фактическим полям перевода; на этом этапе
  переводов у этих полей нет — санитизируем базовые поля.
- **Data-миграция:** прогнать `sanitize_html` по существующим записям News/Promo/Vacancy.

### S3. Валидаторы загрузки изображений
- В `apps/core/validators.py` добавить:
  - `validate_image_file(file)` — проверка размера (лимит, напр. `MAX_IMAGE_MB = 5`) и расширения.
  - Набор `RASTER_EXTENSIONS = {jpg, jpeg, png, webp, gif}`,
    `BRANDING_EXTENSIONS = RASTER_EXTENSIONS | {svg}`.
  - Фабрики/инстансы валидаторов: `raster_image_validators`, `branding_image_validators`
    (комбинируют `FileExtensionValidator` + размер).
- Навесить:
  - Брендинг (svg ok): `core.SiteSettings.brand_logo`, `favicon`, `side_logo_left/right`.
  - Контент (raster): `core.PageBackground.image`, `content.Banner.background`,
    `content.News.image`, `content.Promo.image`, `catalog.Brand.logo`, `catalog.Product.image`,
    `catalog.ProductImage.image`, `vacancies.Vacancy.cover_image`, `vacancies.VacancyImage.image`.
- Валидаторы попадают в миграции (no-op на уровне SQL) — сгенерировать `makemigrations`.
- Остаточный риск: SVG (брендинг) — известный вектор; грузит только staff, фиксируем в комментарии.

### C1. Пагинация вакансий
- `VacancyListView.paginate_by = 12` (или согласованное число).
- В `templates/vacancies/list.html` подключить `partials/_pagination.html`, итерируя `page_obj`.

### P1. Индексы `is_active`
- `db_index=True` на:
  `catalog.Brand.is_active`, `catalog.Category.is_active`, `catalog.Product.is_active`,
  `content.Banner.is_active`, `content.News.is_active`, `content.Promo.is_active`,
  `vacancies.Vacancy.is_active`, `core.PageBackground.is_active`.
- По миграции на приложение.

### P2. Микро-оптимизация `page_background`
- В `apps/core/context_processors.py` фильтровать
  `PageBackground.objects.filter(is_active=True, page_key__in=[current_key, SITE_KEY])`
  вместо загрузки всех записей. Логика выбора (страница → site → none) сохраняется.

## Тестирование (TDD)

Для каждого поведенческого фикса — сначала падающий тест:
- **S1:** юнит-тест `assert_production_secret` — поднимает на дефолтном/пустом ключе, проходит на валидном.
- **S2:** `News`/`Promo`/`Vacancy` с `<script>alert(1)</script>` и `onerror=` — после `save()` опасное вырезано, безопасные теги сохранены. Тест data-миграции — на существующей записи.
- **S3:** загрузка `.exe`/переименованного файла и oversize → `ValidationError`; валидный `.png` проходит; `.svg` проходит для брендинга и отклоняется для контентного поля.
- **C1:** список вакансий с N+1 записей отдаёт `page_obj` и корректную пагинацию.

Прогон: `python manage.py test` (в Docker — как в README). Линт/чек: `manage.py check`.

## Миграции

- `content`, `vacancies`, `catalog`, `core`: миграции на `db_index` и валидаторы.
- `content`, `vacancies`: data-миграция санитизации существующего HTML.
- Все миграции — аддитивные и обратимые; данные не теряются.

## Критерии приёмки

- `manage.py check` без ошибок; `manage.py test` зелёный, новые тесты проходят.
- Контентный HTML с `<script>`/обработчиками событий не сохраняется/не отдаётся.
- Загрузка не-изображения или oversize отклоняется в админке.
- Production-настройки падают с понятной ошибкой при дефолтном `SECRET_KEY`/пустом `ALLOWED_HOSTS`.
- Список вакансий пагинируется.
- `EXPLAIN`-планы по `is_active`-фильтрам используют индекс (или хотя бы индекс создан).

## Риски и заметки

- Санитизация может срезать «экзотический» HTML, который staff вставлял раньше — whitelist
  делаем достаточно широким (таблицы, изображения, ссылки); при необходимости расширим.
- Data-миграция санитизации необратима по содержимому (старый «грязный» HTML не восстановить) —
  это намеренно; откат миграции просто не меняет уже очищенные данные.
- Изменения изолированы и не конфликтуют с предстоящей билингвой (она добавит колонки переводов;
  санитайзер и валидаторы переиспользуются).
