import pygame

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 820
FPS = 60

# Core palette
BG_PRIMARY = (8, 8, 24)
BG_SECONDARY = (14, 14, 34)
BG_PANEL = (18, 18, 42)
BG_CARD = (23, 23, 50)
BG_CARD_HOVER = (32, 32, 62)
BORDER = (40, 40, 72)
BORDER_LIGHT = (55, 55, 90)
TEXT_PRIMARY = (225, 225, 245)
TEXT_SECONDARY = (150, 150, 185)
TEXT_MUTED = (90, 90, 130)
ACCENT = (55, 120, 255)
ACCENT_HOVER = (80, 150, 255)
ACCENT_TEAL = (0, 200, 200)
ACCENT_PURPLE = (120, 70, 220)
GREEN = (0, 200, 80)
RED = (230, 60, 60)
ORANGE = (255, 170, 50)
YELLOW = (245, 220, 60)
CYAN = (0, 185, 200)
WHITE = TEXT_PRIMARY
BLACK = (0, 0, 0)
MUTED = TEXT_MUTED

STATUS_COLORS = {
    "Programado": (70, 110, 255),
    "Abordando": (255, 170, 50),
    "Despegó": (0, 200, 80),
    "En vuelo": (0, 180, 200),
    "Aterrizó": (50, 220, 110),
    "En puerta": (70, 200, 70),
    "Retardado": (230, 60, 60),
    "Cancelado": (130, 30, 30),
}

STATUS_BG = {k: (v[0]//5, v[1]//5, v[2]//5, 180) for k, v in STATUS_COLORS.items()}

STATUS_TRANSITIONS_DEP = ["Programado", "Abordando", "Despegó", "En vuelo"]
STATUS_TRANSITIONS_ARR = ["En vuelo", "Aterrizó", "En puerta"]

PROGRESS_THRESHOLDS_DEP = {"Programado": 20, "Abordando": 50, "Despegó": 60}
PROGRESS_THRESHOLDS_ARR = {"En vuelo": 75, "Aterrizó": 92}

GATES_DEP = [f"{l}{n}" for l in "ABC" for n in range(1, 4)]
GATES_ARR = [f"{l}{n}" for l in "XYZ" for n in range(1, 4)]

WEATHERS = ["Despejado", "Nublado", "Lluvioso", "Tormenta"]
WEATHER_DELAY = {"Despejado": 0, "Nublado": 2, "Lluvioso": 5, "Tormenta": 12}

UPDATE_MS = 3000
PROGRESS_PER_TICK = 4
MAX_PROGRESS = 100

SPEEDS = [1, 2, 5, 10]
SORT_KEYS = ["code", "time", "status"]

AIRPORTS = {
    "BOG": ("Bogotá", (90, 100, 220)),
    "MDE": ("Medellín", (200, 150, 80)),
    "CLO": ("Cali", (160, 200, 120)),
    "CTG": ("Cartagena", (220, 180, 60)),
    "BAQ": ("Barranquilla", (140, 90, 180)),
    "MAD": ("Madrid", (100, 100, 100)),
    "MIA": ("Miami", (200, 80, 80)),
    "PTY": ("Panamá", (180, 180, 80)),
    "UIO": ("Quito", (80, 180, 130)),
    "LIM": ("Lima", (130, 80, 180)),
    "CDG": ("París", (180, 130, 200)),
    "JFK": ("Nueva York", (60, 60, 180)),
    "FRA": ("Frankfurt", (60, 100, 60)),
    "LHR": ("Londres", (130, 130, 180)),
    "ATL": ("Atlanta", (180, 180, 60)),
    "YYZ": ("Toronto", (200, 60, 60)),
    "AMS": ("Ámsterdam", (180, 60, 130)),
    "IST": ("Estambul", (200, 130, 60)),
    "DOH": ("Doha", (130, 180, 60)),
    "DXB": ("Dubái", (180, 130, 60)),
    "FCO": ("Roma", (130, 60, 180)),
    "LIS": ("Lisboa", (60, 180, 130)),
    "SCL": ("Santiago", (60, 130, 180)),
    "EZE": ("Buenos Aires", (130, 180, 180)),
    "MEX": ("Ciudad de México", (180, 180, 130)),
    "HAV": ("La Habana", (60, 180, 60)),
    "PUJ": ("Punta Cana", (180, 60, 180)),
    "SFO": ("San Francisco", (60, 130, 60)),
    "LAX": ("Los Ángeles", (130, 60, 60)),
    "ORD": ("Chicago", (60, 60, 130)),
}

AIRPORT_CODES = {}
for k, v in AIRPORTS.items():
    AIRPORT_CODES[v[0]] = k
