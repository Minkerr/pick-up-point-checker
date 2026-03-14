# Pick-Up Point Checker

Сервис для проверки условий открытия ПВЗ по адресу/координатам.
На старте агрегирует **Ozon** и **Wildberries**; архитектура рассчитана на лёгкое добавление новых маркетплейсов.

## Структура проекта

```
pick-up-point-checker/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI-приложение, точка входа
│   │   ├── config.py        # Настройки (pydantic-settings, .env)
│   │   ├── schemas.py       # Pydantic-схемы запросов/ответов
│   │   ├── geocoder.py      # Геокодирование: адрес → lat/lon
│   │   ├── analyzer.py      # Агрегатор: запускает стратегии параллельно
│   │   └── strategies/
│   │       ├── base.py      # Абстрактный базовый класс стратегии
│   │       ├── ozon.py      # Стратегия для Ozon
│   │       └── wb.py        # Стратегия для Wildberries
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
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # при необходимости отредактируй

uvicorn app.main:app --reload
# → http://127.0.0.1:8000
```

### Фронтенд (MVP — статика)

```bash
cd frontend
python -m http.server 8080
# → http://127.0.0.1:8080
```

## API

### `GET /api/check-location`

| Параметр  | Тип    | Описание              |
|-----------|--------|-----------------------|
| `address` | string | Адрес для проверки    |

**Пример запроса:**
```
GET /api/check-location?address=г.+Санкт-Петербург,+Невский+проспект+1
```

**Пример ответа:**
```json
{
  "coordinates": { "lat": 59.9, "lon": 30.3 },
  "ozon": {
    "status": "approved",
    "tariff": 10.0,
    "financial_support": 2880000
  },
  "wb": {
    "status": "approved",
    "tariff": 4.74,
    "financial_support": 284400
  }
}
```

Поле `status`: `approved` | `denied` | `limited` | `error`

## Геокодер

По умолчанию используется **Nominatim** (OpenStreetMap, бесплатно).  
Для лучшего качества по российским адресам можно переключиться на **Яндекс Геокодер**:

```env
# .env
GEOCODER_PROVIDER=yandex
YANDEX_GEOCODER_API_KEY=ваш_ключ
```

## Добавление нового маркетплейса

1. Создай `backend/app/strategies/yandex_market.py`, унаследуй `BaseStrategy`, реализуй метод `check`.
2. Добавь экземпляр в список `STRATEGIES` в `analyzer.py`.
3. Добавь поле в `CheckLocationResponse` в `schemas.py` и верни значение из эндпоинта.
