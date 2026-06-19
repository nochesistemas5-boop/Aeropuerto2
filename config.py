import pygame

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 820
FPS = 60

BG_TOP = (8, 8, 40)
BG_BOTTOM = (2, 2, 18)
PANEL_BG = (16, 16, 48)
PANEL_BORDER = (40, 40, 90)
CARD_BG = (22, 22, 55)
CARD_BORDER = (35, 35, 75)
CARD_HOVER = (32, 32, 70)
ACCENT = (80, 130, 255)
WHITE = (240, 240, 255)
MUTED = (130, 130, 170)
GREEN = (0, 220, 80)
RED = (220, 50, 50)
ORANGE = (255, 180, 0)
CYAN = (0, 200, 200)
YELLOW = (255, 255, 80)
GOLD = (255, 215, 0)
RADAR_GREEN = (0, 255, 80)
RADAR_DIM = (0, 40, 15)
BLACK = (0, 0, 0)

STATUS_COLORS = {
    "Programado": (80, 100, 255),
    "Abordando": ORANGE,
    "Despegó": GREEN,
    "En vuelo": CYAN,
    "Aterrizó": (60, 255, 120),
    "En puerta": (40, 200, 80),
    "Retardado": RED,
    "Cancelado": (120, 20, 20),
}

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
