#requires -Version 5.1
<#
.SYNOPSIS
    Поднимает dev-стек в Docker Compose и открывает публичный HTTPS-туннель,
    чтобы дать людям в сети потестить сайт с вашими локальными данными/медиа.

.DESCRIPTION
    - Если стек уже запущен — переиспользует его (НЕ пересоздаёт с нуля).
    - Гарантирует наличие суперпользователя (идемпотентно: при повторе только
      обновляет пароль, не падает).
    - Пробует туннели по очереди: cloudflared -> localtunnel -> ngrok.
    - Печатает публичный URL, ссылку в админку и логин/пароль/почту суперадмина.

.PARAMETER Build
    Принудительно пересобрать образы (docker compose up -d --build).

.EXAMPLE
    ./share-test.ps1
    ./share-test.ps1 -Build
#>
param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------
$Compose      = @("compose", "-f", "docker-compose.dev.yml")
$WebService   = "web"
$LocalUrl     = "http://localhost:8000"
$LocalPort    = "8000"

# Учётные данные суперадмина (поменяйте при желании)
$AdminUser    = "admin"
$AdminEmail   = "admin@ada-test.local"
$AdminPass    = "AdaTest12345!"

# ---------------------------------------------------------------------------
# 1. Поднять/переиспользовать стек
# ---------------------------------------------------------------------------
Write-Host "==> Проверяю состояние Docker Compose стека..." -ForegroundColor Cyan

$running = & docker @Compose ps --services --filter "status=running" 2>$null

if ($running -contains $WebService -and -not $Build) {
    Write-Host "    Стек уже запущен — переиспользую (пересборки нет)." -ForegroundColor Green
} else {
    if ($Build) {
        Write-Host "    Запускаю с пересборкой (--build)..." -ForegroundColor Yellow
        & docker @Compose up -d --build
    } else {
        Write-Host "    Поднимаю стек (up -d)..." -ForegroundColor Yellow
        & docker @Compose up -d
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "docker compose up завершился с ошибкой."
        exit 1
    }
}

# ---------------------------------------------------------------------------
# 2. Дождаться готовности веб-сервера
# ---------------------------------------------------------------------------
Write-Host "==> Жду, пока сайт ответит на $LocalUrl ..." -ForegroundColor Cyan
$ready = $false
$deadline = (Get-Date).AddSeconds(240)
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri $LocalUrl -UseBasicParsing -TimeoutSec 5 -MaximumRedirection 0 -ErrorAction Stop
        $ready = $true; break
    } catch {
        # 3xx/4xx тоже означают, что сервер жив
        if ($_.Exception.Response -ne $null) { $ready = $true; break }
    }
    Start-Sleep -Seconds 3
}
if (-not $ready) {
    Write-Warning "Сайт не ответил за 4 минуты. Логи: docker compose -f docker-compose.dev.yml logs -f web"
} else {
    Write-Host "    Сайт отвечает." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 3. Гарантировать суперпользователя (идемпотентно, через stdin shell)
# ---------------------------------------------------------------------------
Write-Host "==> Создаю/обновляю суперпользователя '$AdminUser'..." -ForegroundColor Cyan

$pySnippet = @"
from django.contrib.auth import get_user_model
U = get_user_model()
u, created = U.objects.get_or_create(
    username='$AdminUser',
    defaults={'email': '$AdminEmail', 'is_staff': True, 'is_superuser': True},
)
u.email = '$AdminEmail'
u.is_staff = True
u.is_superuser = True
u.set_password('$AdminPass')
u.save()
print('SUPERUSER_CREATED' if created else 'SUPERUSER_UPDATED')
"@

# Передаём код в `manage.py shell` через stdin — без проблем с кавычками.
$pySnippet | & docker @Compose exec -T $WebService python manage.py shell | ForEach-Object {
    if ($_ -match "SUPERUSER_(CREATED|UPDATED)") {
        Write-Host "    Суперадмин $($Matches[1].ToLower())." -ForegroundColor Green
    }
}

# ---------------------------------------------------------------------------
# 4. Туннели — пробуем по очереди
# ---------------------------------------------------------------------------
function Start-Tunnel {
    param(
        [string]$Name,
        [string]$Exe,
        [string[]]$ArgList,
        [string]$UrlRegex,
        [int]$TimeoutSec = 35
    )

    $cmd = Get-Command $Exe -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "    [$Name] не найден ($Exe) — пропускаю." -ForegroundColor DarkGray
        return $null
    }

    Write-Host "    [$Name] запускаю..." -ForegroundColor Yellow
    $outFile = [System.IO.Path]::GetTempFileName()
    $errFile = [System.IO.Path]::GetTempFileName()

    $proc = Start-Process -FilePath $cmd.Source -ArgumentList $ArgList `
        -NoNewWindow -PassThru `
        -RedirectStandardOutput $outFile -RedirectStandardError $errFile

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if ($proc.HasExited) { break }
        $text = ""
        try { $text += (Get-Content $outFile -Raw -ErrorAction SilentlyContinue) } catch {}
        try { $text += (Get-Content $errFile -Raw -ErrorAction SilentlyContinue) } catch {}
        if ($text -match $UrlRegex) {
            return [pscustomobject]@{
                Name = $Name; Url = $Matches[0]; Process = $proc
                OutFile = $outFile; ErrFile = $errFile
            }
        }
        Start-Sleep -Milliseconds 800
    }

    Write-Host "    [$Name] не выдал URL за $TimeoutSec c — пробую следующий." -ForegroundColor DarkYellow
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    return $null
}

