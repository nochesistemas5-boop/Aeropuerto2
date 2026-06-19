import pygame
import random
import time
import os
import sys

from config import *
from flight import Flight, save_flights, load_flights
from ai_engine import AIEngine
from ui import (
    draw_gradient, TopBar, SearchBar, FlightPanel, Radar,
    DetailPanel, NewFlightDialog, HelpOverlay, NotificationLog,
    Button, get_font
)

beep_sound = None


def init_sound():
    global beep_sound
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        sample_rate = 22050
        duration = 0.08
        n_samples = int(sample_rate * duration)
        import array
        import math as m
        buf = array.array('h', [0]) * n_samples
        for i in range(n_samples):
            val = int(0.3 * 32767 * m.sin(2 * m.pi * 800 * i / sample_rate))
            buf[i] = val
        beep_sound = pygame.mixer.Sound(buffer=buf)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Initial flights
# ---------------------------------------------------------------------------
def make_flights():
    return [
        Flight("AV101", "Medellín", "Nacional", "Salida", "Programado", 90, "06:30"),
        Flight("AV202", "Cali", "Nacional", "Salida", "Abordando", 110, "07:00"),
        Flight("AV303", "Cartagena", "Nacional", "Llegada", "En vuelo", 75, "06:45", delay=10),
        Flight("AV404", "Bogotá", "Nacional", "Salida", "Programado", 130, "07:30"),
        Flight("AV505", "San Andrés", "Nacional", "Llegada", "En vuelo", 120, "07:15"),
        Flight("AV606", "Santa Marta", "Nacional", "Salida", "Programado", 85, "08:45"),
        Flight("AV707", "Pereira", "Nacional", "Llegada", "En vuelo", 65, "07:50"),
        Flight("AV808", "Bucaramanga", "Nacional", "Salida", "Programado", 95, "09:00"),
        Flight("AV909", "Barranquilla", "Nacional", "Llegada", "En vuelo", 105, "08:20"),
        Flight("AV110", "Cúcuta", "Nacional", "Salida", "Programado", 70, "09:30"),
        Flight("AV211", "Manizales", "Nacional", "Salida", "Programado", 80, "10:15"),
        Flight("AV312", "Neiva", "Nacional", "Llegada", "En vuelo", 55, "09:40"),
        Flight("AV413", "Armenia", "Nacional", "Salida", "Programado", 100, "10:45"),
        Flight("AV514", "Sincelejo", "Nacional", "Llegada", "En vuelo", 60, "10:00"),
        Flight("AV615", "Valledupar", "Nacional", "Salida", "Programado", 75, "11:00"),
        Flight("AV716", "Tunja", "Nacional", "Llegada", "En vuelo", 45, "10:30"),
        Flight("IB321", "Madrid", "Internacional", "Salida", "Programado", 260, "08:00"),
        Flight("AF654", "París", "Internacional", "Salida", "Programado", 290, "09:15"),
        Flight("UA555", "Nueva York", "Internacional", "Llegada", "En vuelo", 195, "07:20"),
        Flight("LH789", "Frankfurt", "Internacional", "Llegada", "En vuelo", 210, "08:30", delay=25),
        Flight("BA111", "Londres", "Internacional", "Salida", "Programado", 310, "10:00"),
        Flight("CM222", "Panamá", "Internacional", "Llegada", "En vuelo", 140, "09:00"),
        Flight("AA333", "Miami", "Internacional", "Salida", "Programado", 220, "11:30"),
        Flight("DL444", "Atlanta", "Internacional", "Salida", "Programado", 180, "12:00"),
        Flight("AC555", "Toronto", "Internacional", "Llegada", "En vuelo", 200, "10:45"),
        Flight("KL666", "Ámsterdam", "Internacional", "Salida", "Programado", 280, "13:15"),
        Flight("TK777", "Estambul", "Internacional", "Llegada", "En vuelo", 240, "11:00", delay=15),
        Flight("QR888", "Doha", "Internacional", "Salida", "Programado", 320, "14:00"),
        Flight("EK999", "Dubái", "Internacional", "Llegada", "En vuelo", 300, "12:30"),
        Flight("AZ111", "Roma", "Internacional", "Salida", "Programado", 250, "14:30"),
        Flight("TP222", "Lisboa", "Internacional", "Llegada", "En vuelo", 190, "13:00"),
        Flight("AV117", "Bogotá", "Nacional", "Salida", "Programado", 100, "07:00"),
        Flight("AV118", "Medellín", "Nacional", "Llegada", "En vuelo", 95, "06:00"),
        Flight("AV119", "Cali", "Nacional", "Llegada", "En vuelo", 110, "06:30"),
        Flight("AV120", "Leticia", "Nacional", "Salida", "Programado", 50, "11:30"),
        Flight("AV121", "Pasto", "Nacional", "Llegada", "En vuelo", 70, "11:00"),
        Flight("AV122", "Popayán", "Nacional", "Salida", "Programado", 65, "12:00"),
        Flight("AV123", "Riohacha", "Nacional", "Llegada", "En vuelo", 55, "11:45"),
        Flight("AV124", "Ibagué", "Nacional", "Salida", "Programado", 80, "12:30"),
        Flight("AV125", "Villavicencio", "Nacional", "Llegada", "En vuelo", 90, "12:15"),
    ]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    init_sound()
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Aeropuerto IA Distributiva")
    clock = pygame.time.Clock()

    flights = make_flights()
    ai = AIEngine()
    radar = Radar(1270, 400, 195)
    detail = DetailPanel()
    new_flight_dialog = NewFlightDialog()
    help_overlay = HelpOverlay()
    notifications = NotificationLog()

    top_bar = TopBar()
    search_bar = SearchBar()
    changed_codes = set()

    # panels
    panel_n_dep = FlightPanel(15, 130, 345, 300, "Salidas Nacionales")
    panel_n_arr = FlightPanel(372, 130, 345, 300, "Llegadas Nacionales")
    panel_i_dep = FlightPanel(15, 445, 345, 300, "Salidas Internacionales")
    panel_i_arr = FlightPanel(372, 445, 345, 300, "Llegadas Internacionales")
    panels = [panel_n_dep, panel_n_arr, panel_i_dep, panel_i_arr]

    # bottom bar buttons
    btn_new = Button(15, 785, 150, 28, "[N] Nuevo Vuelo", ACCENT)
    btn_save = Button(175, 785, 130, 28, "[S] Guardar", (60, 60, 60))
    btn_load = Button(315, 785, 130, 28, "[C] Cargar", (60, 60, 60))
    btn_reset = Button(455, 785, 130, 28, "[R] Reset", (80, 50, 50))

    # timer for periodic updates
    UPDATE_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(UPDATE_EVENT, UPDATE_MS)

    change_notify_start = 0
    running = True
    while running:
        dt = clock.tick(FPS)

        # -- update --
        radar.update()

        # -- draw --
        draw_gradient(screen)

        # top bar
        top_bar.draw(screen, ai.stats)

        # search bar + filter buttons
        search_bar.draw(screen)

        # update panels with current data
        for p in panels:
            if "Salidas" in p.title:
                flist = [f for f in flights if f.direction == "Salida" and
                         ((f.flight_type == "Nacional" and "Nacionales" in p.title) or
                          (f.flight_type == "Internacional" and "Internacionales" in p.title))]
            else:
                flist = [f for f in flights if f.direction == "Llegada" and
                         ((f.flight_type == "Nacional" and "Nacionales" in p.title) or
                          (f.flight_type == "Internacional" and "Internacionales" in p.title))]
            p.set_flights(flist, search_bar.text, search_bar.active_filter if hasattr(search_bar, 'active_filter') else "all")
            p.draw(screen, changed_codes)

        # radar
        radar.draw(screen)

        # bottom bar
        pygame.draw.rect(screen, (10, 10, 40), (0, 785, SCREEN_WIDTH, 35))
        pygame.draw.line(screen, PANEL_BORDER, (0, 785), (SCREEN_WIDTH, 785), 2)
        btn_new.draw(screen)
        btn_save.draw(screen)
        btn_load.draw(screen)
        btn_reset.draw(screen)

        help_lbl = get_font(13).render("F1: Ayuda  |  Click vuelo: Detalle + Acciones", True, MUTED)
        screen.blit(help_lbl, (620, 792))

        # notification log
        notifications.draw(screen, 735, 130)

        # dialogs on top
        detail.draw(screen, ai.get_delay_reason(detail.flight) if detail.flight else "")
        new_flight_dialog.draw(screen)
        help_overlay.draw(screen)

        pygame.display.flip()

        # -- events --
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == UPDATE_EVENT:
                ai.update(flights)
                changed_codes.clear()
                for f in flights:
                    if f.has_changed:
                        changed_codes.add(f.code)
                        notifications.add(f"{f.code}: {f.prev_status} → {f.status}", STATUS_COLORS.get(f.status, WHITE))
                        if beep_sound:
                            try:
                                beep_sound.play()
                            except Exception:
                                pass
                    f.ack_change()
                if changed_codes:
                    change_notify_start = pygame.time.get_ticks()

            elif event.type == pygame.KEYDOWN:
                if new_flight_dialog.active:
                    new_flight_dialog.handle_event(event)
                elif event.key == pygame.K_ESCAPE:
                    if help_overlay.active:
                        help_overlay.close()
                    else:
                        detail.hide()
                        new_flight_dialog.close()
                elif event.key == pygame.K_n:
                    new_flight_dialog.open()
                elif event.key == pygame.K_s:
                    try:
                        save_flights(flights, "vuelos.json")
                    except Exception as e:
                        print(f"Error guardando: {e}")
                elif event.key == pygame.K_c:
                    try:
                        loaded = load_flights("vuelos.json")
                        if loaded:
                            flights = loaded
                    except Exception as e:
                        print(f"Error cargando: {e}")
                elif event.key == pygame.K_r:
                    flights = make_flights()
                    ai = AIEngine()
                elif event.key == pygame.K_F1:
                    help_overlay.toggle()
                else:
                    search_bar.handle_event(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                # bottom bar buttons
                if btn_new.rect.collidepoint(pos):
                    new_flight_dialog.open()
                elif btn_save.rect.collidepoint(pos):
                    save_flights(flights, "vuelos.json")
                elif btn_load.rect.collidepoint(pos):
                    try:
                        loaded = load_flights("vuelos.json")
                        if loaded:
                            flights = loaded
                    except Exception:
                        pass
                elif btn_reset.rect.collidepoint(pos):
                    flights = make_flights()
                    ai = AIEngine()

                # filter buttons
                filters_region = [("all", pygame.Rect(380, 90, 72, 34)),
                                  ("dep", pygame.Rect(458, 90, 72, 34)),
                                  ("arr", pygame.Rect(536, 90, 72, 34))]
                for key, rect in filters_region:
                    if rect.collidepoint(pos):
                        search_bar.active_filter = key

                # detail panel click
                if detail.flight:
                    if detail.rect.collidepoint(pos):
                        action_result = detail.handle_click(pos)
                        if action_result:
                            action, f = action_result
                            if action == "cancelar":
                                f.status = "Cancelado"
                                notifications.add(f"{f.code}: Cancelado", RED)
                            elif action == "retardado":
                                f.status = "Retardado"
                                notifications.add(f"{f.code}: Marcado como Retardado", ORANGE)
                            elif action == "delay5":
                                f.delay += 5
                                notifications.add(f"{f.code}: +5 min demora", ORANGE)
                            elif action == "delay15":
                                f.delay += 15
                                notifications.add(f"{f.code}: +15 min demora", ORANGE)
                            elif action == "cleardelay":
                                f.delay = 0
                                notifications.add(f"{f.code}: Demora eliminada", GREEN)
                            elif f.status != action:
                                old = f.status
                                f.status = action
                                f.progress = max(0, f.progress - 10)
                                notifications.add(f"{f.code}: {old} → {action}", CYAN)
                        continue
                    detail.hide()

                # new flight dialog click
                if new_flight_dialog.active:
                    result = new_flight_dialog.handle_event(event)
                    if result:
                        flights.append(result)
                        notifications.add(f"Nuevo vuelo: {result.code} → {result.destination}", GREEN)
                    continue

                # search bar click
                search_bar.handle_event(event)

                # check flight cards
                for p in panels:
                    f = p.handle_mouse(event)
                    if f:
                        detail.show(f)

            elif event.type == pygame.MOUSEMOTION:
                # hover for buttons
                for btn in [btn_new, btn_save, btn_load, btn_reset]:
                    btn.handle_event(event)
                detail.handle_motion(event.pos)
                for p in panels:
                    p.handle_mouse(event)

        if changed_codes and pygame.time.get_ticks() - change_notify_start > 800:
            changed_codes.clear()

    pygame.quit()


if __name__ == "__main__":
    main()
