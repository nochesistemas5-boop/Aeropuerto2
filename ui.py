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
        font_cache[key] = pygame.font.SysFont("Consolas", size, bold=bold)
    return font_cache[key]


def draw_gradient(screen: pygame.Surface):
    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))


class Button:
    def __init__(self, x: int, y: int, w: int, h: int, text: str, color=ACCENT):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover = False

    def draw(self, screen: pygame.Surface):
        c = (min(255, self.color[0] + 30), min(255, self.color[1] + 30), min(255, self.color[2] + 30)) if self.hover else self.color
        pygame.draw.rect(screen, c, self.rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, self.rect, 1, border_radius=6)
        lbl = get_font(18).render(self.text, True, WHITE)
        lr = lbl.get_rect(center=self.rect.center)
        screen.blit(lbl, lr)

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hover:
                return True
        return False


class TopBar:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, SCREEN_WIDTH, 78)

    def draw(self, screen: pygame.Surface, stats: dict):
        pygame.draw.rect(screen, (10, 10, 45), self.rect)
        pygame.draw.line(screen, PANEL_BORDER, (0, 78), (SCREEN_WIDTH, 78), 2)

        title = get_font(28, bold=True).render("✈  Aeropuerto IA Distributiva", True, YELLOW)
        screen.blit(title, (20, 8))

        sim_time = stats.get("time", "06:00")
        st_lbl = get_font(24, bold=True).render(f"  {sim_time}", True, CYAN)
        screen.blit(st_lbl, (380, 10))

        weather = stats.get("weather", "Despejado")
        w_icon = {"Despejado": "☀", "Nublado": "☁", "Lluvioso": "☂", "Tormenta": "⚡"}.get(weather, "☀")
        w_color = {"Despejado": YELLOW, "Nublado": MUTED, "Lluvioso": CYAN, "Tormenta": RED}.get(weather, WHITE)
        w_lbl = get_font(20).render(f"{w_icon} {weather}", True, w_color)
        screen.blit(w_lbl, (550, 14))

        stats_x = 730
        s_items = [
            (f"Total: {stats.get('total', 0)}", WHITE),
            (f"A tiempo: {stats.get('on_time', 0)}", GREEN),
            (f"Demorados: {stats.get('delayed', 0)}", ORANGE),
            (f"Cancelados: {stats.get('cancelled', 0)}", RED),
            (f"Demora prom: {stats.get('avg_delay', 0)}min", MUTED),
        ]
        for i, (txt, col) in enumerate(s_items):
            lbl = get_font(16).render(txt, True, col)
            screen.blit(lbl, (stats_x + i * 150, 54))


