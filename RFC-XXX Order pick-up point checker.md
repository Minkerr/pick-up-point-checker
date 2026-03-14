#inbox 

**Status:** Draft
**Authors:** Valentin Mirontsev
**Feedback Deadline:** 09.03.2026
**Last Update Date:** 09.03.2026

#### Need (Context / Problem)
Представь, что я хочу открыть ПВЗ, нашёл адрес под аренду и пытаюсь понять, выгодно ли здесь его открывать. Нужно создать сервис, который мне в этом сможет помочь.
У всех основных маркетплейсов - есть карты, где можно ввести адрес и узнать какие условия будут, если открыть ПЗВ здесь.

#### Approach
Делаем единый интерфейс, для анализа точек для открытия пвз разных маркетплейсов 
МВП: агрегируем Озон и Вайлдберрис. 
Делаем возможность масштабирования, в перспективе добавляем Яндекс Маркет и другие.

Сценарий:
Юзер вводит адрес / координаты. (это мпв, следущий шаг прикрутить апи с картами). 
Получает значения тарифа и поддержи от Озона и ВБ соответсвенно

#### Alternatives (and why aren’t they the chosen one)
https://map.wb.ru/
https://pvz.ozon.ru/
нужно стыковать информацию с двух разных сервисов

#### Architecture

Client Frontend    --address-->   Backend

Backend:
1. Geocoder. Перевод адреса в координаты: address -> lat+lon
2. Analyzer. Для координат перебирает стратегии для всех API Ozon, WB ... И агрегирует результаты
3. Strategy для API Ozon, WB ...

Frontend:
1. формочка с вводом адресом.
2. (развитие после мвп) OpenStreetMap API / Yandex Map API для показа карты и выбора точки на ней

#### API Contract

**Endpoint:** `GET /api/check-location`
**Request:**
`{   "address": "г. Санкт-Петербург, Невский проспект 1" }`
**Response:**
```
{   
	"coordinates": {"lat": 59.9, "lon": 30.3},   
	"ozon": {     
		"status": "approved",   
		"tariff": 5.0,     
		"financial_support": 2000000   
	},   
	"wb": {     
		"status": "limited",     
		"tariff": 2.5,     
		"financial_support": 200000    
	} 
}
```

`

#### Update Log:


[[ПИ]]