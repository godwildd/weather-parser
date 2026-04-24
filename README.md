# Weather Parser

Простой парсер погоды на Python с CLI и графическим интерфейсом.

Использует бесплатные API без регистрации:
- **[Open-Meteo](https://open-meteo.com/)** — данные о погоде
- **[Nominatim](https://nominatim.openstreetmap.org/)** (OpenStreetMap) — геокодирование городов

## Возможности

- Текущая погода: температура, ощущаемая температура, влажность, ветер, осадки
- Прогноз на 7 дней
- Поиск любого города мира
- Два режима: CLI и GUI с тёмной темой

## Требования

- Python 3.10+
- Стандартная библиотека (tkinter, urllib, json) — сторонние пакеты не нужны

## Запуск

**Графический интерфейс:**
```bash
python weather_gui.py
```

**Командная строка:**
```bash
python weather.py "Москва"
python weather.py "Лондон"
python weather.py "New York"
```

По умолчанию (без аргумента) показывает Москву.

## Скриншот

> _GUI загружает погоду автоматически при запуске_

## Структура

```
weather.py      — CLI-версия
weather_gui.py  — GUI на tkinter
```