class SearchBar:
    def __init__(self):
        self.rect = pygame.Rect(15, 90, 350, 34)
        self.text = ""
        self.active = False
        self.active_filter = "all"

    def draw(self, screen: pygame.Surface):
        c = ACCENT if self.active else PANEL_BORDER
        pygame.draw.rect(screen, (12, 12, 38), self.rect, border_radius=5)
        pygame.draw.rect(screen, c, self.rect, 2, border_radius=5)
        prefix = "🔍 " if not self.text else ""
        display = prefix + (self.text + "|" if self.active else self.text)
        lbl = get_font(18).render(display, True, WHITE if self.text else MUTED)
        screen.blit(lbl, (self.rect.x + 8, self.rect.y + 5))

        # quick filter buttons with active indicator
        filters = [("all", "Todos"), ("dep", "Salidas"), ("arr", "Llegadas")]
        for i, (key, label) in enumerate(filters):
            bx = 380 + i * 78
            active = self.active_filter == key
            btn_color = ACCENT if active else (50, 50, 80)
            pygame.draw.rect(screen, btn_color, (bx, 90, 72, 34), border_radius=5)
            bw = 2 if active else 1
            pygame.draw.rect(screen, WHITE, (bx, 90, 72, 34), bw, border_radius=5)
            lbl = get_font(14, bold=active).render(label, True, WHITE)
            screen.blit(lbl, (bx + 36 - lbl.get_width() // 2, 100))

    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            if hasattr(self, 'filter_all_btn') and self.filter_all_btn.handle_event(event):
                self.active_filter = "all"
            if hasattr(self, 'filter_dep_btn') and self.filter_dep_btn.handle_event(event):
                self.active_filter = "dep"
            if hasattr(self, 'filter_arr_btn') and self.filter_arr_btn.handle_event(event):
                self.active_filter = "arr"
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isprintable():
                self.text += event.unicode
        return None


class FlightCard:
    HEIGHT = 40
    GAP = 3

    def __init__(self, flight: Flight, rect: pygame.Rect):
        self.flight = flight
        self.rect = rect
        self.hover = False

    def draw(self, screen: pygame.Surface, is_new: bool = False):
        bg = CARD_HOVER if self.hover else CARD_BG
        if is_new:
            bg = (40, 30, 60)
        pygame.draw.rect(screen, bg, self.rect, border_radius=5)
        pygame.draw.rect(screen, CARD_BORDER, self.rect, 1, border_radius=5)

        color = STATUS_COLORS.get(self.flight.status, WHITE)
        pygame.draw.circle(screen, color, (self.rect.x + 10, self.rect.centery), 4)

        x0 = self.rect.x + 22
        code_lbl = get_font(13, bold=True).render(self.flight.code, True, WHITE)
        screen.blit(code_lbl, (x0, self.rect.y + 4))

        dest_lbl = get_font(12).render(self.flight.destination, True, MUTED)
        screen.blit(dest_lbl, (x0, self.rect.y + 22))

        x1 = x0 + 110
        status_lbl = get_font(13, bold=True).render(self.flight.status, True, color)
        screen.blit(status_lbl, (x1, self.rect.y + 4))

        time_str = self.flight.scheduled_time
        if self.flight.delay > 0:
            time_str += f" +{self.flight.delay}"
        time_lbl = get_font(12).render(time_str, True, MUTED)
        screen.blit(time_lbl, (x1, self.rect.y + 22))

        gw = self.rect.width - 230
        if gw > 60:
            gate_lbl = get_font(12).render(f"Puerta {self.flight.gate}" if self.flight.gate else "", True, CYAN)
            screen.blit(gate_lbl, (x1 + 90, self.rect.y + 4))

            pax_lbl = get_font(11).render(f"{self.flight.passengers}pax", True, MUTED)
            screen.blit(pax_lbl, (x1 + 90, self.rect.y + 22))

        if is_new:
            new_lbl = get_font(10, bold=True).render("NUEVO", True, YELLOW)
            screen.blit(new_lbl, (self.rect.x + self.rect.width - 48, self.rect.y + 4))


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
        max_visible = max(1, (self.rect.height - 44) // (FlightCard.HEIGHT + FlightCard.GAP))
        self.scroll_offset = min(self.scroll_offset, max(0, self.total_count - max_visible))
        self.scroll_offset = max(0, self.scroll_offset)
        shown = self.all_flights[self.scroll_offset:self.scroll_offset + max_visible]

        self.cards.clear()
        card_w = self.rect.width - 20
        y_offset = self.rect.y + 36
        for f in shown:
            card_rect = pygame.Rect(self.rect.x + 10, y_offset, card_w, FlightCard.HEIGHT)
            self.cards.append(FlightCard(f, card_rect))
            y_offset += FlightCard.HEIGHT + FlightCard.GAP

    def draw(self, screen: pygame.Surface, changed_codes: set):
        pygame.draw.rect(screen, PANEL_BG, self.rect, border_radius=8)
        pygame.draw.rect(screen, PANEL_BORDER, self.rect, 2, border_radius=8)

        title_lbl = get_font(15, bold=True).render(f"{self.title} ({self.total_count})", True, ACCENT)
        screen.blit(title_lbl, (self.rect.x + 10, self.rect.y + 7))

        # clip to panel area
        clip_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 32, self.rect.width - 4, self.rect.height - 36)
        old_clip = screen.get_clip()
        screen.set_clip(clip_rect)

        for card in self.cards:
            card.draw(screen, card.flight.code in changed_codes)

        screen.set_clip(old_clip)

        # scroll indicators
        if self.scroll_offset > 0:
            up_lbl = get_font(11).render("▲", True, MUTED)
            screen.blit(up_lbl, (self.rect.right - 16, self.rect.y + 34))
        if self.scroll_offset + len(self.cards) < self.total_count:
            dn_lbl = get_font(11).render("▼", True, MUTED)
            screen.blit(dn_lbl, (self.rect.right - 16, self.rect.bottom - 18))

    def scroll(self, direction: int):
        max_visible = max(1, (self.rect.height - 44) // (FlightCard.HEIGHT + FlightCard.GAP))
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
        self.planes = []
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
        # outer glow
        for i in range(5, 0, -1):
            alpha = 15 // i
            pygame.draw.circle(screen, (0, 60 // i, 20 // i), (self.cx, self.cy), r + i * 2, 1)

        pygame.draw.circle(screen, RADAR_GREEN, (self.cx, self.cy), r, 2)
        pygame.draw.circle(screen, RADAR_DIM, (self.cx, self.cy), int(r * 0.66), 1)
        pygame.draw.circle(screen, RADAR_DIM, (self.cx, self.cy), int(r * 0.33), 1)

        # crosshairs
        pygame.draw.line(screen, RADAR_DIM, (self.cx - r, self.cy), (self.cx + r, self.cy), 1)
        pygame.draw.line(screen, RADAR_DIM, (self.cx, self.cy - r), (self.cx, self.cy + r), 1)

        # sweep line
        sx = self.cx + r * math.cos(self.sweep_angle)
        sy = self.cy + r * math.sin(self.sweep_angle)
        pygame.draw.line(screen, (0, 200, 60), (self.cx, self.cy), (sx, sy), 2)

        # sweep gradient effect
        for i in range(30):
            a = self.sweep_angle - i * 0.01
            if a < 0:
                a += 2 * math.pi
            ax = self.cx + r * math.cos(a)
            ay = self.cy + r * math.sin(a)
            alpha = max(0, 60 - i * 2)
            if alpha > 0:
                pygame.draw.line(screen, (0, alpha // 2, alpha // 4), (self.cx, self.cy), (ax, ay), 1)

        # trails
        for trail in self.trails:
            for j, (tx, ty) in enumerate(trail):
                t = j / len(trail)
                size = max(1, int(3 * t))
                pygame.draw.circle(screen, (0, int(60 * t), int(20 * t)), (int(tx), int(ty)), size)

        # planes
        for i, p in enumerate(self.planes):
            px = int(self.cx + p["dist"] * math.cos(p["angle"]))
            py = int(self.cy + p["dist"] * math.sin(p["angle"]))
            blink = int(abs(math.sin(self.sweep_angle * 3 + i)) * 200 + 55)
            pygame.draw.circle(screen, (blink, 255, blink), (px, py), 5)
            pygame.draw.circle(screen, (blink, 255, blink), (px, py), 7, 1)
            lbl = get_font(11).render(p["code"], True, (150, 255, 150))
            screen.blit(lbl, (px + 8, py + 6))

        lbl = get_font(14, bold=True).render("RADAR", True, RADAR_GREEN)
        screen.blit(lbl, (self.cx - 28, self.cy - r - 22))


class DetailPanel:
    def __init__(self):
        self.flight: Optional[Flight] = None
        self.rect = pygame.Rect(0, 0, 420, 540)
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
        overlay.set_alpha(140)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (20, 20, 55), self.rect, border_radius=14)
        pygame.draw.rect(screen, (60, 60, 120), self.rect, 2, border_radius=14)

        f = self.flight
        color = STATUS_COLORS.get(f.status, WHITE)
        title = get_font(26, bold=True).render(f"{f.code} - {f.destination}", True, YELLOW)
        screen.blit(title, (self.rect.x + 25, self.rect.y + 18))

        status_lbl = get_font(20, bold=True).render(f"Status: {f.status}", True, color)
        screen.blit(status_lbl, (self.rect.x + 25, self.rect.y + 55))

        info_lines = f.info_lines()[2:]
        y = self.rect.y + 88
        for line in info_lines:
            lbl = get_font(16).render(line, True, WHITE)
            screen.blit(lbl, (self.rect.x + 25, y))
            y += 26

        # Progress bar
        y += 6
        bar_x, bar_y = self.rect.x + 25, y
        bar_w, bar_h = 370, 14
        pygame.draw.rect(screen, (40, 40, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=7)
        fill_w = int(bar_w * f.progress / 100)
        fill_color = GREEN if f.progress < 80 else (ORANGE if f.progress < 95 else RED)
        if fill_w > 0:
            pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=7)
        pct_lbl = get_font(12).render(f"Progreso: {f.progress}%", True, WHITE)
        screen.blit(pct_lbl, (bar_x + 6, bar_y - 1))
        y += 24

        # Delay reason
        if delay_reason:
            dr_lbl = get_font(14).render(f"Causa: {delay_reason}", True, ORANGE)
            screen.blit(dr_lbl, (self.rect.x + 25, y))
            y += 28

        # Action buttons
        y += 8
        sep = y - 6
        pygame.draw.line(screen, (50, 50, 90), (self.rect.x + 25, sep), (self.rect.x + 395, sep), 1)
        action_title = get_font(16, bold=True).render("Acciones:", True, ACCENT)
        screen.blit(action_title, (self.rect.x + 25, y))
        y += 30

        self.action_rects = []
        actions = []
        if f.status != "Cancelado":
            if f.direction == "Salida":
                states = ["Programado", "Abordando", "Despegó"]
            else:
                states = ["En vuelo", "Aterrizó", "En puerta"]
            for i, s in enumerate(states):
                if s != f.status:
                    actions.append(("Cambiar a " + s, s))
            actions.append(("+5 min demora", "delay5"))
            actions.append(("+15 min demora", "delay15"))
            if f.delay > 0:
                actions.append(("Quitar demora", "cleardelay"))
            if f.status != "Retardado":
                actions.append(("Marcar Retardado", "retardado"))
            actions.append(("Cancelar vuelo", "cancelar"))

        for i, (label, action) in enumerate(actions):
            ax = self.rect.x + 25 + (i % 2) * 195
            ay = y + (i // 2) * 32
            ar = pygame.Rect(ax, ay, 185, 27)
            is_hover = (self.action_hover == (label, action))
            btn_c = ACCENT if "delay" not in action and "cancelar" not in action else \
                     RED if action == "cancelar" else ORANGE
            if "retardado" in action:
                btn_c = RED
            if "cleardelay" in action:
                btn_c = GREEN
            if is_hover:
                btn_c = tuple(min(255, c + 40) for c in btn_c)
            pygame.draw.rect(screen, btn_c, ar, border_radius=4)
            pygame.draw.rect(screen, WHITE, ar, 1, border_radius=4)
            albl = get_font(12, bold=True).render(label, True, WHITE)
            screen.blit(albl, (ar.centerx - albl.get_width() // 2, ar.centery - albl.get_height() // 2))
            self.action_rects.append((ar, action, f))

        close_lbl = get_font(14, bold=True).render("Click fuera para cerrar", True, MUTED)
        screen.blit(close_lbl, (self.rect.x + 25, self.rect.y + self.rect.height - 32))

    def handle_click(self, pos) -> Optional[tuple]:
        """Returns (action, flight) tuple if action button clicked, or None"""
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


class NotificationLog:
    def __init__(self, max_items=8):
        self.items: List[tuple] = []
        self.max_items = max_items

    def add(self, message: str, color=WHITE):
        self.items.append((message, color, pygame.time.get_ticks()))
        if len(self.items) > self.max_items:
            self.items.pop(0)

    def draw(self, screen: pygame.Surface, x: int, y: int):
        now = pygame.time.get_ticks()
        self.items = [(m, c, t) for (m, c, t) in self.items if now - t < 6000]

        if not self.items:
            return

        h = min(len(self.items), self.max_items) * 22 + 10
        w = 320
        rect = pygame.Rect(x, y - 10, w, h)
        s = pygame.Surface((w, h))
        s.set_alpha(160)
        s.fill((5, 5, 25))
        screen.blit(s, (x, y - 10))
        pygame.draw.rect(screen, (30, 30, 70), (x, y - 10, w, h), 1, border_radius=4)

        title = get_font(12, bold=True).render("Notificaciones", True, MUTED)
        screen.blit(title, (x + 6, y - 6))

        for i, (msg, col, t) in enumerate(self.items):
            age = (now - t) / 1000
            alpha = max(0.3, 1.0 - age / 6)
            r = int(col[0] * alpha + 20 * (1 - alpha))
            g = int(col[1] * alpha + 20 * (1 - alpha))
            b = int(col[2] * alpha + 20 * (1 - alpha))
            lbl = get_font(11).render(msg, True, (r, g, b))
            screen.blit(lbl, (x + 6, y + 16 + i * 22))


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
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        rect = pygame.Rect(0, 0, 500, 420)
        rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.rect(screen, (20, 20, 55), rect, border_radius=14)
        pygame.draw.rect(screen, (60, 60, 120), rect, 2, border_radius=14)

        title = get_font(26, bold=True).render("Ayuda - Controles", True, YELLOW)
        screen.blit(title, (rect.x + 30, rect.y + 20))

        shortcuts = [
            ("N", "Crear nuevo vuelo"),
            ("S", "Guardar vuelos (JSON)"),
            ("C", "Cargar vuelos (JSON)"),
            ("R", "Resetear todos los vuelos"),
            ("ESC", "Cerrar panel / diálogo"),
            ("F1", "Mostrar/ocultar esta ayuda"),
            ("Click vuelo", "Ver detalle del vuelo"),
            ("Click fuera", "Cerrar panel detalle"),
            ("Filtros", "Filtrar por Salidas/Llegadas/Todos"),
            ("Búsqueda", "Buscar por código o destino"),
        ]
        y = rect.y + 65
        for key, desc in shortcuts:
            key_lbl = get_font(16, bold=True).render(key, True, CYAN)
            screen.blit(key_lbl, (rect.x + 30, y))
            desc_lbl = get_font(16).render(desc, True, WHITE)
            screen.blit(desc_lbl, (rect.x + 150, y))
            y += 30

        close_lbl = get_font(16, bold=True).render("ESC o click fuera para cerrar", True, MUTED)
        screen.blit(close_lbl, (rect.x + 30, rect.y + rect.height - 40))


class NewFlightDialog:
    def __init__(self):
        self.active = False
        self.rect = pygame.Rect(0, 0, 500, 380)
        self.step = 0
        self.data = {"flight_type": "Nacional", "direction": "Salida", "code": "", "destination": ""}
        self.options = {
            0: ["Nacional", "Internacional"],
            1: ["Salida", "Llegada"],
        }
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
        overlay.set_alpha(140)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (25, 25, 60), self.rect, border_radius=14)
        pygame.draw.rect(screen, (70, 70, 130), self.rect, 2, border_radius=14)

        title = get_font(24, bold=True).render("Crear Nuevo Vuelo", True, YELLOW)
        screen.blit(title, (self.rect.x + 30, self.rect.y + 20))

        if self.step == 0:
            lbl = get_font(20).render("Tipo de vuelo:", True, WHITE)
            screen.blit(lbl, (self.rect.x + 30, self.rect.y + 80))
            for i, opt in enumerate(self.options[0]):
                bx = self.rect.x + 40 + i * 220
                by = self.rect.y + 120
                sel = opt == self.data["flight_type"]
                c = ACCENT if sel else (50, 50, 80)
                pygame.draw.rect(screen, c, (bx, by, 200, 40), border_radius=6)
                pygame.draw.rect(screen, WHITE, (bx, by, 200, 40), 1 if not sel else 2, border_radius=6)
                lbl2 = get_font(18, bold=sel).render(opt, True, WHITE)
                screen.blit(lbl2, (bx + 100 - lbl2.get_width() // 2, by + 10))
        elif self.step == 1:
            lbl = get_font(20).render("Dirección del vuelo:", True, WHITE)
            screen.blit(lbl, (self.rect.x + 30, self.rect.y + 80))
            for i, opt in enumerate(self.options[1]):
                bx = self.rect.x + 40 + i * 220
                by = self.rect.y + 120
                sel = opt == self.data["direction"]
                c = ACCENT if sel else (50, 50, 80)
                pygame.draw.rect(screen, c, (bx, by, 200, 40), border_radius=6)
                pygame.draw.rect(screen, WHITE, (bx, by, 200, 40), 1 if not sel else 2, border_radius=6)
                lbl2 = get_font(18, bold=sel).render(opt, True, WHITE)
                screen.blit(lbl2, (bx + 100 - lbl2.get_width() // 2, by + 10))
        elif self.step == 2:
            lbl = get_font(20).render("Código de vuelo:", True, WHITE)
            screen.blit(lbl, (self.rect.x + 30, self.rect.y + 80))
            inp_rect = pygame.Rect(self.rect.x + 30, self.rect.y + 120, 440, 40)
            c = ACCENT if self.input_active else PANEL_BORDER
            pygame.draw.rect(screen, (12, 12, 38), inp_rect, border_radius=6)
            pygame.draw.rect(screen, c, inp_rect, 2, border_radius=6)
            display = self.data["code"] + ("|" if self.input_active else "")
            inp_lbl = get_font(22).render(display, True, WHITE)
            screen.blit(inp_lbl, (inp_rect.x + 8, inp_rect.y + 8))
        elif self.step == 3:
            lbl = get_font(20).render("Destino:", True, WHITE)
            screen.blit(lbl, (self.rect.x + 30, self.rect.y + 80))
            inp_rect = pygame.Rect(self.rect.x + 30, self.rect.y + 120, 440, 40)
            c = ACCENT if self.input_active else PANEL_BORDER
            pygame.draw.rect(screen, (12, 12, 38), inp_rect, border_radius=6)
            pygame.draw.rect(screen, c, inp_rect, 2, border_radius=6)
            display = self.data["destination"] + ("|" if self.input_active else "")
            inp_lbl = get_font(22).render(display, True, WHITE)
            screen.blit(inp_lbl, (inp_rect.x + 8, inp_rect.y + 8))

        # nav buttons
        nav_y = self.rect.y + self.rect.height - 55
        if self.step > 0:
            back_btn = Button(self.rect.x + 30, nav_y, 120, 36, "Atras", (80, 80, 80))
            setattr(self, '_back_btn', back_btn)
            back_btn.draw(screen)
        if self.step < 3:
            next_btn = Button(self.rect.x + 350, nav_y, 120, 36, "Siguiente", ACCENT)
        else:
            next_btn = Button(self.rect.x + 350, nav_y, 120, 36, "Crear", GREEN)
        setattr(self, '_next_btn', next_btn)
        next_btn.draw(screen)

    def handle_event(self, event) -> Optional[Flight]:
        if not self.active:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if not self.rect.collidepoint(pos):
                self.close()
                return None

            # check option clicks
            if self.step == 0:
                for i, opt in enumerate(self.options[0]):
                    bx = self.rect.x + 40 + i * 220
                    by = self.rect.y + 120
                    if pygame.Rect(bx, by, 200, 40).collidepoint(pos):
                        self.data["flight_type"] = opt
                        return None
            elif self.step == 1:
                for i, opt in enumerate(self.options[1]):
                    bx = self.rect.x + 40 + i * 220
                    by = self.rect.y + 120
                    if pygame.Rect(bx, by, 200, 40).collidepoint(pos):
                        self.data["direction"] = opt
                        return None

            # input fields focus
            if self.step in [2, 3]:
                inp_rect = pygame.Rect(self.rect.x + 30, self.rect.y + 120, 440, 40)
                self.input_active = inp_rect.collidepoint(pos)

            # back button
            if self.step > 0:
                bx = self.rect.x + 30
                if pygame.Rect(bx, nav_y_val := self.rect.y + self.rect.height - 55, 120, 36).collidepoint(pos):
                    self.step -= 1
                    return None

            # next/create button
            if self.step < 3:
                nx = self.rect.x + 350
            else:
                nx = self.rect.x + 350
            if pygame.Rect(nx, self.rect.y + self.rect.height - 55, 120, 36).collidepoint(pos):
                if self.step == 2 and not self.data["code"]:
                    return None
                if self.step == 3 and not self.data["destination"]:
                    return None
                if self.step < 3:
                    self.step += 1
                    if self.step in [2, 3]:
                        self.input_active = True
                    return None
                else:
                    # create the flight
                    import time as ttime
                    f = Flight(
                        code=self.data["code"],
                        destination=self.data["destination"],
                        flight_type=self.data["flight_type"],
                        direction=self.data["direction"],
                        status="Programado" if self.data["direction"] == "Salida" else "En vuelo",
                        passengers=random.randint(50, 200),
                        scheduled_time=ttime.strftime("%H:%M"),
                    )
                    self.close()
                    return f
        if event.type == pygame.KEYDOWN and self.input_active and self.step in [2, 3]:
            key = self.step
            if event.key == pygame.K_BACKSPACE:
                if key == 2:
                    self.data["code"] = self.data["code"][:-1]
                else:
                    self.data["destination"] = self.data["destination"][:-1]
            elif event.key == pygame.K_RETURN:
                if key == 2 and self.data["code"]:
                    self.step = 3
                    self.input_active = True
                elif key == 3 and self.data["destination"]:
                    pass  # would need to trigger create
            elif event.unicode.isprintable():
                if key == 2:
                    self.data["code"] += event.unicode.upper()
                else:
                    self.data["destination"] += event.unicode
        return None
