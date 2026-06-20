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


class Tooltip:
    def __init__(self):
        self.text = ""
        self.anchor = pygame.Rect(0, 0, 0, 0)
        self.visible = False

    def show(self, text: str, rect: pygame.Rect):
        self.text = text
        self.anchor = rect
        self.visible = True

    def hide(self):
        self.visible = False

    def draw(self, screen: pygame.Surface, mouse_pos: tuple):
        if not self.visible:
            return
        if not self.anchor.collidepoint(mouse_pos):
            self.hide()
            return
        lbl = get_font(11).render(self.text, True, TEXT_PRIMARY)
        tw, th = lbl.get_width() + 12, lbl.get_height() + 8
        tx = min(mouse_pos[0] + 14, SCREEN_WIDTH - tw - 6)
        ty = mouse_pos[1] - th - 10
        if ty < 0:
            ty = mouse_pos[1] + 14
        s = pygame.Surface((tw, th))
        s.set_alpha(235)
        s.fill((16, 16, 40))
        screen.blit(s, (tx, ty))
        pygame.draw.rect(screen, BORDER_LIGHT, (tx, ty, tw, th), 1, border_radius=4)
        screen.blit(lbl, (tx + 6, ty + (th - lbl.get_height()) // 2))


class TopBar:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, SCREEN_WIDTH, 64)
        self.pause_rect = pygame.Rect(0, 0, 0, 0)
        self.speed_btn_rects: List[tuple] = []
        self.airport_rect = pygame.Rect(0, 0, 0, 0)
        self.airport_index = 0

    def draw(self, screen: pygame.Surface, stats: dict, current_speed: int = 1, airport_list: list = None, current_airport: str = "BOG"):
        pygame.draw.rect(screen, (10, 10, 30), self.rect)
        pygame.draw.line(screen, BORDER, (0, 64), (SCREEN_WIDTH, 64), 1)
        pygame.draw.line(screen, (20, 20, 48), (0, 63), (SCREEN_WIDTH, 63), 1)

        title = get_font(22, bold=True).render(f"Aeropuerto IA  ·  {current_airport}", True, TEXT_PRIMARY)
        screen.blit(title, (24, 12))
        sub = get_font(11).render("Sistema de Control Distributivo", True, TEXT_MUTED)
        screen.blit(sub, (26, 42))

        sim_time = stats.get("time", "06:00")
        st_bg = pygame.Rect(270, 14, 90, 34)
        rounded_rect(screen, BG_PANEL, st_bg, 6)
        pygame.draw.rect(screen, BORDER, st_bg, 1, border_radius=6)
        st_lbl = get_font(18, bold=True).render(sim_time, True, ACCENT_TEAL)
        screen.blit(st_lbl, (st_bg.centerx - st_lbl.get_width() // 2, st_bg.centery - st_lbl.get_height() // 2))

        weather = stats.get("weather", "Despejado")
        w_icon = {"Despejado": "☀", "Nublado": "☁", "Lluvioso": "☂", "Tormenta": "⚡"}.get(weather, "☀")
        w_color = {"Despejado": YELLOW, "Nublado": TEXT_MUTED, "Lluvioso": ACCENT_TEAL, "Tormenta": RED}.get(weather, TEXT_PRIMARY)
        w_bg = pygame.Rect(372, 14, 100, 34)
        rounded_rect(screen, BG_PANEL, w_bg, 6)
        pygame.draw.rect(screen, BORDER, w_bg, 1, border_radius=6)
        w_lbl = get_font(13).render(f"{w_icon} {weather}", True, w_color)
        screen.blit(w_lbl, (w_bg.centerx - w_lbl.get_width() // 2, w_bg.centery - w_lbl.get_height() // 2))

        # Airport selector
        ap_x, ap_y = 484, 14
        ap_w, ap_h = 96, 34
        self.airport_rect = pygame.Rect(ap_x, ap_y, ap_w, ap_h)
        rounded_rect(screen, BG_PANEL, self.airport_rect, 6)
        pygame.draw.rect(screen, ACCENT, self.airport_rect, 1, border_radius=6)
        from config import AIRPORTS
        ap_name = AIRPORTS.get(current_airport, ("???", (100, 100, 100)))[0]
        ap_lbl = get_font(12, bold=True).render(f"{current_airport}", True, ACCENT)
        screen.blit(ap_lbl, (self.airport_rect.centerx - ap_lbl.get_width() // 2, self.airport_rect.centery - ap_lbl.get_height() // 2 - 4))
        ap_name_lbl = get_font(8).render(ap_name, True, TEXT_MUTED)
        screen.blit(ap_name_lbl, (self.airport_rect.centerx - ap_name_lbl.get_width() // 2, self.airport_rect.centery + 4))

        stats_x = 592
        items = [
            (f"Total: {stats.get('total', 0)}", TEXT_PRIMARY),
            (f"A tiempo: {stats.get('on_time', 0)}", GREEN),
            (f"Demorados: {stats.get('delayed', 0)}", ORANGE),
            (f"Cancelados: {stats.get('cancelled', 0)}", RED),
            (f"Demora: {stats.get('avg_delay', 0)}min", TEXT_MUTED),
        ]
        for i, (txt, col) in enumerate(items):
            bg = pygame.Rect(stats_x + i * 122, 14, 114, 34)
            rounded_rect(screen, BG_PANEL, bg, 6)
            pygame.draw.rect(screen, BORDER, bg, 1, border_radius=6)
            lbl = get_font(11).render(txt, True, col)
            screen.blit(lbl, (bg.centerx - lbl.get_width() // 2, bg.centery - lbl.get_height() // 2))

        # Speed controls
        px, py = SCREEN_WIDTH - 220, 14
        pw, ph = 30, 34
        self.pause_rect = pygame.Rect(px, py, pw, ph)
        pause_color = ACCENT if current_speed == 0 else TEXT_MUTED
        rounded_rect(screen, BG_PANEL, self.pause_rect, 6)
        pygame.draw.rect(screen, BORDER, self.pause_rect, 1, border_radius=6)
        pause_icon = "▶" if current_speed == 0 else "⏸"
        plbl = get_font(14).render(pause_icon, True, pause_color)
        screen.blit(plbl, (px + pw//2 - plbl.get_width()//2, py + ph//2 - plbl.get_height()//2))

        self.speed_btn_rects = []
        for i, s in enumerate(SPEEDS):
            bx = px + pw + 5 + i * 43
            br = pygame.Rect(bx, py, 37, ph)
            self.speed_btn_rects.append((br, s))
            active = current_speed == s
            c = ACCENT if active else BG_PANEL
            rounded_rect(screen, c, br, 6)
            bc = ACCENT if active else BORDER
            pygame.draw.rect(screen, bc, br, 1, border_radius=6)
            lbl = get_font(11, bold=active).render(f"{s}×", True, TEXT_PRIMARY if active else TEXT_MUTED)
            screen.blit(lbl, (br.centerx - lbl.get_width()//2, br.centery - lbl.get_height()//2))


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
        self.sort_key = "code"
        self.sort_asc = True

    def toggle_sort(self, key: str):
        if self.sort_key == key:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_key = key
            self.sort_asc = True

    def header_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 26)

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

        key_map = {
            "code": lambda f: f.code,
            "time": lambda f: f.scheduled_time,
            "status": lambda f: (
                ["Programado", "Abordando", "Despegó", "En vuelo", "Aterrizó", "En puerta", "Retardado", "Cancelado"]
                .index(f.status) if f.status in [
                    "Programado", "Abordando", "Despegó", "En vuelo", "Aterrizó", "En puerta", "Retardado", "Cancelado"]
                else 99
            ),
        }
        key_fn = key_map.get(self.sort_key, lambda f: f.code)
        self.all_flights.sort(key=key_fn, reverse=not self.sort_asc)

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

        sort_names = {"code": "Código", "time": "Hora", "status": "Estado"}
        sort_arrow = "▲" if self.sort_asc else "▼"
        sort_text = get_font(9).render(f"{sort_arrow} {sort_names.get(self.sort_key, self.sort_key)}", True, ACCENT_TEAL)
        screen.blit(sort_text, (self.rect.right - sort_text.get_width() - 10, self.rect.y + 10))

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


class AirportMap:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.rect = pygame.Rect(x, y, w, h)
        self.gates: List[dict] = []
        self._init_layout()

    def _init_layout(self):
        r = self.rect
        # Terminal
        self.terminal_rect = pygame.Rect(r.x + 10, r.y + 10, r.w - 20, 40)
        # Gate positions — departures (top row), arrivals (bottom row)
        self.gate_positions = []
        dep_gates = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]
        arr_gates = ["X1", "X2", "X3", "Y1", "Y2", "Y3", "Z1", "Z2", "Z3"]
        n = max(len(dep_gates), len(arr_gates))
        spacing = (r.w - 32) / n
        for i, label in enumerate(dep_gates):
            gx = r.x + 16 + int(i * spacing)
            gy = r.y + 56
            self.gate_positions.append({"label": label, "x": gx, "y": gy, "type": "dep"})
        for i, label in enumerate(arr_gates):
            gx = r.x + 16 + int(i * spacing)
            gy = r.y + 76
            self.gate_positions.append({"label": label, "x": gx, "y": gy, "type": "arr"})
        # Taxiway
        self.taxiway_y = r.y + 105
        # Runway
        self.runway_rect = pygame.Rect(r.x + 10, r.y + r.h - 40, r.w - 20, 14)

    def update(self):
        pass

    def get_plane_positions(self, flights) -> List[dict]:
        visible = []
        for f in flights:
            if f.status in ("Cancelado",):
                continue
            progress = f.progress
            # Find which gate position this flight is at
            gate_idx = -1
            for i, gp in enumerate(self.gate_positions):
                if gp["label"] == f.gate:
                    gate_idx = i
                    break
            if gate_idx < 0:
                continue

            gp = self.gate_positions[gate_idx]
            r = self.rect

            if f.direction == "Salida":
                # At gate (0-30%), taxi (30-50%), runway (50-65%), airborne (65%+)
                if progress < 30:
                    phase = "gate"
                    px = gp["x"]
                    py = gp["y"]
                elif progress < 45:
                    phase = "taxi"
                    t = (progress - 30) / 15
                    px = gp["x"] + (r.x + r.w // 2 - gp["x"]) * t
                    py = gp["y"] + (self.taxiway_y - gp["y"]) * t
                elif progress < 60:
                    phase = "runway"
                    t = (progress - 45) / 15
                    px = r.x + r.w // 2
                    py = self.taxiway_y + (self.runway_rect.centery - self.taxiway_y) * t
                else:
                    phase = "airborne"
                    px = r.x + r.w // 2 + (progress - 60) * 3
                    py = self.runway_rect.centery - (progress - 60) * 2
            else:
                # Airborne (0-30%), approach (30-45%), landing (45-60%), taxi (60-80%), gate (80%+)
                if progress < 30:
                    phase = "airborne"
                    px = r.x + r.w // 2 - (30 - progress) * 3
                    py = self.runway_rect.centery - 40 + progress * 0.5
                elif progress < 50:
                    phase = "landing"
                    t = (progress - 30) / 20
                    px = r.x + r.w // 2 - (1 - t) * 40
                    py = self.runway_rect.centery + (self.taxiway_y - self.runway_rect.centery) * t
                elif progress < 75:
                    phase = "taxi"
                    t = (progress - 50) / 25
                    px = r.x + r.w // 2 + (gp["x"] - r.x - r.w // 2) * t
                    py = self.taxiway_y + (gp["y"] - self.taxiway_y) * t
                else:
                    phase = "gate"
                    px = gp["x"]
                    py = gp["y"]

            visible.append({
                "code": f.code,
                "x": px, "y": py,
                "color": STATUS_COLORS.get(f.status, TEXT_PRIMARY),
                "phase": phase,
                "status": f.status,
                "gate": f.gate,
                "direction": f.direction,
            })
        return visible

    def draw(self, screen: pygame.Surface, flights):
        r = self.rect
        draw_shadow(screen, r, radius=8, alpha=25)

        # Background
        rounded_rect(screen, (12, 12, 30), r, 8)
        pygame.draw.rect(screen, BORDER, r, 1, border_radius=8)

        # Grass area
        grass = r.inflate(-6, -6)
        rounded_rect(screen, (16, 24, 18), grass, 6)

        # Runway
        rwy = self.runway_rect
        rounded_rect(screen, (35, 35, 50), rwy, 3)
        pygame.draw.rect(screen, (60, 60, 85), rwy, 1, border_radius=3)
        for i in range(0, rwy.w - 8, 14):
            pygame.draw.rect(screen, (90, 90, 120), (rwy.x + 6 + i, rwy.centery - 1, 6, 2))

        # Taxiway center line
        pygame.draw.line(screen, (40, 40, 60), (r.x + 16, self.taxiway_y), (r.right - 16, self.taxiway_y), 1)
        for i in range(0, r.w - 32, 16):
            x = r.x + 16 + i
            pygame.draw.rect(screen, (60, 60, 40), (x, self.taxiway_y - 1, 8, 2))

        # Terminal
        t = self.terminal_rect
        rounded_rect(screen, (25, 25, 55), t, 4)
        pygame.draw.rect(screen, BORDER, t, 1, border_radius=4)
        # Windows
        for wx in range(t.x + 8, t.right - 8, 16):
            pygame.draw.rect(screen, (60, 60, 40), (wx, t.y + 10, 6, 6))
        lbl = get_font(9, bold=True).render("TERMINAL", True, TEXT_MUTED)
        screen.blit(lbl, (t.centerx - lbl.get_width() // 2, t.centery - lbl.get_height() // 2))

        # Gates
        for gp in self.gate_positions:
            gc = ACCENT if gp["type"] == "dep" else ACCENT_TEAL
            pygame.draw.rect(screen, gc, (gp["x"] - 8, gp["y"] - 4, 16, 8), 1, border_radius=2)
            gl = get_font(7, bold=True).render(gp["label"], True, gc)
            screen.blit(gl, (gp["x"] - gl.get_width() // 2, gp["y"] - 10))

        # Animated planes
        for p in self.get_plane_positions(flights):
            px, py = int(p["x"]), int(p["y"])
            if px < r.x or px > r.right or py < r.y or py > r.bottom:
                continue
            c = p["color"]
            pygame.draw.circle(screen, c, (px, py), 5)
            pygame.draw.circle(screen, (c[0] // 2, c[1] // 2, c[2] // 2), (px, py), 7, 1)
            lbl = get_font(8).render(p["code"], True, c)
            screen.blit(lbl, (px + 9, py - 4))

        # Title + airport code
        title = get_font(10, bold=True).render("AEROPUERTO", True, ACCENT_TEAL)
        screen.blit(title, (r.x + 8, r.y + r.h - 16))
        from config import AIRPORTS
        subtitle = get_font(8).render("BOG · Centro de Control", True, TEXT_MUTED)
        screen.blit(subtitle, (r.x + 8, r.y + r.h - 30))


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
        stage_name = {"": "—", "check-in": "Check-in", "seguridad": "Seguridad", "sala": "Sala de espera",
                       "abordaje": "Abordando", "a bordo": "A bordo", "en vuelo": "En vuelo",
                       "desembarque": "Desembarcando", "llegada": "Llegada"}
        info = [
            ("Estado", f.status, color),
            ("Tipo", f"{f.flight_type} · {f.direction}", TEXT_SECONDARY),
            ("Pasajeros", str(f.passengers), TEXT_PRIMARY),
            ("Hora", f.scheduled_time, TEXT_PRIMARY),
            ("Puerta", f.gate if f.gate else "Sin asignar", ACCENT_TEAL if f.gate else TEXT_MUTED),
            ("Demora", f"{f.delay} min" if f.delay > 0 else "0 min", ORANGE if f.delay > 0 else TEXT_MUTED),
            ("Progreso", f"{f.progress}%", TEXT_PRIMARY),
            ("Pasajeros", stage_name.get(f.passenger_stage, f.passenger_stage), ACCENT_PURPLE if f.passenger_stage else TEXT_MUTED),
        ]
        if f.destination_airport:
            from config import AIRPORTS
            ap_info = AIRPORTS.get(f.destination_airport)
            if ap_info:
                info.insert(4, ("Destino", f"{f.destination} ({f.destination_airport})", TEXT_PRIMARY))
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
            ("F2", "Estadísticas del aeropuerto"),
            ("F3", "Panel FIDS (como aeropuerto real)"),
            ("F11", "Pantalla completa"),
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


class StatsOverlay:
    def __init__(self):
        self.active = False

    def toggle(self):
        self.active = not self.active

    def close(self):
        self.active = False

    def draw(self, screen: pygame.Surface, flights: List[Flight], ai_stats: dict):
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 10))
        screen.blit(overlay, (0, 0))

        rect = pygame.Rect(0, 0, 520, 420)
        rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        draw_shadow(screen, rect, radius=14, alpha=60)
        rounded_rect(screen, (16, 16, 40), rect, 14)
        pygame.draw.rect(screen, BORDER_LIGHT, rect, 1, border_radius=14)

        title = get_font(20, bold=True).render("Estadísticas del Aeropuerto", True, TEXT_PRIMARY)
        screen.blit(title, (rect.x + 30, rect.y + 20))
        pygame.draw.line(screen, BORDER, (rect.x + 30, rect.y + 52), (rect.right - 30, rect.y + 52), 1)

        status_counts = {}
        for f in flights:
            status_counts[f.status] = status_counts.get(f.status, 0) + 1

        y = rect.y + 68
        left_items = [
            ("Total vuelos", str(ai_stats.get("total", 0)), TEXT_PRIMARY),
            ("A tiempo", str(ai_stats.get("on_time", 0)), GREEN),
            ("Demorados", str(ai_stats.get("delayed", 0)), ORANGE),
            ("Cancelados", str(ai_stats.get("cancelled", 0)), RED),
            ("Demora promedio", f"{ai_stats.get('avg_delay', 0)} min", TEXT_MUTED),
        ]
        for label, value, color in left_items:
            lbl = get_font(12).render(label, True, TEXT_MUTED)
            screen.blit(lbl, (rect.x + 30, y))
            vl = get_font(13, bold=True).render(value, True, color)
            screen.blit(vl, (rect.x + 170, y))
            y += 26

        right_x = rect.x + 280
        y2 = rect.y + 68
        right_items = [
            ("Clima", ai_stats.get("weather", "Despejado"), TEXT_PRIMARY),
            ("Hora", ai_stats.get("time", "06:00"), ACCENT_TEAL),
            ("Puertas usadas", f"{ai_stats.get('gates_used', 0)}/{ai_stats.get('gates_total', 0)}", ACCENT),
        ]
        for label, value, color in right_items:
            lbl = get_font(12).render(label, True, TEXT_MUTED)
            screen.blit(lbl, (right_x, y2))
            vl = get_font(13, bold=True).render(value, True, color)
            screen.blit(vl, (right_x + 130, y2))
            y2 += 26

        # Status breakdown — bar chart
        y = max(y, y2) + 16
        pygame.draw.line(screen, BORDER, (rect.x + 30, y - 4), (rect.right - 30, y - 4), 1)
        status_title = get_font(12, bold=True).render("Estado de vuelos", True, TEXT_SECONDARY)
        screen.blit(status_title, (rect.x + 30, y))
        y += 24

        sorted_status = sorted(status_counts.items(), key=lambda x: -x[1])
        max_cnt = max((c for _, c in sorted_status), default=1)
        chart_w = rect.w - 60
        bar_h = 22
        bar_gap = 4
        for i, (st, cnt) in enumerate(sorted_status):
            by = y + i * (bar_h + bar_gap)
            c = STATUS_COLORS.get(st, TEXT_PRIMARY)
            bw = int((cnt / max_cnt) * chart_w) if max_cnt > 0 else 0
            # bar background
            bar_bg = pygame.Rect(rect.x + 30, by, chart_w, bar_h)
            pygame.draw.rect(screen, (15, 15, 35), bar_bg, border_radius=3)
            # bar fill
            if bw > 0:
                bar_fill = pygame.Rect(rect.x + 30, by, max(bw, 4), bar_h)
                pygame.draw.rect(screen, (c[0]//2, c[1]//2, c[2]//2), bar_fill, border_radius=3)
                bar_fill2 = pygame.Rect(rect.x + 30, by, bw, bar_h)
                grad = pygame.Rect(rect.x + 30, by, bw, bar_h // 2)
                pygame.draw.rect(screen, c, bar_fill2, border_radius=3)
                pygame.draw.rect(screen, (min(255, c[0]+60), min(255, c[1]+60), min(255, c[2]+60)), grad, border_radius=3)
            # label on top of bar
            lbl = get_font(11, bold=True).render(f"{st}: {cnt}", True, TEXT_PRIMARY)
            screen.blit(lbl, (rect.x + 36, by + 2))

        cl = get_font(11).render("F2 o ESC para cerrar", True, TEXT_MUTED)
        screen.blit(cl, (rect.x + 30, rect.y + rect.height - 30))


class FIDSDisplay:
    AIRLINES = {
        "AV": "Avianca", "IB": "Iberia", "AF": "Air France",
        "UA": "United", "LH": "Lufthansa", "BA": "British Airways",
        "CM": "Copa Airlines", "AA": "American Airlines",
        "DL": "Delta", "AC": "Air Canada", "KL": "KLM",
        "TK": "Turkish Airlines", "QR": "Qatar Airways",
        "EK": "Emirates", "AZ": "ITA Airways", "TP": "TAP Portugal",
    }

    def __init__(self):
        self.active = False
        self.show_departures = True

    def toggle(self):
        self.active = not self.active

    def close(self):
        self.active = False

    def draw(self, screen: pygame.Surface, flights: List[Flight], current_airport: str):
        if not self.active:
            return

        # Full black background
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill((2, 4, 16))
        screen.blit(bg, (0, 0))

        # Top accent bar
        pygame.draw.rect(screen, (0, 110, 230), (0, 0, SCREEN_WIDTH, 3))

        # Airport name
        from config import AIRPORTS
        ap_name = AIRPORTS.get(current_airport, (current_airport, (0,0,0)))[0]
        title = get_font(28, bold=True).render(f"AEROPUERTO {ap_name.upper()}", True, (200, 215, 255))
        screen.blit(title, (40, 28))

        mode = "SALIDAS" if self.show_departures else "LLEGADAS"
        mode_lbl = get_font(20, bold=True).render(mode, True, (0, 180, 230))
        screen.blit(mode_lbl, (40, 62))

        # Separator
        pygame.draw.line(screen, (20, 35, 70), (40, 94), (SCREEN_WIDTH - 40, 94), 1)

        # Column headers
        cols = [
            (40, "VUELO", 120), (165, "AEROLÍNEA", 150), (320, "DESTINO", 200),
            (530, "PUERTA", 70), (610, "HORA", 90), (710, "DEMORA", 70),
            (790, "ESTADO", 220),
        ]
        for cx, label, cw in cols:
            hl = get_font(10, bold=True).render(label, True, (80, 100, 160))
            screen.blit(hl, (cx + 4, 104))

        # Filter flights
        filtered = [f for f in flights
                    if (self.show_departures and f.direction == "Salida") or
                       (not self.show_departures and f.direction == "Llegada")]
        filtered.sort(key=lambda f: f.scheduled_time)

        row_h = 32
        start_y = 126
        max_rows = (SCREEN_HEIGHT - start_y - 20) // row_h
        shown = filtered[:max_rows]

        for i, f in enumerate(shown):
            y = start_y + i * row_h
            # Row background
            row_bg = (6, 10, 28) if i % 2 == 0 else (10, 16, 36)
            pygame.draw.rect(screen, row_bg, (36, y, SCREEN_WIDTH - 72, row_h - 2))

            # Flight code
            code_lbl = get_font(13, bold=True).render(f.code, True, (220, 230, 255))
            screen.blit(code_lbl, (44, y + 6))

            # Airline
            prefix = f.code[:2] if f.code[:2].isalpha() else ""
            airline = self.AIRLINES.get(prefix, prefix)
            al_lbl = get_font(12).render(airline, True, (160, 175, 210))
            screen.blit(al_lbl, (169, y + 7))

            # Destination
            dest = f"{f.destination} ({f.destination_airport})" if f.destination_airport else f.destination
            dest_lbl = get_font(13, bold=True).render(dest, True, (200, 215, 255))
            screen.blit(dest_lbl, (324, y + 6))

            # Gate
            gate_str = f.gate if f.gate else "—"
            gate_lbl = get_font(13, bold=True).render(gate_str, True, (0, 200, 230))
            screen.blit(gate_lbl, (534, y + 6))

            # Time
            time_str = f.scheduled_time
            time_lbl = get_font(13).render(time_str, True, (180, 195, 230))
            screen.blit(time_lbl, (614, y + 6))

            # Delay
            if f.delay > 0:
                delay_lbl = get_font(13, bold=True).render(f"+{f.delay}", True, (255, 180, 50))
            else:
                delay_lbl = get_font(12).render("—", True, (60, 75, 110))
            screen.blit(delay_lbl, (714, y + 6))

            # Status
            sc = STATUS_COLORS.get(f.status, (180, 195, 230))
            status_bg = pygame.Rect(794, y + 5, 150, 22)
            pygame.draw.rect(screen, (sc[0]//6, sc[1]//6, sc[2]//6), status_bg, border_radius=3)
            status_lbl = get_font(11, bold=True).render(f.status, True, sc)
            screen.blit(status_lbl, (status_bg.centerx - status_lbl.get_width() // 2, status_bg.centery - status_lbl.get_height() // 2))

        # Footer bar
        pygame.draw.line(screen, (20, 35, 70), (40, SCREEN_HEIGHT - 40), (SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), 1)
        footer = get_font(11).render(f"TAB: Cambiar vista  |  F3 o ESC: Cerrar  |  {len(filtered)} vuelos", True, (70, 85, 130))
        screen.blit(footer, (40, SCREEN_HEIGHT - 30))

        # Blinking current time in top-right
        import time as ttime
        now = ttime.strftime("%H:%M:%S")
        clock_lbl = get_font(22, bold=True).render(now, True, (0, 200, 230))
        screen.blit(clock_lbl, (SCREEN_WIDTH - clock_lbl.get_width() - 40, 28))


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
