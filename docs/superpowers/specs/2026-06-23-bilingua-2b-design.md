# Bilingua 2b — Bilingual content (modeltranslation) — design spec

**Дата:** 2026-06-23
**Направление:** 2b (из 3: Ремедиация ✅ → Билингва 2a ✅ → **Билингва 2b (контент)** → Конструктор)
**Статус:** на ревью

## Контекст

После 2a (влито в `main`): английский — основной язык, исходные строки кода английские,
украинский в `locale/uk`; `LANGUAGE_CODE="en"`, `MODELTRANSLATION_DEFAULT_LANGUAGE="en"`,
fallback `("en","uk")`. Из моделей в `modeltranslation` зарегистрирован только `SiteSettings`
(UI-лейблы). Контентные модели (catalog/content/vacancies) хранят пользовательский текст в
**одиночных колонках с украинским содержимым** — они НЕ переводимы.

2b делает контент двуязычным: каждое пользовательское текстовое поле получает `_en`/`_uk`,
с вкладками в админке, и мигрирует существующий украинский контент в `_uk`.

## Цель

Зарегистрировать контентные модели в `modeltranslation` (поля `_en`/`_uk`), перевести их
админки на `TranslationAdmin`, и аккуратно мигрировать существующий украинский контент
в украинский вариант, оставив английский пустым (fallback en→uk до ручного заполнения).

## Не-цели

- UI-переключатель языка и статический gettext — сделано в 2a.
- Авто-перевод существующего контента на английский (редактор заполняет `_en` вручную).
- Визуальный конструктор — направление 3.
- Перевод пользовательских данных/снимков: `Order.comment`, `OrderItem.product_name`,
  `ContactRequest.*`.

## Поля для перевода

- **catalog** (`apps/catalog/translation.py`):
  - `Brand`: `name`, `description`
  - `Category`: `name`
  - `Product`: `name`, `description`, `location`
  - `VehicleSpec`: `color`
  - `ProductSpec`: `label`, `value`
- **content** (`apps/content/translation.py`):
  - `Banner`: `title`, `subtitle`, `button_text`
  - `News`: `title`, `preview`, `content`
  - `Promo`: `title`, `description`
- **vacancies** (`apps/vacancies/translation.py`):
  - `Vacancy`: `title`, `city`, `short_tagline`, `description`, `requirements`, `conditions`
  - `VacancyImage`: `caption`

**Не переводим:** `slug` (URL стабильный — одиночное поле), `article`/SKU, choice-поля
(`fuel_type`/`transmission`/`condition`/`availability`/`currency` — уже через gettext),
`button_url`, `vin`, цены, изображения; и пользовательские данные/снимки (см. Не-цели).

## Дизайн

### 1. Регистрация и админка
- `translation.py` в каждом из трёх приложений с `TranslationOptions` для перечисленных полей.
- Существующие `ModelAdmin` (catalog/content/vacancies) переводятся на
  `modeltranslation.admin.TranslationAdmin` (вкладки EN/UK), как уже сделано у `SiteSettings`.
  Сохранить текущие `list_display`, `list_filter`, `fieldsets`, inlines, действия.
  Inlines с переводимыми полями (`ProductImage`/`ProductSpec`/`VehicleSpec`/`VacancyImage`) —
  через `TranslationStackedInline`/`TranslationTabularInline` соответственно.

### 2. Миграции
- **Схемная** (генерируется `makemigrations` после регистрации): добавляет `*_en`/`*_uk`
  колонки для всех переводимых полей (≈30 колонок), по миграции на приложение.
- **Data-миграция** (по приложению, после схемной): для каждой строки выставить
  `*_uk = <текущее базовое значение>`, `*_en` оставить пустым. Реализовать **сырым SQL**
  (`UPDATE ... SET <field>_uk = <field>`), чтобы:
  - обойти read-маскинг `SummernoteTextField.from_db_value` (см. [[summernote-readmask]]),
    скопировав точные хранимые значения;
  - не зависеть от исторических модель-классов modeltranslation/summernote в миграциях.
  Базовую колонку не трогаем (modeltranslation отдаёт значение через дескриптор с fallback).
  Reverse — noop.

### 3. Санитайзер rich-text (взаимодействие с ремедиацией)
- Сейчас `save()` у `News`/`Promo`/`Vacancy` санитизирует только базовое rich-text поле
  (`self.content = sanitize_html(self.content)` и т.д.).
- После регистрации перевода `save()` должен прогонять `bleach` по **всем зарегистрированным
  языковым вариантам** санитизируемых полей (`content_en`, `content_uk`, `description_en`, …).
- Реализация: в `save()` для каждого санитизируемого поля получить список его переводных
  атрибутов (через `modeltranslation` хелпер или явный перечень `(_en, _uk)`) и санитизировать
  каждый ненулевой; затем `super().save()`.

### 4. Slug и choices
- `slug` остаётся одиночным (один URL на запись). Не регистрируется.
- Choice-метки уже локализуются через gettext (2a) — не трогаем.

## Тестирование (в Docker)
- **Регистрация:** у `Product`/`News`/`Vacancy`/… присутствуют `*_en` и `*_uk`;
  под активным `uk` `obj.name` отдаёт украинское значение; под `en` при пустом `_en` —
  fallback на `_uk` (украинский).
- **Data-миграция:** на тестовой записи после миграции `field_uk` == исходное значение,
  `field_en` == "" (для rich-text — точная копия без потери).
- **Санитайзер:** `<script>`/обработчики вырезаются и в `content_en`, и в `content_uk` на `save()`
  (проверять in-memory экземпляр — read-маскинг иначе скрывает результат, см. [[summernote-readmask]]).
- **Регресс:** полный сьют, `manage.py check`, `makemigrations --check --dry-run` (6 приложений) —
  зелёные; `compilemessages` не затрагивается.

## Критерии приёмки
- Все перечисленные поля переводимы; админка показывает вкладки EN/UK.
- Существующий украинский контент сохранён в `_uk`; `_en` пуст; фронтенд под `en` показывает
  украинский через fallback, под `uk` — украинский; после заполнения `_en` показывает английский.
- rich-text санитизируется на обоих языках.
- Нет регрессий: сьют/`check`/`makemigrations --check` зелёные.

## Риски
- **modeltranslation + SummernoteTextField в исторических моделях миграций** — поэтому
  data-миграция использует сырой SQL, а не ORM-доступ к полям.
- **Объём схемных колонок** (≈30) — одна аккуратная миграция на приложение; проверить, что
  `makemigrations` не тянет посторонних изменений.
- **inlines с переводимыми полями** требуют `Translation*Inline`, иначе вкладки не появятся —
  покрыть в задаче по админке.
- **Существующие тесты**, создающие контент (`Brand.objects.create(name=...)` и т.п.), должны
  продолжать работать: базовый аксессор и `create(name=...)` пишут в активный язык; под `en`
  (тестовый дефолт) это пишет в `name_en`. Проверить, что фикстуры тестов не сломались.
