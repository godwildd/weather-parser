import tkinter as tk
from tkinter import ttk, messagebox
import threading
import urllib.request
import urllib.parse
import json

# ── API ───────────────────────────────────────────────────────────────────────

def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())


def geocode(city: str) -> tuple[float, float, str]:
    url = (
        "https://nominatim.openstreetmap.org/search"
        f"?q={urllib.parse.quote(city)}&format=json&limit=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "weather-gui/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
    if not data:
        raise ValueError(f"Город не найден: {city!r}")
    res = data[0]
    return float(res["lat"]), float(res["lon"]), res["display_name"]


def get_weather(lat: float, lon: float) -> dict:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        "weather_code,wind_speed_10m,wind_direction_10m,precipitation"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"
        "&timezone=auto&forecast_days=7"
    )
    return fetch_json(url)


WMO_CODES = {
    0:  ("Ясно",                    "☀"),
    1:  ("Преим. ясно",             "🌤"),
    2:  ("Переменная облачность",   "⛅"),
    3:  ("Пасмурно",                "☁"),
    45: ("Туман",                   "🌫"),
    48: ("Туман с изморозью",       "🌫"),
    51: ("Слабая морось",           "🌦"),
    53: ("Морось",                  "🌦"),
    55: ("Сильная морось",          "🌧"),
    61: ("Слабый дождь",            "🌧"),
    63: ("Дождь",                   "🌧"),
    65: ("Сильный дождь",           "🌧"),
    71: ("Слабый снег",             "🌨"),
    73: ("Снег",                    "❄"),
    75: ("Сильный снег",            "❄"),
    77: ("Снежная крупа",           "🌨"),
    80: ("Ливень",                  "⛈"),
    81: ("Сильный ливень",          "⛈"),
    82: ("Шквальный ливень",        "⛈"),
    85: ("Снежный ливень",          "🌨"),
    86: ("Сильный снежный ливень",  "🌨"),
    95: ("Гроза",                   "⛈"),
    96: ("Гроза с градом",          "⛈"),
    99: ("Гроза с сильным градом",  "⛈"),
}

WIND_DIRS = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]

def wind_dir(deg: float) -> str:
    return WIND_DIRS[round(deg / 45) % 8]

def wmo(code: int) -> tuple[str, str]:
    return WMO_CODES.get(code, (str(code), "?"))

# ── Palette ───────────────────────────────────────────────────────────────────

BG      = "#0f172a"
CARD    = "#1e293b"
BORDER  = "#334155"
ACCENT  = "#38bdf8"
TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
WARM    = "#fb923c"
COOL    = "#60a5fa"
PILL_BG = "#0f2942"

FONT    = "Segoe UI"