Write-Host "==> Поднимаю публичный туннель..." -ForegroundColor Cyan

$tunnel = $null

# 1) Cloudflare Tunnel — без регистрации, стабильнее всего
$tunnel = Start-Tunnel -Name "cloudflared" -Exe "cloudflared" `
    -ArgList @("tunnel", "--url", $LocalUrl) `
    -UrlRegex "https://[a-z0-9-]+\.trycloudflare\.com"

# 2) localtunnel (через npx) — нужен только Node.js
if (-not $tunnel) {
    $tunnel = Start-Tunnel -Name "localtunnel" -Exe "npx" `
        -ArgList @("--yes", "localtunnel", "--port", $LocalPort) `
        -UrlRegex "https://[a-z0-9-]+\.loca\.lt"
}

# 3) ngrok — нужен настроенный authtoken
if (-not $tunnel) {
    $tunnel = Start-Tunnel -Name "ngrok" -Exe "ngrok" `
        -ArgList @("http", $LocalPort, "--log=stdout") `
        -UrlRegex "https://[a-z0-9-]+\.ngrok[a-z0-9.-]*\.app"
}

# ---------------------------------------------------------------------------
# 5. Итог
# ---------------------------------------------------------------------------
""
Write-Host "============================================================" -ForegroundColor Magenta
if ($tunnel) {
    $adminUrl = $tunnel.Url.TrimEnd("/") + "/admin/"
    Write-Host " ГОТОВО — сайт доступен через [$($tunnel.Name)]" -ForegroundColor Green
    Write-Host "------------------------------------------------------------"
    Write-Host " Публичный URL :  $($tunnel.Url)"
    Write-Host " Админка       :  $adminUrl"
    Write-Host "------------------------------------------------------------"
    Write-Host " Суперадмин логин :  $AdminUser"
    Write-Host " Пароль           :  $AdminPass"
    Write-Host " Почта            :  $AdminEmail"
    Write-Host "============================================================" -ForegroundColor Magenta
    ""
    if ($tunnel.Name -eq "localtunnel") {
        Write-Host "NB: localtunnel может показать страницу-заглушку с просьбой ввести пароль —" -ForegroundColor Yellow
        Write-Host "    это ваш публичный IP (узнать: (Invoke-WebRequest https://loca.lt/mytunnelpassword).Content)" -ForegroundColor Yellow
        ""
    }
    Write-Host "Туннель живёт, пока открыто это окно. Нажмите Ctrl+C для остановки." -ForegroundColor Cyan
    Write-Host "(Контейнеры при этом останутся работать; остановить: docker compose -f docker-compose.dev.yml stop)" -ForegroundColor DarkGray
    try {
        Wait-Process -Id $tunnel.Process.Id
    } finally {
        if (-not $tunnel.Process.HasExited) {
            Stop-Process -Id $tunnel.Process.Id -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host " Ни один туннель не поднялся." -ForegroundColor Red
    Write-Host "------------------------------------------------------------"
    Write-Host " Установите хотя бы один инструмент:"
    Write-Host "   winget install Cloudflare.cloudflared"
    Write-Host "   winget install ngrok.ngrok   (затем: ngrok config add-authtoken <токен>)"
    Write-Host "   npx localtunnel               (нужен Node.js)"
    Write-Host "------------------------------------------------------------"
    Write-Host " Локально сайт всё равно доступен: $LocalUrl/admin/"
    Write-Host " Суперадмин: $AdminUser / $AdminPass / $AdminEmail"
    Write-Host "============================================================" -ForegroundColor Magenta
    exit 1
}
