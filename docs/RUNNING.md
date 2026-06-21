# Запуск проекта Дистрибьютор

## Структура репозитория

```
ada-html/
├── ada-frontend/          # Vite + Tailwind + Tailus Themer
│   ├── assets/css/        # исходный CSS
│   ├── main.js            # точка входа + Swiper
│   ├── tailwind.config.js
│   └── vite.config.js     # outDir → ../distributor/static/ada
├── distributor/           # Django проект
│   ├── apps/              # catalog, content, vacancies, contacts, core
│   ├── config/            # settings/, urls.py, wsgi.py
│   ├── templates/         # Django HTML шаблоны
│   ├── static/ada/        # ГЕНЕРИРУЕТСЯ: npm run build:django
│   ├── media/             # загружаемые файлы (gitignore)
│   └── manage.py
├── nginx/                 # nginx конфиг для production
├── Dockerfile.dev         # Docker для разработки
├── Dockerfile.prod        # Docker для production (multi-stage)
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .env.dev               # переменные для разработки
└── .env.prod.example      # шаблон для production
```

## Вариант 1: Локальный запуск без Docker

### Требования
- Python 3.12 (рекомендуется) или 3.14
- Node.js 20+
- npm

### Шаги

```bash
# 1. Клонировать репозиторий
git clone https://github.com/VasylCherkesHYS/Landing.git
cd Landing

# 2. Сборка фронтенда
cd ada-frontend
npm install
npm run build:django
cd ..

# 3. Настройка Python окружения
cd distributor
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt

# 4. Создать .env файл
cp .env.example .env
# Отредактируй .env: задай SECRET_KEY

# 5. Миграции и тестовые данные
python manage.py migrate --settings=config.settings.development
python manage.py seed_data --settings=config.settings.development
python manage.py createsuperuser --settings=config.settings.development

# 6. Запуск
python manage.py runserver --settings=config.settings.development
```

Открой: http://127.0.0.1:8000
Админка: http://127.0.0.1:8000/admin/

### Пересборка фронтенда при изменениях шаблонов

```bash
cd ada-frontend && npm run build:django && cd ..
```

## Вариант 2: Docker — локальная разработка

### Требования
- Docker Desktop
- Docker Compose v2

### Шаги

```bash
# 1. Создать .env.dev (уже создан в репо как шаблон)
# Проверь что DB_HOST=db (не localhost)

# 2. Запуск
docker compose -f docker-compose.dev.yml up --build

# 3. В отдельном терминале — создать суперпользователя
docker compose -f docker-compose.dev.yml exec web \
  python manage.py createsuperuser \
  --settings=config.settings.development

# 4. Загрузить тестовые данные
docker compose -f docker-compose.dev.yml exec web \
  python manage.py seed_data \
  --settings=config.settings.development
```

Открой: http://localhost:8000
Админка: http://localhost:8000/admin/

### Полезные команды для разработки

```bash
# Остановить
docker compose -f docker-compose.dev.yml down

# Остановить и удалить данные БД
docker compose -f docker-compose.dev.yml down -v

# Логи
docker compose -f docker-compose.dev.yml logs -f web

# Выполнить команду в контейнере
docker compose -f docker-compose.dev.yml exec web \
  python manage.py makemigrations --settings=config.settings.development
```

## Вариант 3: Docker — деплой на сервер (production)

### Требования к серверу
- Ubuntu 22.04 LTS
- Docker Engine 24+
- Docker Compose v2
- Домен с DNS A-записью на IP сервера

### Подготовка сервера

```bash
# Установить Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Клонировать репозиторий
git clone https://github.com/VasylCherkesHYS/Landing.git /opt/distributor
cd /opt/distributor
```

### Настройка окружения

```bash
# Создать .env.prod из шаблона
cp .env.prod.example .env.prod

# Заполнить обязательные переменные
nano .env.prod
```

Обязательные переменные в `.env.prod`:

- `SECRET_KEY` — сгенерируй: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DB_PASSWORD` — сильный пароль
- `ALLOWED_HOSTS=YOUR_DOMAIN,www.YOUR_DOMAIN`

### Настройка nginx

```bash
# Заменить yourdomain.com на свой домен
sed -i 's/yourdomain.com/YOUR_DOMAIN/g' nginx/nginx.conf
```

### Первый запуск (без SSL)

```bash
# Временно запустить только HTTP для получения сертификата
# В nginx/nginx.conf закомментировать блок server на 443
# и убрать return 301 редирект

docker compose -f docker-compose.prod.yml up -d db web nginx

# Получить SSL сертификат
docker compose -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot -w /var/www/certbot \
  -d YOUR_DOMAIN -d www.YOUR_DOMAIN \
  --email admin@YOUR_DOMAIN --agree-tos --no-eff-email

# Восстановить nginx.conf (раскомментировать SSL блок)
docker compose -f docker-compose.prod.yml restart nginx
```

### Полный запуск production

```bash
docker compose -f docker-compose.prod.yml up -d --build

# Создать суперпользователя
docker compose -f docker-compose.prod.yml exec web \
  python manage.py createsuperuser \
  --settings=config.settings.production
```

### Обновление проекта

```bash
cd /opt/distributor
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web \
  python manage.py migrate --settings=config.settings.production
```

### Резервное копирование БД

```bash
# Создать бэкап
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).sql

# Восстановить из бэкапа
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U $DB_USER $DB_NAME < backup_20240101.sql
```

### Мониторинг

```bash
# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Логи
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx

# Использование ресурсов
docker stats
```

## Переменные окружения

| Переменная     | Описание              | Пример                       |
|----------------|-----------------------|------------------------------|
| SECRET_KEY     | Django секретный ключ | 50+ случайных символов       |
| DEBUG          | Режим отладки         | True / False                 |
| DB_NAME        | Имя базы данных       | distributor                  |
| DB_USER        | Пользователь БД       | postgres                     |
| DB_PASSWORD    | Пароль БД             | strong_password              |
| DB_HOST        | Хост БД               | db (в Docker)                |
| DB_PORT        | Порт БД               | 5432                         |
| ALLOWED_HOSTS  | Допустимые хосты      | domain.com,www.domain.com    |

## Частые проблемы

**Ошибка: static files не отображаются в production**
```bash
docker compose -f docker-compose.prod.yml exec web \
  python manage.py collectstatic --noinput \
  --settings=config.settings.production
```

**Ошибка: медиафайлы недоступны**
Проверь что volume `media_prod` смонтирован в nginx как `/app/media/`.

**Ошибка: 502 Bad Gateway**
```bash
docker compose -f docker-compose.prod.yml logs web
# Обычно: миграции не применены или неверный DJANGO_SETTINGS_MODULE
```
