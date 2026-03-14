# Pick-Up Point Checker

Сервис для проверки условий открытия ПВЗ по адресу/координатам.
Агрегирует **Ozon**, **Wildberries** и **Яндекс Маркет**; архитектура рассчитана на лёгкое добавление новых маркетплейсов.

## Структура проекта

```
pick-up-point-checker/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI-приложение, точка входа
│   │   ├── config.py        # Настройки (pydantic-settings, .env)
│   │   ├── schemas.py       # Pydantic-схемы запросов/ответов
│   │   ├── geocoder.py      # Геокодирование: адрес → lat/lon (Nominatim)
│   │   ├── analyzer.py      # Агрегатор: запускает стратегии параллельно
│   │   └── strategies/
│   │       ├── base.py           # Абстрактный базовый класс стратегии
│   │       ├── ozon.py           # Стратегия для Ozon
│   │       ├── wb.py             # Стратегия для Wildberries
│   │       └── yandex_market.py  # Стратегия для Яндекс Маркет
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

## Быстрый старт

### Бэкенд

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # заполни OZON_COOKIE (см. .env.example)

uvicorn app.main:app --reload
# → http://127.0.0.1:8000
```

### Фронтенд

```bash
cd frontend
python3 -m http.server 8080
# → http://127.0.0.1:8080
```

### Остановить всё

```bash
lsof -ti :8000 -ti :8080 | xargs kill -9
```

## API

### `GET /api/check-location`

| Параметр  | Тип    | Описание                                      |
|-----------|--------|-----------------------------------------------|
| `address` | string | Адрес для проверки (геокодируется через Nominatim) |
| `lat`     | float  | Широта (альтернатива address)                 |
| `lon`     | float  | Долгота (альтернатива address)                |

Нужно передать либо `address`, либо `lat` + `lon`.

**Пример запроса:**
```
GET /api/check-location?address=г.+Санкт-Петербург,+Невский+проспект+1
GET /api/check-location?lat=59.9&lon=30.3
```

**Пример ответа:**
```json
{
  "coordinates": { "lat": 59.9, "lon": 30.3 },
  "ozon": {
    "status": "approved",
    "tariff": 10.0,
    "financial_support": 2880000,
    "financial_support_label": "за 273 дней (итого по программе)",
    "extra_fields": [...]
  },
  "wb": {
    "status": "approved",
    "tariff": 4.74,
    "financial_support": 284400,
    "financial_support_label": "в месяц (вознаграждение)",
    "extra_fields": [...]
  },
  "yandex_market": {
    "status": "approved",
    "financial_support": 200000,
    "financial_support_label": "в месяц",
    "extra_fields": [...]
  }
}
```

Поле `status`: `approved` | `denied` | `limited` | `error`

## Добавление нового маркетплейса

1. Создай `backend/app/strategies/<name>.py`, унаследуй `BaseStrategy`, реализуй метод `check`.
2. Добавь экземпляр в список `STRATEGIES` в `analyzer.py`.
3. Добавь поле в `CheckLocationResponse` в `schemas.py` и верни значение из эндпоинта.
