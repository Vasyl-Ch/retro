# Временный публичный доступ к сайту (туннель)

Как дать людям в интернете потестить сайт прямо с вашего компьютера, **без деплоя
на сервер и без переноса БД**. Сайт поднимается в Docker (dev-стек), а наружу
прокидывается HTTPS-туннель. Тестеры видят ваши локальные данные и медиа.

> Скрипт-обёртка: [`share-test.ps1`](../share-test.ps1) в корне репозитория.
> Он поднимает/переиспользует стек, создаёт суперадмина и сам пробует туннели
> по очереди: **Cloudflare → localtunnel → ngrok**.

---

## 1. Что установить на машине-«сервере»

Это компьютер, на котором будет крутиться Docker и туннель. Должен быть включён,
пока идёт тест.

### 1.1 Docker Desktop (обязательно)

```powershell
winget install -e --id Docker.DockerDesktop
```

После установки:
1. **Перезагрузить** компьютер.
2. Запустить **Docker Desktop**, дождаться статуса *Engine running* (зелёный значок).

Если не установлен WSL2 (Docker на Windows требует его):

```powershell
wsl --install
```

### 1.2 Git (для переноса проекта на машину)

```powershell
winget install -e --id Git.Git
```

### 1.3 Инструмент туннеля (минимум один)

Скрипт пробует их в порядке Cloudflare → localtunnel → ngrok. Достаточно **одного**.

**Cloudflare Tunnel — рекомендуется** (без регистрации, стабильный HTTPS):

```powershell
winget install -e --id Cloudflare.cloudflared
```

**ngrok** (нужен бесплатный аккаунт + токен):

```powershell
winget install -e --id ngrok.ngrok
ngrok config add-authtoken <ваш_токен_с_dashboard.ngrok.com>
```

**localtunnel** (запускается через `npx`, отдельно ставить не нужно — но требует Node.js):

```powershell
winget install -e --id OpenJS.NodeJS.LTS
```

> Node.js нужен **только** для localtunnel. Для Cloudflare он не требуется —
> фронтенд собирается внутри Docker-контейнера.

### Проверка готовности

```powershell
docker --version          # Docker установлен
cloudflared --version     # туннель установлен (или ngrok --version)
```

---

## 2. Настройка проекта

Уже настроено в репозитории — отдельных действий не требуется:

- [`.env.dev`](../.env.dev) — в `ALLOWED_HOSTS` добавлены туннельные домены
  (`.trycloudflare.com`, `.ngrok-free.app`, `.loca.lt`), поэтому Django не отдаёт
  `400 Bad Request` на туннельный хост.
- [`development.py`](../distributor/config/settings/development.py) — в
  `CSRF_TRUSTED_ORIGINS` прописаны те же домены (нужно для входа в `/admin`
  через HTTPS).

Учётные данные суперадмина задаются вверху скрипта `share-test.ps1`
(по умолчанию `admin` / `AdaTest12345!`). Поменяйте при необходимости.

---

## 3. Запуск

```powershell
cd <папка-проекта>

# первый раз — с пересборкой образов:
.\share-test.ps1 -Build

# далее — просто (переиспользует уже поднятый стек, НЕ пересоздаёт с нуля):
.\share-test.ps1
```

Если PowerShell блокирует выполнение скриптов:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Что делает скрипт

1. Проверяет, поднят ли dev-стек; если да — переиспользует, иначе `docker compose up -d`.
2. Ждёт, пока сайт ответит на `http://localhost:8000`.
3. Идемпотентно создаёт/обновляет суперпользователя.
4. Пробует туннели по очереди, берёт первый сработавший.
5. Печатает: **публичный URL**, **ссылку в админку**, **логин/пароль/почту**.

Туннель живёт, пока открыто окно со скриптом. `Ctrl+C` гасит туннель
(контейнеры при этом продолжают работать).

---

## 4. Полезные команды

```powershell
# Логи веб-контейнера
docker compose -f docker-compose.dev.yml logs -f web

# Остановить контейнеры (данные БД сохраняются)
docker compose -f docker-compose.dev.yml stop

# Остановить и удалить контейнеры (данные БД сохраняются в volume)
docker compose -f docker-compose.dev.yml down

# ВНИМАНИЕ: удалить контейнеры ВМЕСТЕ с данными БД
docker compose -f docker-compose.dev.yml down -v
```

---

## 5. Частые проблемы

**`400 Bad Request` / DisallowedHost при заходе по туннелю**
Туннельный домен не попал в `ALLOWED_HOSTS`. Проверьте `.env.dev` и перезапустите
веб-контейнер: `docker compose -f docker-compose.dev.yml restart web`.

**Не пускает в `/admin` — ошибка CSRF**
Домен туннеля должен быть в `CSRF_TRUSTED_ORIGINS` (см. `development.py`).
Для ngrok/localtunnel домен меняется при каждом запуске — wildcard-записи это покрывают.

**localtunnel просит пароль на странице-заглушке**
Это ваш публичный IP. Узнать:
```powershell
(Invoke-WebRequest https://loca.lt/mytunnelpassword).Content
```

**Ни один туннель не поднялся**
Установите хотя бы один инструмент (см. п. 1.3). Локально сайт всё равно доступен
на `http://localhost:8000/admin/`.

---

## 6. Ограничения

- Сайт доступен, **только пока включён ПК** и открыто окно со скриптом.
- На бесплатных тарифах Cloudflare/ngrok **домен меняется** при каждом запуске.
- Это **dev-режим** (`DEBUG=True`) — годится для теста в узком кругу,
  но не для публичного продакшена.
- Скорость зависит от вашего интернет-канала (особенно отдачи/upload).
```
