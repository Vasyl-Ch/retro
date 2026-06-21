# Distributor — конфигурируемый мульти-вертикальный сайт

Django (backend) + Vite/Tailwind/Tailus (frontend). Один шаблон, который переключается между
вертикалями через **пресеты**: `distributor`, `auto` (автосалон), `food` (ресторан),
`shop` (магазин с корзиной), `generic`. Внешний вид, термины, меню, hero, брендинг админки и
доступные блоки задаются в админке (раздел «Налаштування сайту»).

- `ada-frontend/` — Vite + Tailwind + Tailus (сборка в `distributor/static/ada/`)
- `distributor/` — Django: `apps/` (catalog, content, vacancies, contacts, orders, core), `config/`, `templates/`

---

## Быстрый старт (Docker, разработка)

Требуется Docker Desktop + Docker Compose v2.

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Открыть в браузере:

- **Сайт:** http://localhost:8000
- **Админка:** http://localhost:8000/admin/

Первичное наполнение (один раз, в отдельном терминале):

```bash
# суперпользователь для админки
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# применить пресет вертикали (auto / shop / food / distributor / generic)
docker compose -f docker-compose.dev.yml exec web python manage.py apply_preset auto

# справочник марок авто (для пресета auto)
docker compose -f docker-compose.dev.yml exec web python manage.py seed_car_makes
```

> Внутри контейнера `web` уже задан `DJANGO_SETTINGS_MODULE=config.settings.development`,
> поэтому флаг `--settings` указывать не нужно.

---

## Полезные команды

```bash
# логи
docker compose -f docker-compose.dev.yml logs -f web

# остановить
docker compose -f docker-compose.dev.yml down

# остановить и УДАЛИТЬ данные БД (тома)
docker compose -f docker-compose.dev.yml down -v

# миграции
docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations
docker compose -f docker-compose.dev.yml exec web python manage.py migrate

# пересобрать фронтенд после правок шаблонов/JS/CSS
docker compose -f docker-compose.dev.yml exec web \
  sh -c "cd /ada-frontend && npm run build:django && cp -r /distributor/static/ada/. /app/static/ada/"

# тесты
docker compose -f docker-compose.dev.yml exec web python manage.py test
```

Сменить вертикаль можно в админке (**Налаштування сайту** → кнопки пресетов) либо командой
`apply_preset <name>`.

---

## Запустить второй стек рядом (другое имя + своя БД + свои порты)

Имя проекта Compose задаётся в `docker-compose.dev.yml` (`name: ada-html`) и переопределяется
флагом `-p`. Отдельный проект = отдельные контейнеры, сеть и тома (то есть **отдельная БД**).
Порты параметризованы (`WEB_PORT`, `DB_PORT`).

**PowerShell:**

```powershell
$env:WEB_PORT="8001"; $env:DB_PORT="5433"
docker compose -p ada-html-2 -f docker-compose.dev.yml up -d --build
```

**Bash:**

```bash
WEB_PORT=8001 DB_PORT=5433 docker compose -p ada-html-2 -f docker-compose.dev.yml up -d --build
```

Второй сайт будет на **http://localhost:8001** (БД на :5433), основной `ada-html` продолжит
работать на :8000. У клона **пустая БД** — наполни её (`createsuperuser`, `apply_preset`,
`seed_car_makes`), указывая тот же `-p ada-html-2` во всех командах. Управление клоном —
тоже с `-p` (например `docker compose -p ada-html-2 -f docker-compose.dev.yml down`).

---

## Подробнее

Локальный запуск без Docker и деплой в production — см. **[docs/RUNNING.md](docs/RUNNING.md)**.

---

Frontend основан на шаблоне [Ada](https://github.com/Tailus-UI) (Tailwind + Tailus Themer).
