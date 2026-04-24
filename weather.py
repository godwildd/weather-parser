import urllib.request
import json
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode())


def geocode(city: str) -> tuple[float, float, str]:
    url = (
        "https://nominatim.openstreetmap.org/search"
        f"?q={urllib.parse.quote(city)}&format=json&limit=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "weather-parser/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if not data:
        raise ValueError(f"Город не найден: {city!r}")
    result = data[0]
    return float(result["lat"]), float(result["lon"]), result["display_name"]


def get_weather(lat: float, lon: float) -> dict:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        "weather_code,wind_speed_10m,wind_direction_10m,precipitation"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"
        "&timezone=auto&forecast_days=5"
    )
    return fetch_json(url)


WMO_CODES = {
    0: "Ясно", 1: "Преим. ясно", 2: "Переменная облачность", 3: "Пасмурно",
    45: "Туман", 48: "Туман с изморозью",
    51: "Слабая морось", 53: "Морось", 55: "Сильная морось",
    61: "Слабый дождь", 63: "Дождь", 65: "Сильный дождь",
    71: "Слабый снег", 73: "Снег", 75: "Сильный снег",
    77: "Снежная крупа", 80: "Ливень", 81: "Сильный ливень", 82: "Шквальный ливень",
    85: "Снежный ливень", 86: "Сильный снежный ливень",
    95: "Гроза", 96: "Гроза с градом", 99: "Гроза с сильным градом",
}

WIND_DIRS = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]


def wind_dir(deg: float) -> str:
    return WIND_DIRS[round(deg / 45) % 8]


def print_weather(city_input: str) -> None:
    import urllib.parse  # noqa: needed here after geocode import

    print(f"\nПолучаю данные для: {city_input!r} ...")
    lat, lon, full_name = geocode(city_input)
    print(f"Найдено: {full_name}")
    data = get_weather(lat, lon)

    cur = data["current"]
    tz = data.get("timezone", "")

    print(f"\n{'─'*50}")
    print(f"  Текущая погода  ({cur['time']}  {tz})")
    print(f"{'─'*50}")
    print(f"  Температура      : {cur['temperature_2m']} °C  (ощущается {cur['apparent_temperature']} °C)")
    print(f"  Влажность        : {cur['relative_humidity_2m']} %")
    print(f"  Осадки           : {cur['precipitation']} мм")
    print(f"  Ветер            : {cur['wind_speed_10m']} км/ч  {wind_dir(cur['wind_direction_10m'])}")
    print(f"  Описание         : {WMO_CODES.get(cur['weather_code'], cur['weather_code'])}")

    daily = data["daily"]
    print(f"\n{'─'*50}")
    print("  Прогноз на 5 дней")
    print(f"{'─'*50}")
    print(f"  {'Дата':<12} {'Мин':>6} {'Макс':>6} {'Осадки':>8}  Погода")
    for i, date in enumerate(daily["time"]):
        desc = WMO_CODES.get(daily["weather_code"][i], str(daily["weather_code"][i]))
        precip = daily["precipitation_sum"][i]
        t_min = daily["temperature_2m_min"][i]
        t_max = daily["temperature_2m_max"][i]
        print(f"  {date:<12} {t_min:>5}°C {t_max:>5}°C {precip:>6} мм  {desc}")
    print()


import urllib.parse  # noqa: module-level import after function defs


if __name__ == "__main__":
    city = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Москва"
    try:
        print_weather(city)
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка сети: {e}", file=sys.stderr)
        sys.exit(1)
