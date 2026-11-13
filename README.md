# Обёртка над Keitaro

Локальный UI над Keitaro Admin API: создание кампаний и редактор офферов в потоках. Keitaro — источник правды. Локальная SQLite хранит только черновики редактора (доли, закрепления, удалённые офферы) до публикации.

## Быстрый старт

```bash
chmod +x scripts/*.sh
./scripts/install.sh
```

В `backend/.env` укажи трекер и API key (см. ниже). Затем:

```bash
./scripts/start.sh
```

Открой http://127.0.0.1:8000

**Логин формы входа:** `guk` / `keitaro`  
(значения `APP_USERNAME` / `APP_PASSWORD` из `backend/.env.example`, копируются в `.env` при install.)

## Что умеет

- Создание кампании с префиксом `test_guk_` (в поле — хвост: `campaign1` → `test_guk_campaign1`).
- Ротация по позиции, привязка домена / группы / источника (домен и источник опциональны).
- **Поток 1** — фильтр по ГЕО (можно несколько через запятую) → `https://google.com`.
- **Поток 2** — оффер со долей 100%.
- Редактор: доли (сумма 100), pin, add/remove/restore, Fetch / Push / Cancel, жёлтая рамка для неопубликованных правок.
- Stats и Trends за 7 дней, скелетоны загрузки, удаление кампании.

Список кампаний показывает только префикс `test_guk_`.

## Требования

- Python 3.11+
- URL трекера **без** хвоста `/admin`
- API key: Keitaro → профиль → API keys

## Конфиг `backend/.env`

`install.sh` создаёт файл из `.env.example`, если его ещё нет.

```
KEITARO_BASE_URL=https://tracker.example.com
KEITARO_API_KEY=
CAMPAIGN_PREFIX=test_guk_
APP_USERNAME=guk
APP_PASSWORD=keitaro
SESSION_SECRET=dev-secret-change-me
SESSION_HTTPS=false
```

| Переменная | Назначение |
|---|---|
| `KEITARO_BASE_URL` | База админки без `/admin` |
| `KEITARO_API_KEY` | Ключ Admin API |
| `CAMPAIGN_PREFIX` | Префикс имён кампаний |
| `APP_USERNAME` / `APP_PASSWORD` | Логин формы входа (по умолчанию `guk` / `keitaro`) |
| `SESSION_SECRET` | Секрет cookie-сессии |
| `SESSION_HTTPS` | `true` только за HTTPS-прокси |

Сброс локальной БД: удалить `backend/data/app.db` и снова `./scripts/install.sh`.

## Тесты

```bash
cd backend
source .venv/bin/activate
pytest
```

## Стек

FastAPI + SQLAlchemy + Alembic (SQLite), vanilla HTML/JS/CSS.