# ── App ───────────────────────────────────────────────────────────────────────

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Погода")
        self.geometry("640x780")
        self.minsize(540, 600)
        self.configure(bg=BG)
        self._build_ui()
        self.after(100, self._start_fetch)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # ── Search row ──
        sf = tk.Frame(self, bg=BG)
        sf.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        sf.columnconfigure(0, weight=1)

        self.city_var = tk.StringVar(value="Москва")
        entry = tk.Entry(
            sf, textvariable=self.city_var,
            font=(FONT, 13), bg=CARD, fg=TEXT,
            insertbackground=TEXT, relief="flat", bd=0,
            highlightthickness=2, highlightbackground=BORDER, highlightcolor=ACCENT,
        )
        entry.grid(row=0, column=0, sticky="ew", ipady=9, padx=(0, 10))
        entry.bind("<Return>", lambda _: self._start_fetch())

        self.btn = tk.Button(
            sf, text="Найти", font=(FONT, 12, "bold"),
            bg=ACCENT, fg=BG, activebackground="#7dd3fc", activeforeground=BG,
            relief="flat", bd=0, cursor="hand2", padx=18, pady=9,
            command=self._start_fetch,
        )
        self.btn.grid(row=0, column=1)

        # ── Status ──
        self.status_var = tk.StringVar(value="Введите город и нажмите «Найти»")
        tk.Label(
            self, textvariable=self.status_var,
            bg=BG, fg=MUTED, font=(FONT, 9), anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=22, pady=(6, 0))

        # ── Scrollable area ──
        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._canvas.grid(row=2, column=0, sticky="nsew")

        sb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        sb.grid(row=2, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=sb.set)

        self.content = tk.Frame(self._canvas, bg=BG)
        self._win_id = self._canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind(
            "<Configure>",
            lambda _: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._win_id, width=e.width)
        )
        self._canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-(e.delta // 120), "units")
        )

    # ── Fetch ─────────────────────────────────────────────────────────────────

    def _start_fetch(self):
        city = self.city_var.get().strip()
        if not city:
            return
        self.btn.configure(state="disabled", text="...")
        self.status_var.set("Загрузка...")
        threading.Thread(target=self._fetch, args=(city,), daemon=True).start()

    def _fetch(self, city: str):
        try:
            lat, lon, full_name = geocode(city)
            data = get_weather(lat, lon)
            self.after(0, self._render, full_name, data)
        except ValueError as e:
            self.after(0, self._on_error, str(e))
        except Exception as e:
            self.after(0, self._on_error, f"Ошибка сети: {e}")

    def _on_error(self, msg: str):
        self.status_var.set(msg)
        self.btn.configure(state="normal", text="Найти")
        messagebox.showerror("Ошибка", msg, parent=self)

    # ── Render ────────────────────────────────────────────────────────────────

    def _render(self, full_name: str, data: dict):
        for w in self.content.winfo_children():
            w.destroy()

        cur   = data["current"]
        daily = data["daily"]
        tz    = data.get("timezone", "")
        time_str = cur["time"].replace("T", "  ")
        desc, icon = wmo(cur["weather_code"])

        self.status_var.set(full_name)
        self.btn.configure(state="normal", text="Найти")

        # ── Current weather card ──
        card = self._card(self.content)
        card.pack(fill="x", padx=14, pady=(10, 6))
        card.columnconfigure(1, weight=1)

        tk.Label(
            card, text=icon, font=("Segoe UI Emoji", 48),
            bg=CARD, fg=TEXT,
        ).grid(row=0, column=0, rowspan=3, padx=(16, 6), pady=(14, 6))

        tk.Label(
            card, text=f"{cur['temperature_2m']}°C",
            font=(FONT, 40, "bold"), bg=CARD, fg=TEXT, anchor="w",
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            card, text=desc,
            font=(FONT, 13), bg=CARD, fg=ACCENT, anchor="w",
        ).grid(row=1, column=1, sticky="w")

        tk.Label(
            card,
            text=f"Ощущается {cur['apparent_temperature']}°C  ·  {time_str}  ({tz})",
            font=(FONT, 9), bg=CARD, fg=MUTED, anchor="w",
        ).grid(row=2, column=1, sticky="w")

        # Pills row
        pf = tk.Frame(card, bg=CARD)
        pf.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(6, 14))

        self._pill(pf, "Влажность",  f"{cur['relative_humidity_2m']} %")
        self._pill(pf, "Ветер",      f"{cur['wind_speed_10m']} км/ч {wind_dir(cur['wind_direction_10m'])}")
        self._pill(pf, "Осадки",     f"{cur['precipitation']} мм")

        # ── 7-day forecast ──
        tk.Label(
            self.content, text="Прогноз на 7 дней",
            bg=BG, fg=MUTED, font=(FONT, 11, "bold"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        for i, date in enumerate(daily["time"]):
            d_desc, d_icon = wmo(daily["weather_code"][i])
            t_min    = daily["temperature_2m_min"][i]
            t_max    = daily["temperature_2m_max"][i]
            precip   = daily["precipitation_sum"][i]

            row = self._card(self.content)
            row.pack(fill="x", padx=14, pady=3)
            row.columnconfigure(2, weight=1)

            tk.Label(
                row, text=d_icon, font=("Segoe UI Emoji", 20),
                bg=CARD, fg=TEXT, width=3,
            ).grid(row=0, column=0, padx=(12, 4), pady=10)

            tk.Label(
                row, text=date,
                font=(FONT, 10, "bold"), bg=CARD, fg=TEXT, anchor="w", width=12,
            ).grid(row=0, column=1, sticky="w")

            tk.Label(
                row, text=d_desc,
                font=(FONT, 10), bg=CARD, fg=MUTED, anchor="w",
            ).grid(row=0, column=2, sticky="w")

            tf = tk.Frame(row, bg=CARD)
            tf.grid(row=0, column=3, padx=(0, 6))
            tk.Label(tf, text=f"↓{t_min}°", font=(FONT, 10, "bold"), bg=CARD, fg=COOL).pack(side="left", padx=3)
            tk.Label(tf, text=f"↑{t_max}°", font=(FONT, 10, "bold"), bg=CARD, fg=WARM).pack(side="left", padx=3)

            if precip and precip > 0:
                tk.Label(
                    row, text=f"{precip} мм",
                    font=(FONT, 9), bg=CARD, fg=MUTED,
                ).grid(row=0, column=4, padx=(0, 12))

        tk.Frame(self.content, bg=BG, height=16).pack()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _card(self, parent: tk.Widget) -> tk.Frame:
        """Frame with a 1px border via highlightthickness."""
        return tk.Frame(
            parent, bg=CARD,
            highlightbackground=BORDER, highlightthickness=1,
        )

    def _pill(self, parent: tk.Widget, label: str, value: str):
        f = tk.Frame(parent, bg=PILL_BG, highlightbackground=BORDER, highlightthickness=1)
        f.pack(side="left", padx=4, pady=2)
        tk.Label(f, text=label, font=(FONT, 9),       bg=PILL_BG, fg=MUTED ).pack(side="left", padx=(8, 2), pady=4)
        tk.Label(f, text=value, font=(FONT, 9, "bold"), bg=PILL_BG, fg=TEXT ).pack(side="left", padx=(0, 8), pady=4)


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
