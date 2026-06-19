import math
import random
from typing import List, Tuple, Optional
import pygame
from flight import Flight
from config import *

font_cache = {}

def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in font_cache:
        font_cache[key] = pygame.font.SysFont("Segoe UI", size, bold=bold)
    return font_cache[key]


def draw_gradient(screen: pygame.Surface):
    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        r = int(BG_PRIMARY[0] * (1 - t) + BG_SECONDARY[0] * t)
        g = int(BG_PRIMARY[1] * (1 - t) + BG_SECONDARY[1] * t)
        b = int(BG_PRIMARY[2] * (1 - t) + BG_SECONDARY[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))


def rounded_rect(screen, color, rect, radius=6):
    pygame.draw.rect(screen, color, rect, border_radius=radius)


def draw_shadow(screen, rect, radius=8, alpha=40):
    for i in range(3, 0, -1):
        s = pygame.Surface((rect.w + i * 4, rect.h + i * 4))
        s.set_alpha(alpha // i)
        s.fill((0, 0, 0))
        screen.blit(s, (rect.x - i * 2, rect.y - i * 2))


class Button:
    def __init__(self, x: int, y: int, w: int, h: int, text: str, color=ACCENT, text_color=TEXT_PRIMARY):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover = False

    def draw(self, screen: pygame.Surface):
        c = (min(255, self.color[0] + 30), min(255, self.color[1] + 30), min(255, self.color[2] + 30)) if self.hover else self.color
        draw_shadow(screen, self.rect, radius=4, alpha=30)
        rounded_rect(screen, c, self.rect, radius=6)
        inner = self.rect.inflate(-2, -2)
        brdr = (min(255, c[0] + 40), min(255, c[1] + 40), min(255, c[2] + 40)) if self.hover else (min(255, c[0] + 20), min(255, c[1] + 20), min(255, c[2] + 20))
        pygame.draw.rect(screen, brdr, inner, 1, border_radius=5)
        lbl = get_font(12, bold=True).render(self.text, True, self.text_color)
        screen.blit(lbl, (self.rect.centerx - lbl.get_width() // 2, self.rect.centery - lbl.get_height() // 2))

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self.hover:
            return True
        return False


class TopBar:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, SCREEN_WIDTH, 64)

    def draw(self, screen: pygame.Surface, stats: dict):
        pygame.draw.rect(screen, (10, 10, 30), self.rect)
        pygame.draw.line(screen, BORDER, (0, 64), (SCREEN_WIDTH, 64), 1)
        pygame.draw.line(screen, (20, 20, 48), (0, 63), (SCREEN_WIDTH, 63), 1)

        title = get_font(22, bold=True).render("Aeropuerto IA", True, TEXT_PRIMARY)
        screen.blit(title, (24, 12))
        sub = get_font(11).render("Sistema de Control Distributivo", True, TEXT_MUTED)
        screen.blit(sub, (26, 42))

        sim_time = stats.get("time", "06:00")
        st_bg = pygame.Rect(340, 14, 96, 34)
        rounded_rect(screen, BG_PANEL, st_bg, 6)
        pygame.draw.rect(screen, BORDER, st_bg, 1, border_radius=6)
        st_lbl = get_font(18, bold=True).render(sim_time, True, ACCENT_TEAL)
        screen.blit(st_lbl, (st_bg.centerx - st_lbl.get_width() // 2, st_bg.centery - st_lbl.get_height() // 2))

        weather = stats.get("weather", "Despejado")
        w_icon = {"Despejado": "☀", "Nublado": "☁", "Lluvioso": "☂", "Tormenta": "⚡"}.get(weather, "☀")
        w_color = {"Despejado": YELLOW, "Nublado": TEXT_MUTED, "Lluvioso": ACCENT_TEAL, "Tormenta": RED}.get(weather, TEXT_PRIMARY)
        w_bg = pygame.Rect(450, 14, 120, 34)
        rounded_rect(screen, BG_PANEL, w_bg, 6)
        pygame.draw.rect(screen, BORDER, w_bg, 1, border_radius=6)
        w_lbl = get_font(16).render(f"{w_icon} {weather}", True, w_color)
        screen.blit(w_lbl, (w_bg.centerx - w_lbl.get_width() // 2, w_bg.centery - w_lbl.get_height() // 2))

        stats_x = 600
        items = [
            (f"Total: {stats.get('total', 0)}", TEXT_PRIMARY),
            (f"A tiempo: {stats.get('on_time', 0)}", GREEN),
            (f"Demorados: {stats.get('delayed', 0)}", ORANGE),
            (f"Cancelados: {stats.get('cancelled', 0)}", RED),
            (f"Demora: {stats.get('avg_delay', 0)}min", TEXT_MUTED),
        ]
        for i, (txt, col) in enumerate(items):
            bg = pygame.Rect(stats_x + i * 142, 14, 134, 34)
            rounded_rect(screen, BG_PANEL, bg, 6)
            pygame.draw.rect(screen, BORDER, bg, 1, border_radius=6)
            lbl = get_font(12).render(txt, True, col)
            screen.blit(lbl, (bg.centerx - lbl.get_width() // 2, bg.centery - lbl.get_height() // 2))


class SearchBar:
    def __init__(self):
        self.rect = pygame.Rect(14, 78, 300, 30)
        self.text = ""
        self.active = False
        self.active_filter = "all"

    def draw(self, screen: pygame.Surface):
        c = ACCENT if self.active else BORDER
        rounded_rect(screen, (13, 13, 32), self.rect, 5)
        pygame.draw.rect(screen, c, self.rect, 1, border_radius=5)
        prefix = "" if self.text else ""
        cursor = "|" if self.active else ""
        display = prefix + self.text + cursor
        lbl = get_font(13).render(display, True, TEXT_PRIMARY if self.text else TEXT_MUTED)
        screen.blit(lbl, (self.rect.x + 8, self.rect.y + 6))

        filters = [("all", "Todos"), ("dep", "Salidas"), ("arr", "Llegadas")]
        for i, (key, label) in enumerate(filters):
            bx = 328 + i * 82
            active = self.active_filter == key
            c = ACCENT if active else BG_PANEL
            rounded_rect(screen, c, (bx, 78, 76, 30), 5)
            bw = 1 if not active else 1
            bc = ACCENT if active else BORDER
            pygame.draw.rect(screen, bc, (bx, 78, 76, 30), bw, border_radius=5)
            lbl = get_font(12, bold=active).render(label, True, TEXT_PRIMARY if active else TEXT_MUTED)
            screen.blit(lbl, (bx + 38 - lbl.get_width() // 2, 86))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_ESCAPE:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isprintable():
                self.text += event.unicode


class FlightCard:
    HEIGHT = 32
    GAP = 3

    def __init__(self, flight: Flight, rect: pygame.Rect):
        self.flight = flight
        self.rect = rect
        self.hover = False

    def draw(self, screen: pygame.Surface, is_new: bool = False):
        bg = BG_CARD_HOVER if self.hover else BG_CARD
        if is_new:
            bg = (30, 25, 50)
        rounded_rect(screen, bg, self.rect, 4)
        inner = self.rect.inflate(-1, -1)
        pygame.draw.rect(screen, BORDER, inner, 1, border_radius=3)

        color = STATUS_COLORS.get(self.flight.status, TEXT_PRIMARY)
        pygame.draw.circle(screen, color, (self.rect.x + 10, self.rect.centery), 4)
        pygame.draw.circle(screen, (color[0]//2, color[1]//2, color[2]//2), (self.rect.x + 10, self.rect.centery), 5, 1)

        code_lbl = get_font(11, bold=True).render(self.flight.code, True, TEXT_PRIMARY)
        screen.blit(code_lbl, (self.rect.x + 20, self.rect.y + 3))

        dest_lbl = get_font(10).render(self.flight.destination, True, TEXT_SECONDARY)
        screen.blit(dest_lbl, (self.rect.x + 20, self.rect.y + 17))

        status_bg = pygame.Rect(self.rect.x + 100, self.rect.y + 4, 72, 24)
        c = color
        rounded_rect(screen, (c[0]//6, c[1]//6, c[2]//6), status_bg, 4)
        status_lbl = get_font(10, bold=True).render(self.flight.status, True, color)
        screen.blit(status_lbl, (status_bg.centerx - status_lbl.get_width() // 2, status_bg.centery - status_lbl.get_height() // 2))

        time_str = self.flight.scheduled_time
        if self.flight.delay > 0:
            time_str += f" +{self.flight.delay}"
        time_lbl = get_font(10).render(time_str, True, TEXT_MUTED)
        screen.blit(time_lbl, (self.rect.x + 180, self.rect.y + 4))

        gate_str = self.flight.gate if self.flight.gate else ""
        if gate_str:
            gate_lbl = get_font(10).render(gate_str, True, ACCENT_TEAL)
            screen.blit(gate_lbl, (self.rect.x + 180, self.rect.y + 17))

        if is_new:
            new_lbl = get_font(8, bold=True).render("NUEVO", True, YELLOW)
            screen.blit(new_lbl, (self.rect.right - 38, self.rect.y + 3))


class FlightPanel:
    def __init__(self, x: int, y: int, w: int, h: int, title: str):
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.cards: List[FlightCard] = []
        self.total_count = 0
        self.all_flights: List[Flight] = []
        self.scroll_offset = 0

    def set_flights(self, flights: List[Flight], filter_text: str, filter_dir: str):
        self.all_flights = []
        for f in flights:
            dir_match = (filter_dir == "all" or
                         (filter_dir == "dep" and f.direction == "Salida") or
                         (filter_dir == "arr" and f.direction == "Llegada"))
            if not dir_match:
                continue
            if filter_text:
                if filter_text.lower() not in f.code.lower() and filter_text.lower() not in f.destination.lower():
                    continue
            self.all_flights.append(f)

        self.total_count = len(self.all_flights)
        max_visible = max(1, (self.rect.height - 38) // (FlightCard.HEIGHT + FlightCard.GAP))
        self.scroll_offset = min(self.scroll_offset, max(0, self.total_count - max_visible))
        self.scroll_offset = max(0, self.scroll_offset)
        shown = self.all_flights[self.scroll_offset:self.scroll_offset + max_visible]

        self.cards.clear()
        card_w = self.rect.width - 16
        y_offset = self.rect.y + 30
        for f in shown:
            cr = pygame.Rect(self.rect.x + 8, y_offset, card_w, FlightCard.HEIGHT)
            self.cards.append(FlightCard(f, cr))
            y_offset += FlightCard.HEIGHT + FlightCard.GAP

    def draw(self, screen: pygame.Surface, changed_codes: set):
        draw_shadow(screen, self.rect, radius=8, alpha=25)
        rounded_rect(screen, BG_PANEL, self.rect, 8)
        inner = self.rect.inflate(-1, -1)
        pygame.draw.rect(screen, BORDER, inner, 1, border_radius=7)

        title_lbl = get_font(13, bold=True).render(f"{self.title}  {TEXT_SECONDARY}{self.total_count}", True, TEXT_PRIMARY)
        screen.blit(title_lbl, (self.rect.x + 12, self.rect.y + 8))

        clip = pygame.Rect(self.rect.x + 2, self.rect.y + 26, self.rect.width - 4, self.rect.height - 28)
        old = screen.get_clip()
        screen.set_clip(clip)

        for card in self.cards:
            card.draw(screen, card.flight.code in changed_codes)

        screen.set_clip(old)

        if self.scroll_offset > 0:
            lbl = get_font(10).render("▲", True, TEXT_MUTED)
            screen.blit(lbl, (self.rect.right - 16, self.rect.y + 28))
        if self.scroll_offset + len(self.cards) < self.total_count:
            lbl = get_font(10).render("▼", True, TEXT_MUTED)
            screen.blit(lbl, (self.rect.right - 16, self.rect.bottom - 16))

    def scroll(self, direction: int):
        max_visible = max(1, (self.rect.height - 38) // (FlightCard.HEIGHT + FlightCard.GAP))
        self.scroll_offset = max(0, min(self.total_count - max_visible, self.scroll_offset + direction))

    def handle_mouse(self, event) -> Optional[Flight]:
        if event.type == pygame.MOUSEMOTION:
            for card in self.cards:
                card.hover = card.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                if self.rect.collidepoint(event.pos):
                    self.scroll(-1)
                    return None
            if event.button == 5:
                if self.rect.collidepoint(event.pos):
                    self.scroll(1)
                    return None
            for card in self.cards:
                if card.rect.collidepoint(event.pos):
                    return card.flight
        return None


class Radar:
    def __init__(self, cx: int, cy: int, radius: int):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.sweep_angle = 0.0
        self.planes: List[dict] = []
        self.trails: List[List[Tuple[float, float]]] = []
        self._init_planes()

    def _init_planes(self):
        for i in range(10):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.randint(60, self.radius - 20)
            self.planes.append({
                "code": f"AV{200 + i}",
                "angle": angle,
                "dist": dist,
                "speed": random.uniform(-0.008, 0.008),
                "altitude": random.randint(25000, 40000),
            })
            self.trails.append([])

    def update(self):
        self.sweep_angle += 0.015
        if self.sweep_angle > 2 * math.pi:
            self.sweep_angle = 0
        for i, p in enumerate(self.planes):
            p["angle"] += p["speed"]
            p["dist"] += random.uniform(-0.3, 0.3)
            p["dist"] = max(20, min(self.radius - 10, p["dist"]))
            px = self.cx + p["dist"] * math.cos(p["angle"])
            py = self.cy + p["dist"] * math.sin(p["angle"])
            self.trails[i].append((px, py))
            if len(self.trails[i]) > 20:
                self.trails[i].pop(0)

    def draw(self, screen: pygame.Surface):
        r = self.radius
        draw_shadow(screen, pygame.Rect(self.cx - r, self.cy - r, r * 2, r * 2), radius=r // 4, alpha=20)

        # Outer rings
        for i in range(3):
            rr = r - i * 4
            a = 20 - i * 5
            pygame.draw.circle(screen, (0, a * 2, a), (self.cx, self.cy), rr, 1)

        # Crosshairs
        pygame.draw.line(screen, (0, 30, 15), (self.cx - r, self.cy), (self.cx + r, self.cy), 1)
        pygame.draw.line(screen, (0, 30, 15), (self.cx, self.cy - r), (self.cx, self.cy + r), 1)

        # Sweep
        sx = self.cx + r * math.cos(self.sweep_angle)
        sy = self.cy + r * math.sin(self.sweep_angle)
        pygame.draw.line(screen, (0, 180, 60), (self.cx, self.cy), (sx, sy), 2)

        for i in range(25):
            a = self.sweep_angle - i * 0.012
            if a < 0:
                a += 2 * math.pi
            ax = self.cx + r * math.cos(a)
            ay = self.cy + r * math.sin(a)
            alpha = max(0, 50 - i * 2)
            if alpha > 0:
                pygame.draw.line(screen, (0, alpha, alpha // 3), (self.cx, self.cy), (ax, ay), 1)

        # Trails
        for trail in self.trails:
            for j, (tx, ty) in enumerate(trail):
                t = j / len(trail)
                sz = max(1, int(2.5 * t))
                pygame.draw.circle(screen, (0, int(50 * t), int(15 * t)), (int(tx), int(ty)), sz)

        # Planes
        for i, p in enumerate(self.planes):
            px = int(self.cx + p["dist"] * math.cos(p["angle"]))
            py = int(self.cy + p["dist"] * math.sin(p["angle"]))
            blink = int(abs(math.sin(self.sweep_angle * 3 + i)) * 180 + 75)
            c = (blink // 2, blink, blink // 2)
            pygame.draw.circle(screen, c, (px, py), 4)
            pygame.draw.circle(screen, (blink, 255, blink), (px, py), 6, 1)
            lbl = get_font(9).render(p["code"], True, (120, 200, 120))
            screen.blit(lbl, (px + 8, py + 4))

        lbl = get_font(11, bold=True).render("RADAR", True, (0, 180, 80))
        screen.blit(lbl, (self.cx - 24, self.cy - r - 16))


class Runway:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.rect = pygame.Rect(x, y, w, h)
        self.planes: List[dict] = []
        self.spawn_timer = 0

    def update(self):
        self.spawn_timer += 1
        if self.spawn_timer > 120 and len(self.planes) < 3:
            self.spawn_timer = 0
            if random.random() < 0.4:
                direction = random.choice(["takeoff", "landing"])
                if direction == "takeoff":
                    self.planes.append({
                        "x": self.rect.x + 10, "y": self.rect.centery + random.randint(-8, 8),
                        "speed": random.uniform(1.5, 3.0), "phase": "roll", "alpha": 255,
                        "size": random.randint(5, 8),
                        "color": random.choice([(180, 200, 255), (255, 180, 180), (180, 255, 200)]),
                    })
                else:
                    self.planes.append({
                        "x": self.rect.right - 10, "y": self.rect.centery + random.randint(-8, 8),
                        "speed": random.uniform(-1.0, -0.5), "phase": "approach", "alpha": 255,
                        "size": random.randint(5, 8),
                        "color": random.choice([(180, 200, 255), (255, 180, 180), (180, 255, 200)]),
                    })
        for p in self.planes[:]:
            p["x"] += p["speed"]
            if p["phase"] == "roll" and p["x"] > self.rect.right - 20:
                p["alpha"] -= 10
            elif p["phase"] == "approach" and p["x"] < self.rect.x + 20:
                p["alpha"] -= 10
            if p["alpha"] <= 0 or p["x"] < self.rect.x - 30 or p["x"] > self.rect.right + 30:
                self.planes.remove(p)

    def draw(self, screen: pygame.Surface):
        r = self.rect
        draw_shadow(screen, r, radius=6, alpha=25)
        rounded_rect(screen, (14, 14, 34), r, 6)
        pygame.draw.rect(screen, BORDER, r, 1, border_radius=6)

        rwy = pygame.Rect(r.x + 8, r.centery - 10, r.w - 16, 20)
        rounded_rect(screen, (24, 24, 44), rwy, 3)
        pygame.draw.rect(screen, (40, 40, 65), rwy, 1, border_radius=3)

        for i in range(0, rwy.w - 6, 16):
            x = rwy.x + 4 + i
            pygame.draw.rect(screen, (90, 90, 120), (x, rwy.y + 2, 8, 2))
            pygame.draw.rect(screen, (90, 90, 120), (x, rwy.centery + 4, 8, 2))

        lbl = get_font(8).render("PISTA 13", True, TEXT_MUTED)
        screen.blit(lbl, (r.x + 10, r.y + 4))

        for p in self.planes:
            if p["alpha"] <= 0:
                continue
            sz, a = p["size"], p["alpha"]
            c = tuple(v * a // 255 for v in p["color"])
            pts = [(p["x"] + sz, p["y"]), (p["x"] - sz // 2, p["y"] - sz // 2), (p["x"] - sz // 2, p["y"] + sz // 2)]
            pygame.draw.polygon(screen, c, pts)


class DetailPanel:
    def __init__(self):
        self.flight: Optional[Flight] = None
        self.rect = pygame.Rect(0, 0, 400, 520)
        self.action_rects: List[tuple] = []
        self.action_hover = None

    def show(self, f: Flight):
        self.flight = f

    def hide(self):
        self.flight = None

    def draw(self, screen: pygame.Surface, delay_reason: str = ""):
        if not self.flight:
            return
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 10))
        screen.blit(overlay, (0, 0))

        draw_shadow(screen, self.rect, radius=16, alpha=60)
        rounded_rect(screen, (16, 16, 40), self.rect, 14)
        pygame.draw.rect(screen, BORDER_LIGHT, self.rect, 1, border_radius=14)

        f = self.flight
        color = STATUS_COLORS.get(f.status, TEXT_PRIMARY)

        # Header bar
        hdr = pygame.Rect(self.rect.x + 0, self.rect.y + 0, self.rect.w, 48)
        rounded_rect(screen, (22, 22, 50), hdr)
        pygame.draw.line(screen, BORDER, (self.rect.x + 20, 48 + self.rect.y), (self.rect.right - 20, 48 + self.rect.y), 1)

        title = get_font(20, bold=True).render(f"{f.code}  ·  {f.destination}", True, TEXT_PRIMARY)
        screen.blit(title, (self.rect.x + 24, self.rect.y + 14))

        y = self.rect.y + 64
        info = [
            ("Estado", f.status, color),
            ("Tipo", f"{f.flight_type} · {f.direction}", TEXT_SECONDARY),
            ("Pasajeros", str(f.passengers), TEXT_PRIMARY),
            ("Hora", f.scheduled_time, TEXT_PRIMARY),
            ("Puerta", f.gate if f.gate else "Sin asignar", ACCENT_TEAL if f.gate else TEXT_MUTED),
            ("Demora", f"{f.delay} min" if f.delay > 0 else "0 min", ORANGE if f.delay > 0 else TEXT_MUTED),
            ("Progreso", f"{f.progress}%", TEXT_PRIMARY),
        ]
        for label, value, val_color in info:
            lbl = get_font(12).render(label, True, TEXT_MUTED)
            screen.blit(lbl, (self.rect.x + 24, y))
            vl = get_font(13, bold=True).render(value, True, val_color)
            screen.blit(vl, (self.rect.x + 120, y))
            y += 24

        # Crew
        if f.captain:
            y += 4
            pygame.draw.line(screen, BORDER, (self.rect.x + 20, y - 4), (self.rect.right - 20, y - 4), 1)
            cr_lbl = get_font(11).render(f"Tripulación: {f.captain} · {f.copilot} · {f.cabin_crew}", True, TEXT_SECONDARY)
            screen.blit(cr_lbl, (self.rect.x + 24, y + 2))
            y += 28

        # Progress bar
        bar = pygame.Rect(self.rect.x + 24, y, self.rect.w - 48, 10)
        rounded_rect(screen, (30, 30, 55), bar, 5)
        fill_w = int(bar.w * f.progress / 100)
        if fill_w > 0:
            fc = GREEN if f.progress < 80 else (ORANGE if f.progress < 95 else RED)
            fill = pygame.Rect(bar.x, bar.y, fill_w, bar.h)
            rounded_rect(screen, fc, fill, 5)
        y += 20

        # Delay reason
        if delay_reason:
            dr_lbl = get_font(10).render(delay_reason, True, ORANGE)
            screen.blit(dr_lbl, (self.rect.x + 24, y))
            y += 20

        # Action buttons
        y += 8
        pygame.draw.line(screen, BORDER, (self.rect.x + 20, y - 6), (self.rect.right - 20, y - 6), 1)
        act_title = get_font(12, bold=True).render("Acciones", True, ACCENT)
        screen.blit(act_title, (self.rect.x + 24, y))
        y += 24

        self.action_rects = []
        actions = []
        if f.status != "Cancelado":
            if f.direction == "Salida":
                for s in ["Programado", "Abordando", "Despegó"]:
                    if s != f.status:
                        actions.append((f"→ {s}", s))
            else:
                for s in ["En vuelo", "Aterrizó", "En puerta"]:
                    if s != f.status:
                        actions.append((f"→ {s}", s))
            actions.extend([
                ("+5 min", "delay5"), ("+15 min", "delay15"),
            ])
            if f.delay > 0:
                actions.append(("Quitar demora", "cleardelay"))
            if f.status != "Retardado":
                actions.append(("Retardar", "retardado"))
            actions.append(("Cancelar", "cancelar"))

        for i, (label, action) in enumerate(actions):
            col = i % 2
            ax = self.rect.x + 24 + col * 185
            ay = y + (i // 2) * 28
            ar = pygame.Rect(ax, ay, 175, 23)
            is_hover = self.action_hover == (label, action)
            ac = BG_CARD_HOVER if is_hover else BG_CARD
            if action == "cancelar":
                ac = (60, 15, 15) if is_hover else (40, 10, 10)
            rounded_rect(screen, ac, ar, 4)
            pygame.draw.rect(screen, BORDER, ar, 1, border_radius=4)
            albl = get_font(10, bold=True).render(label, True, TEXT_PRIMARY)
            screen.blit(albl, (ar.centerx - albl.get_width() // 2, ar.centery - albl.get_height() // 2))
            self.action_rects.append((ar, action, f))

        close_lbl = get_font(11).render("ESC o clic fuera para cerrar", True, TEXT_MUTED)
        screen.blit(close_lbl, (self.rect.x + 24, self.rect.y + self.rect.height - 28))

    def handle_click(self, pos) -> Optional[tuple]:
        if hasattr(self, 'action_rects'):
            for rect, action, flight in self.action_rects:
                if rect.collidepoint(pos):
                    return (action, flight)
        return None

    def handle_motion(self, pos):
        self.action_hover = None
        if hasattr(self, 'action_rects'):
            for rect, action, flight in self.action_rects:
                if rect.collidepoint(pos):
                    self.action_hover = (action, flight)


class ContextMenu:
    def __init__(self):
        self.active = False
        self.flight: Optional[Flight] = None
        self.menu_x = 0
        self.menu_y = 0
        self.options: List[tuple] = []
        self.hover_idx = -1

    def show(self, flight: Flight, x: int, y: int):
        self.active = True
        self.flight = flight
        self.options = self._build_options(flight)
        menu_h = len(self.options) * 28 + 32
        self.menu_x = min(x, SCREEN_WIDTH - 210)
        self.menu_y = min(y, SCREEN_HEIGHT - menu_h)
        self.hover_idx = -1

    def hide(self):
        self.active = False
        self.flight = None
        self.hover_idx = -1

    def _build_options(self, f: Flight) -> List[tuple]:
        opts = []
        opts.append(("Ver detalle", "detail"))
        if f.direction == "Salida" and f.status == "Programado":
            opts.append(("Iniciar abordaje", "abordar"))
        if f.status in ("Programado", "Abordando") and f.direction == "Salida":
            opts.append(("Autorizar despegue", "despegar"))
        if f.direction == "Llegada" and f.status in ("En vuelo",):
            opts.append(("Autorizar aterrizaje", "aterrizar"))
        opts.append(("Asignar puerta", "repuerta"))
        if f.delay < 15:
            opts.append(("+10 min demora", "delay10"))
        if f.delay > 0:
            opts.append(("Quitar demora", "cleardelay"))
        if f.status == "Retardado" and f.delay == 0:
            opts.append(("Reanudar vuelo", "reanudar"))
        if f.status not in ("Cancelado",):
            opts.append(("Cancelar vuelo", "cancelar"))
        return opts

    def draw(self, screen: pygame.Surface):
        if not self.active or not self.flight:
            return
        item_h = 28
        w, h = 200, len(self.options) * item_h + 32
        mx, my = self.menu_x, self.menu_y

        draw_shadow(screen, pygame.Rect(mx, my, w, h), radius=8, alpha=50)
        s = pygame.Surface((w, h))
        s.set_alpha(240)
        s.fill((12, 12, 30))
        screen.blit(s, (mx, my))
        pygame.draw.rect(screen, BORDER_LIGHT, (mx, my, w, h), 1, border_radius=8)

        hdr = get_font(11, bold=True).render(f"TORRE  ·  {self.flight.code}", True, ACCENT_TEAL)
        screen.blit(hdr, (mx + 10, my + 6))
        pygame.draw.line(screen, BORDER, (mx + 8, my + 24), (mx + w - 8, my + 24), 1)

        for i, (label, action) in enumerate(self.options):
            iy = my + 28 + i * item_h
            if i == self.hover_idx:
                bg = pygame.Rect(mx + 3, iy, w - 6, item_h - 2)
                rounded_rect(screen, (30, 30, 60), bg, 4)
            c = RED if action == "cancelar" else TEXT_PRIMARY
            lbl = get_font(12).render(label, True, c)
            screen.blit(lbl, (mx + 14, iy + 6))

    def handle_motion(self, pos) -> bool:
        if not self.active:
            return False
        item_h = 28
        w, h = 200, len(self.options) * item_h + 32
        mx, my = self.menu_x, self.menu_y
        rel_y = pos[1] - my - 28
        if 0 <= pos[0] - mx <= w and 0 <= rel_y < len(self.options) * item_h:
            self.hover_idx = rel_y // item_h
            return True
        self.hover_idx = -1
        return False

    def handle_click(self, pos) -> Optional[tuple]:
        if not self.active:
            return None
        item_h = 28
        w, h = 200, len(self.options) * item_h + 32
        mx, my = self.menu_x, self.menu_y
        if mx <= pos[0] <= mx + w and my <= pos[1] <= my + h:
            rel_y = pos[1] - my - 28
            idx = rel_y // item_h
            if 0 <= idx < len(self.options):
                action = self.options[idx][1]
                result = (action, self.flight)
                self.hide()
                return result
        self.hide()
        return None


class NotificationLog:
    def __init__(self, max_items=6):
        self.items: List[tuple] = []
        self.max_items = max_items

    def add(self, msg: str, color=TEXT_PRIMARY):
        self.items.append((msg, color, pygame.time.get_ticks()))
        if len(self.items) > self.max_items:
            self.items.pop(0)

    def draw(self, screen: pygame.Surface, x: int, y: int):
        now = pygame.time.get_ticks()
        self.items = [(m, c, t) for (m, c, t) in self.items if now - t < 5000]
        if not self.items:
            return

        h = min(len(self.items), self.max_items) * 20 + 12
        w = 320
        s = pygame.Surface((w, h))
        s.set_alpha(180)
        s.fill((8, 8, 24))
        screen.blit(s, (x, y - 8))
        pygame.draw.rect(screen, BORDER, (x, y - 8, w, h), 1, border_radius=5)

        title = get_font(10, bold=True).render("ACTIVIDAD", True, TEXT_MUTED)
        screen.blit(title, (x + 8, y - 4))

        for i, (msg, col, t) in enumerate(self.items):
            age = (now - t) / 1000
            alpha = max(0.35, 1.0 - age / 5)
            c = tuple(int(v * alpha + 15 * (1 - alpha)) for v in col)
            lbl = get_font(10).render(msg, True, c)
            screen.blit(lbl, (x + 8, y + 14 + i * 20))


class CommandLog:
    def __init__(self, max_items=8):
        self.items: List[str] = []
        self.max_items = max_items

    def add(self, msg: str):
        self.items.append(msg)
        if len(self.items) > self.max_items:
            self.items.pop(0)

    def draw(self, screen: pygame.Surface, x: int, y: int):
        if not self.items:
            return
        h = len(self.items) * 18 + 12
        w = 310
        s = pygame.Surface((w, h))
        s.set_alpha(180)
        s.fill((8, 8, 24))
        screen.blit(s, (x, y - 8))
        pygame.draw.rect(screen, BORDER, (x, y - 8, w, h), 1, border_radius=5)

        title = get_font(10, bold=True).render("COMANDOS TORRE", True, ACCENT_TEAL)
        screen.blit(title, (x + 8, y - 4))

        for i, msg in enumerate(self.items[-self.max_items:]):
            lbl = get_font(10).render(f"▸ {msg}", True, TEXT_SECONDARY)
            screen.blit(lbl, (x + 8, y + 14 + i * 18))


class HelpOverlay:
    def __init__(self):
        self.active = False

    def toggle(self):
        self.active = not self.active

    def close(self):
        self.active = False

    def draw(self, screen: pygame.Surface):
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 10))
        screen.blit(overlay, (0, 0))

        rect = pygame.Rect(0, 0, 460, 360)
        rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        rounded_rect(screen, (16, 16, 40), rect, 14)
        pygame.draw.rect(screen, BORDER_LIGHT, rect, 1, border_radius=14)

        title = get_font(20, bold=True).render("Controles", True, TEXT_PRIMARY)
        screen.blit(title, (rect.x + 30, rect.y + 20))

        shortcuts = [
            ("N", "Nuevo vuelo"),
            ("S", "Guardar vuelos"),
            ("C", "Cargar vuelos"),
            ("R", "Resetear vuelos"),
            ("F1", "Mostrar / ocultar ayuda"),
            ("ESC", "Cerrar panel / menú"),
            ("Click izq.", "Ver detalle del vuelo"),
            ("Click der.", "Menú Torre de Control"),
            ("Rueda", "Navegar lista de vuelos"),
        ]
        y = rect.y + 60
        for key, desc in shortcuts:
            key_bg = pygame.Rect(rect.x + 30, y, 40, 22)
            rounded_rect(screen, BG_CARD, key_bg, 4)
            pygame.draw.rect(screen, BORDER, key_bg, 1, border_radius=4)
            kl = get_font(11, bold=True).render(key, True, ACCENT)
            screen.blit(kl, (key_bg.centerx - kl.get_width() // 2, key_bg.centery - kl.get_height() // 2))
            dl = get_font(12).render(desc, True, TEXT_PRIMARY)
            screen.blit(dl, (rect.x + 90, y + 3))
            y += 30

        cl = get_font(11).render("ESC o clic fuera para cerrar", True, TEXT_MUTED)
        screen.blit(cl, (rect.x + 30, rect.y + rect.height - 32))


class NewFlightDialog:
    def __init__(self):
        self.active = False
        self.rect = pygame.Rect(0, 0, 460, 360)
        self.step = 0
        self.data = {"flight_type": "Nacional", "direction": "Salida", "code": "", "destination": ""}
        self.options = {0: ["Nacional", "Internacional"], 1: ["Salida", "Llegada"]}
        self.input_active = False

    def open(self):
        self.active = True
        self.step = 0
        self.data = {"flight_type": "Nacional", "direction": "Salida", "code": "", "destination": ""}

    def close(self):
        self.active = False

    def draw(self, screen: pygame.Surface):
        if not self.active:
            return
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 10))
        screen.blit(overlay, (0, 0))

        draw_shadow(screen, self.rect, radius=14, alpha=60)
        rounded_rect(screen, (16, 16, 40), self.rect, 14)
        pygame.draw.rect(screen, BORDER_LIGHT, self.rect, 1, border_radius=14)

        title = get_font(20, bold=True).render("Nuevo vuelo", True, TEXT_PRIMARY)
        screen.blit(title, (self.rect.x + 28, self.rect.y + 18))

        steps = ["Tipo", "Dirección", "Código", "Destino"]
        for i, s in enumerate(steps):
            c = ACCENT if i == self.step else TEXT_MUTED if i < self.step else (50, 50, 70)
            lbl = get_font(10, bold=(i == self.step)).render(s, True, c)
            screen.blit(lbl, (self.rect.x + 28 + i * 105, self.rect.y + 50))

        if self.step in (0, 1):
            opts = self.options[self.step]
            key = "flight_type" if self.step == 0 else "direction"
            for i, opt in enumerate(opts):
                bx = self.rect.x + 40 + i * 210
                by = self.rect.y + 90
                sel = opt == self.data[key]
                c = ACCENT if sel else BG_CARD
                rounded_rect(screen, c, (bx, by, 190, 42), 6)
                bw = 2 if sel else 1
                bc = ACCENT if sel else BORDER
                pygame.draw.rect(screen, bc, (bx, by, 190, 42), bw, border_radius=6)
                lbl = get_font(14, bold=sel).render(opt, True, TEXT_PRIMARY if sel else TEXT_MUTED)
                screen.blit(lbl, (bx + 95 - lbl.get_width() // 2, by + 12))
        elif self.step in (2, 3):
            key = "code" if self.step == 2 else "destination"
            lbl = get_font(13).render("Código de vuelo" if self.step == 2 else "Destino", True, TEXT_SECONDARY)
            screen.blit(lbl, (self.rect.x + 28, self.rect.y + 88))
            inp = pygame.Rect(self.rect.x + 28, self.rect.y + 114, 404, 40)
            c = ACCENT if self.input_active else BORDER
            rounded_rect(screen, (10, 10, 28), inp, 6)
            pygame.draw.rect(screen, c, inp, 1, border_radius=6)
            display = self.data[key] + ("|" if self.input_active else "")
            il = get_font(20).render(display, True, TEXT_PRIMARY)
            screen.blit(il, (inp.x + 10, inp.y + 9))

        nav_y = self.rect.y + self.rect.height - 52
        if self.step > 0:
            back = Button(self.rect.x + 28, nav_y, 100, 32, "Anterior", (40, 40, 60), TEXT_MUTED)
            back.draw(screen)
        if self.step < 3:
            nxt = Button(self.rect.x + self.rect.w - 128, nav_y, 100, 32, "Siguiente", ACCENT)
        else:
            nxt = Button(self.rect.x + self.rect.w - 128, nav_y, 100, 32, "Crear", ACCENT)
        nxt.draw(screen)

    def handle_event(self, event) -> Optional[Flight]:
        if not self.active:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if not self.rect.collidepoint(pos):
                self.close()
                return None

            if self.step == 0:
                for i, opt in enumerate(self.options[0]):
                    bx = self.rect.x + 40 + i * 210
                    if pygame.Rect(bx, self.rect.y + 90, 190, 42).collidepoint(pos):
                        self.data["flight_type"] = opt
                        return None
            elif self.step == 1:
                for i, opt in enumerate(self.options[1]):
                    bx = self.rect.x + 40 + i * 210
                    if pygame.Rect(bx, self.rect.y + 90, 190, 42).collidepoint(pos):
                        self.data["direction"] = opt
                        return None

            if self.step in (2, 3):
                inp = pygame.Rect(self.rect.x + 28, self.rect.y + 114, 404, 40)
                self.input_active = inp.collidepoint(pos)

            if self.step > 0:
                if pygame.Rect(self.rect.x + 28, self.rect.y + self.rect.height - 52, 100, 32).collidepoint(pos):
                    self.step -= 1
                    return None

            nbx = self.rect.x + self.rect.w - 128
            if pygame.Rect(nbx, self.rect.y + self.rect.height - 52, 100, 32).collidepoint(pos):
                key = "code" if self.step == 2 else "destination"
                if self.step == 2 and not self.data["code"]:
                    return None
                if self.step == 3 and not self.data["destination"]:
                    return None
                if self.step < 3:
                    self.step += 1
                    self.input_active = True
                    return None
                import time as ttime
                f = Flight(
                    code=self.data["code"], destination=self.data["destination"],
                    flight_type=self.data["flight_type"], direction=self.data["direction"],
                    status="Programado" if self.data["direction"] == "Salida" else "En vuelo",
                    passengers=random.randint(50, 200),
                    scheduled_time=ttime.strftime("%H:%M"),
                )
                self.close()
                return f

        if event.type == pygame.KEYDOWN and self.input_active and self.step in (2, 3):
            key = "code" if self.step == 2 else "destination"
            if event.key == pygame.K_BACKSPACE:
                self.data[key] = self.data[key][:-1]
            elif event.key == pygame.K_RETURN:
                if self.step == 2 and self.data["code"]:
                    self.step = 3
                    self.input_active = True
            elif event.unicode.isprintable():
                self.data[key] += event.unicode.upper() if key == "code" else event.unicode
        return None
