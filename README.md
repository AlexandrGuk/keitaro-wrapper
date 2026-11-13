# Обёртка над Keitaro

Локальный UI над Keitaro Admin API: создание кампаний и редактор офферов в потоках. Keitaro — источник правды. Локальная SQLite хранит только черновики редактора (доли, закрепления, удалённые офферы) до публикации.

## Что умеет

- **Создание кампании** с префиксом `test_guk_` (в поле — хвост: `campaign1` → `test_guk_campaign1`).
- Ротация по позиции, привязка домена / группы / источника (домен и источник опциональны).
- **Поток 1** — фильтр по ГЕО (можно несколько через запятую) → `https://google.com`.
- **Поток 2** — оффер со долей 100%.
- **Редактор**: доли (сумма 100), pin, add/remove/restore, Fetch / Push / Cancel, жёлтая рамка для неопубликованных правок.
- Stats и Trends за 7 дней, скелетоны загрузки, удаление кампании.
- Вход по сессии (`APP_USERNAME` / `APP_PASSWORD`).

Список кампаний показывает только префикс `test_guk_`.

## Требования

- Python 3.11+
- URL трекера без хвоста `/admin` и API key из Keitaro → профиль → API keys

## OneClick

Из корня репозитория.

```bash
chmod +x scripts/*.sh
./scripts/install.sh
./scripts/start.sh
```

Открыть http://127.0.0.1:8000

`install` создаёт venv, ставит зависимости, копирует `.env` из примера (если его ещё нет) и накатывает миграции. Перед первым входом заполни `backend/.env`.

Windows (PowerShell), если нужно локально:

```powershell
.\scripts\install.ps1
.\scripts\start.ps1
```

## Конфиг `backend/.env`

```
KEITARO_BASE_URL=https://tracker.example.com
KEITARO_API_KEY=
CAMPAIGN_PREFIX=test_guk_
APP_USERNAME=guk
APP_PASSWORD=
SESSION_SECRET=
SESSION_HTTPS=false
```

| Переменная | Назначение |
|---|---|
| `KEITARO_BASE_URL` | База админки без `/admin` |
| `KEITARO_API_KEY` | Ключ Admin API |
| `CAMPAIGN_PREFIX` | Префикс имён кампаний |
| `APP_USERNAME` / `APP_PASSWORD` | Логин формы входа |
| `SESSION_SECRET` | Секрет cookie-сессии |
| `SESSION_HTTPS` | `true` за HTTPS-прокси |

Сброс локальной БД: удалить `backend/data/app.db` и снова `./scripts/install.sh` (или `alembic upgrade head` в venv).

## Тесты

```bash
cd backend
source .venv/bin/activate
pytest
```

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

## Стек

FastAPI + SQLAlchemy + Alembic (SQLite), vanilla HTML/JS/CSS.
