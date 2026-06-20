import pygame
import random
import time
import os
import sys

from config import *
from flight import Flight, save_flights, load_flights
from ai_engine import AIEngine
from ui import (
    draw_gradient, TopBar, SearchBar, FlightPanel, AirportMap, Runway,
    ContextMenu, CommandLog,
    DetailPanel, NewFlightDialog, HelpOverlay, NotificationLog,
    Button, get_font, Tooltip, StatsOverlay, FIDSDisplay
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
    F = Flight
    return [
        # ========== BOG Departures ==========
        F("AV101", "Medellín", "Nacional", "Salida", "Programado", 90, "06:30", destination_airport="MDE"),
        F("AV202", "Cali", "Nacional", "Salida", "Abordando", 110, "07:00", destination_airport="CLO"),
        F("AV404", "Bogotá", "Nacional", "Salida", "Programado", 130, "07:30", destination_airport="BOG"),
        F("AV606", "Santa Marta", "Nacional", "Salida", "Programado", 85, "08:45", destination_airport="", gate="A2"),
        F("AV110", "Cúcuta", "Nacional", "Salida", "Programado", 70, "09:30"),
        F("AV211", "Manizales", "Nacional", "Salida", "Programado", 80, "10:15"),
        F("AV413", "Armenia", "Nacional", "Salida", "Programado", 100, "10:45"),
        F("AV615", "Valledupar", "Nacional", "Salida", "Programado", 75, "11:00"),
        F("AV120", "Leticia", "Nacional", "Salida", "Programado", 50, "11:30"),
        F("AV122", "Popayán", "Nacional", "Salida", "Programado", 65, "12:00"),
        F("AV124", "Ibagué", "Nacional", "Salida", "Programado", 80, "12:30"),
        F("IB321", "Madrid", "Internacional", "Salida", "Programado", 260, "08:00", destination_airport="MAD", gate="C1"),
        F("AF654", "París", "Internacional", "Salida", "Programado", 290, "09:15", destination_airport="CDG"),
        F("BA111", "Londres", "Internacional", "Salida", "Programado", 310, "10:00", destination_airport="LHR"),
        F("DL444", "Atlanta", "Internacional", "Salida", "Programado", 180, "12:00", destination_airport="ATL"),
        F("KL666", "Ámsterdam", "Internacional", "Salida", "Programado", 280, "13:15", destination_airport="AMS"),
        F("QR888", "Doha", "Internacional", "Salida", "Programado", 320, "14:00", destination_airport="DOH"),
        F("AZ111", "Roma", "Internacional", "Salida", "Programado", 250, "14:30", destination_airport="FCO"),
        F("LA501", "Santiago", "Internacional", "Salida", "Programado", 340, "15:00", destination_airport="SCL"),
        F("AR601", "Buenos Aires", "Internacional", "Salida", "Programado", 370, "16:00", destination_airport="EZE"),
        F("AM701", "Ciudad de México", "Internacional", "Salida", "Programado", 280, "17:00", destination_airport="MEX"),
        # ========== BOG Arrivals ==========
        F("AV303", "Cartagena", "Nacional", "Llegada", "En vuelo", 75, "06:45", delay=10, origin_airport="CTG", destination_airport="BOG"),
        F("AV505", "San Andrés", "Nacional", "Llegada", "En vuelo", 120, "07:15", destination_airport="BOG"),
        F("AV707", "Pereira", "Nacional", "Llegada", "En vuelo", 65, "07:50", destination_airport="BOG"),
        F("AV909", "Barranquilla", "Nacional", "Llegada", "En vuelo", 105, "08:20", origin_airport="BAQ", destination_airport="BOG"),
        F("AV312", "Neiva", "Nacional", "Llegada", "En vuelo", 55, "09:40", destination_airport="BOG"),
        F("AV514", "Sincelejo", "Nacional", "Llegada", "En vuelo", 60, "10:00", destination_airport="BOG"),
        F("AV716", "Tunja", "Nacional", "Llegada", "En vuelo", 45, "10:30", destination_airport="BOG"),
        F("AV121", "Pasto", "Nacional", "Llegada", "En vuelo", 70, "11:00", destination_airport="BOG"),
        F("AV123", "Riohacha", "Nacional", "Llegada", "En vuelo", 55, "11:45", destination_airport="BOG"),
        F("AV125", "Villavicencio", "Nacional", "Llegada", "En vuelo", 90, "12:15", destination_airport="BOG"),
        F("UA555", "Nueva York", "Internacional", "Llegada", "En vuelo", 195, "07:20", destination_airport="BOG"),
        F("LH789", "Frankfurt", "Internacional", "Llegada", "En vuelo", 210, "08:30", delay=25, destination_airport="BOG"),
        F("CM222", "Panamá", "Internacional", "Llegada", "En vuelo", 140, "09:00", origin_airport="PTY", destination_airport="BOG"),
        F("AC555", "Toronto", "Internacional", "Llegada", "En vuelo", 200, "10:45", destination_airport="BOG"),
        F("TK777", "Estambul", "Internacional", "Llegada", "En vuelo", 240, "11:00", delay=15, destination_airport="BOG"),
        F("EK999", "Dubái", "Internacional", "Llegada", "En vuelo", 300, "12:30", destination_airport="BOG"),
        F("TP222", "Lisboa", "Internacional", "Llegada", "En vuelo", 190, "13:00", destination_airport="BOG"),
        F("UX801", "Madrid", "Internacional", "Llegada", "En vuelo", 280, "14:00", origin_airport="MAD", destination_airport="BOG"),
        F("CU901", "La Habana", "Internacional", "Llegada", "En vuelo", 160, "15:30", destination_airport="BOG"),
        # ========== MDE ==========
        F("AV117", "Bogotá", "Nacional", "Salida", "Programado", 100, "07:00", origin_airport="MDE", destination_airport="BOG"),
        F("AV118", "Medellín", "Nacional", "Llegada", "En vuelo", 95, "06:00", origin_airport="BOG", destination_airport="MDE"),
        F("AV119", "Cali", "Nacional", "Llegada", "En vuelo", 110, "06:30", origin_airport="CLO", destination_airport="MDE"),
        F("AA333", "Miami", "Internacional", "Salida", "Programado", 220, "11:30", origin_airport="MDE", destination_airport="MIA"),
        F("AV801", "Bogotá", "Nacional", "Salida", "Programado", 95, "13:00", origin_airport="MDE", destination_airport="BOG"),
        F("AV802", "Cartagena", "Nacional", "Llegada", "En vuelo", 85, "14:30", origin_airport="CTG", destination_airport="MDE"),
        # ========== CTG ==========
        F("AV301", "Bogotá", "Nacional", "Salida", "Programado", 120, "07:00", origin_airport="CTG", destination_airport="BOG"),
        F("AV302", "Medellín", "Nacional", "Salida", "Abordando", 100, "12:00", origin_airport="CTG", destination_airport="MDE"),
        F("AV304", "Bogotá", "Nacional", "Llegada", "En vuelo", 90, "18:00", origin_airport="BOG", destination_airport="CTG"),
        # ========== CLO ==========
        F("AV401", "Bogotá", "Nacional", "Salida", "Programado", 140, "08:00", origin_airport="CLO", destination_airport="BOG"),
        F("AV402", "Medellín", "Nacional", "Salida", "Programado", 110, "14:00", origin_airport="CLO", destination_airport="MDE"),
        F("AV403", "Bogotá", "Nacional", "Llegada", "En vuelo", 130, "20:00", origin_airport="BOG", destination_airport="CLO"),
        # ========== BAQ ==========
        F("AV501", "Bogotá", "Nacional", "Salida", "Programado", 80, "09:00", origin_airport="BAQ", destination_airport="BOG"),
        F("AV502", "Medellín", "Nacional", "Llegada", "En vuelo", 75, "16:00", origin_airport="MDE", destination_airport="BAQ"),
        # ========== International extra ==========
        F("IB322", "Bogotá", "Internacional", "Llegada", "En vuelo", 270, "22:00", origin_airport="MAD", destination_airport="BOG"),
        F("AF655", "Bogotá", "Internacional", "Salida", "Programado", 295, "23:00", origin_airport="BOG", destination_airport="CDG"),
        F("LA502", "Bogotá", "Internacional", "Llegada", "En vuelo", 350, "21:00", origin_airport="SCL", destination_airport="BOG"),
        F("AM702", "Bogotá", "Internacional", "Llegada", "En vuelo", 285, "19:30", origin_airport="MEX", destination_airport="BOG"),
    ]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    init_sound()
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    fullscreen = False
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Aeropuerto IA Distributiva  |  F11: Pantalla completa")
    clock = pygame.time.Clock()

    flights = make_flights()
    ai = AIEngine()
    airport_map = AirportMap(1145, 240, 260, 260)
    runway = Runway(1080, 660, 400, 115)
    detail = DetailPanel()
    new_flight_dialog = NewFlightDialog()
    help_overlay = HelpOverlay()
    stats_overlay = StatsOverlay()
    fids = FIDSDisplay()
    notifications = NotificationLog()
    command_log = CommandLog()
    context_menu = ContextMenu()
    tooltip = Tooltip()

    top_bar = TopBar()
    search_bar = SearchBar()
    changed_codes = set()
    mouse_pos = (0, 0)

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

    # time controls
    speed = 1
    time_acc = 0.0
    current_airport = "BOG"
    airport_list = list(AIRPORTS.keys())

    change_notify_start = 0
    running = True
    while running:
        dt = clock.tick(FPS)

        # -- update --
        airport_map.update()
        runway.update()

        if speed > 0:
            time_acc += dt * speed
            while time_acc >= UPDATE_MS:
                time_acc -= UPDATE_MS
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

        # -- draw --
        draw_gradient(screen)

        # per-airport stats
        ap_flights = [f for f in flights if f.origin_airport == current_airport or f.destination_airport == current_airport]
        ap_total = len(ap_flights)
        ap_delayed = sum(1 for f in ap_flights if f.delay > 15 or f.status == "Retardado")
        ap_cancelled = sum(1 for f in ap_flights if f.status == "Cancelado")
        ap_delays = [f.delay for f in ap_flights if f.delay > 0]
        ap_stats = dict(ai.stats)
        ap_stats.update(total=ap_total, on_time=ap_total - ap_delayed - ap_cancelled,
                        delayed=ap_delayed, cancelled=ap_cancelled,
                        avg_delay=round(sum(ap_delays)/len(ap_delays), 1) if ap_delays else 0.0)

        # top bar
        top_bar.draw(screen, ap_stats, speed, airport_list, current_airport)

        # search bar + filter buttons
        search_bar.draw(screen)

        # update panels with current data (filtered by airport)
        for p in panels:
            if "Salidas" in p.title:
                flist = [f for f in flights if f.direction == "Salida" and f.origin_airport == current_airport and
                         ((f.flight_type == "Nacional" and "Nacionales" in p.title) or
                          (f.flight_type == "Internacional" and "Internacionales" in p.title))]
            else:
                flist = [f for f in flights if f.direction == "Llegada" and f.destination_airport == current_airport and
                         ((f.flight_type == "Nacional" and "Nacionales" in p.title) or
                          (f.flight_type == "Internacional" and "Internacionales" in p.title))]
            p.set_flights(flist, search_bar.text, search_bar.active_filter if hasattr(search_bar, 'active_filter') else "all")
            p.draw(screen, changed_codes)

        # airport map
        airport_map.draw(screen, flights)

        # runway
        runway.draw(screen)

        # bottom bar
        pygame.draw.rect(screen, (10, 10, 40), (0, 785, SCREEN_WIDTH, 35))
        pygame.draw.line(screen, BORDER, (0, 785), (SCREEN_WIDTH, 785), 1)
        btn_new.draw(screen)
        btn_save.draw(screen)
        btn_load.draw(screen)
        btn_reset.draw(screen)

        help_lbl = get_font(11).render("F1: Ayuda  |  F2: Stats  |  F3: FIDS  |  F11: Fullscreen  |  Click: Detalle  |  Click der: Torre  |  Rueda: Scroll", True, TEXT_MUTED)
        screen.blit(help_lbl, (530, 792))

        # tooltip
        tooltip.draw(screen, mouse_pos)

        # notification log
        notifications.draw(screen, 735, 130)

        # command log
        command_log.draw(screen, 735, 560)

        # dialogs on top
        detail.draw(screen, ai.get_delay_reason(detail.flight) if detail.flight else "")
        new_flight_dialog.draw(screen)
        context_menu.draw(screen)
        help_overlay.draw(screen)
        stats_overlay.draw(screen, flights, ai.stats)
        fids.draw(screen, flights, current_airport)

        pygame.display.flip()

        # -- events --
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if new_flight_dialog.active:
                    new_flight_dialog.handle_event(event)
                elif event.key == pygame.K_ESCAPE:
                    if context_menu.active:
                        context_menu.hide()
                    elif help_overlay.active:
                        help_overlay.close()
                    elif stats_overlay.active:
                        stats_overlay.close()
                    elif fids.active:
                        fids.close()
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
                elif event.key == pygame.K_F2:
                    stats_overlay.toggle()
                elif event.key == pygame.K_F3:
                    fids.toggle()
                elif event.key == pygame.K_TAB and fids.active:
                    fids.show_departures = not fids.show_departures
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                else:
                    search_bar.handle_event(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                # speed controls
                if top_bar.pause_rect.collidepoint(pos):
                    speed = 0 if speed > 0 else 1
                    continue
                speed_clicked = False
                for br, s in top_bar.speed_btn_rects:
                    if br.collidepoint(pos):
                        speed = s if speed != s else speed
                        speed_clicked = True
                        break
                if speed_clicked:
                    continue

                search_bar.handle_event(event)

                # bottom bar buttons
                if btn_new.rect.collidepoint(pos):
                    new_flight_dialog.open()
                    continue
                elif btn_save.rect.collidepoint(pos):
                    save_flights(flights, "vuelos.json")
                    continue
                elif btn_load.rect.collidepoint(pos):
                    try:
                        loaded = load_flights("vuelos.json")
                        if loaded:
                            flights = loaded
                    except Exception:
                        pass
                    continue
                elif btn_reset.rect.collidepoint(pos):
                    flights = make_flights()
                    ai = AIEngine()
                    continue

                # filter buttons
                filters_region = [("all", pygame.Rect(380, 90, 72, 34)),
                                  ("dep", pygame.Rect(458, 90, 72, 34)),
                                  ("arr", pygame.Rect(536, 90, 72, 34))]
                clicked_filter = False
                for key, rect in filters_region:
                    if rect.collidepoint(pos):
                        search_bar.active_filter = key
                        clicked_filter = True
                        break
                if clicked_filter:
                    continue

                # airport selector
                if top_bar.airport_rect.collidepoint(pos):
                    idx = airport_list.index(current_airport) if current_airport in airport_list else 0
                    current_airport = airport_list[(idx + 1) % len(airport_list)]
                    continue

                # panel header sort click
                for p in panels:
                    if p.header_rect().collidepoint(pos):
                        sort_keys = ["code", "time", "status"]
                        current_idx = sort_keys.index(p.sort_key) if p.sort_key in sort_keys else -1
                        next_key = sort_keys[(current_idx + 1) % len(sort_keys)]
                        p.toggle_sort(next_key)
                        break

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

                # context menu click (right click handled first)
                if context_menu.active:
                    result = context_menu.handle_click(pos)
                    if result:
                        action, f = result
                        if action == "detail":
                            detail.show(f)
                        elif action == "abordar" and f.status == "Programado":
                            f.status = "Abordando"
                            command_log.add(f"{f.code}: Abordaje iniciado")
                        elif action == "despegar":
                            f.status = "Despegó"
                            f.progress = 55
                            command_log.add(f"{f.code}: Despegue autorizado")
                        elif action == "aterrizar":
                            f.status = "Aterrizó"
                            f.progress = 82
                            command_log.add(f"{f.code}: Aterrizaje autorizado")
                        elif action == "repuerta":
                            import random
                            from config import GATES_DEP, GATES_ARR
                            pool = GATES_DEP if f.direction == "Salida" else GATES_ARR
                            f.gate = random.choice(pool)
                            command_log.add(f"{f.code}: Puerta asignada {f.gate}")
                        elif action == "delay10":
                            f.delay += 10
                            command_log.add(f"{f.code}: +10 min demora")
                        elif action == "cleardelay":
                            f.delay = 0
                            command_log.add(f"{f.code}: Demora eliminada")
                        elif action == "reanudar":
                            from config import STATUS_TRANSITIONS_DEP, STATUS_TRANSITIONS_ARR
                            if f.direction == "Salida":
                                for s in STATUS_TRANSITIONS_DEP:
                                    if f.progress < 60:
                                        f.status = s
                                        break
                            else:
                                for s in STATUS_TRANSITIONS_ARR:
                                    if f.progress < 92:
                                        f.status = s
                                        break
                            command_log.add(f"{f.code}: Vuelo reanudado")
                        elif action == "cancelar":
                            f.status = "Cancelado"
                            command_log.add(f"{f.code}: Vuelo CANCELADO")
                        notifications.add(f"Torre: {command_log.items[-1] if command_log.items else action}", CYAN)

                # new flight dialog click
                if new_flight_dialog.active:
                    result = new_flight_dialog.handle_event(event)
                    if result:
                        flights.append(result)
                        notifications.add(f"Nuevo vuelo: {result.code} → {result.destination}", GREEN)
                    continue

                # right click - context menu
                if event.button == 3:
                    for p in panels:
                        f = p.handle_mouse(event)
                        if f:
                            context_menu.show(f, event.pos[0], event.pos[1])
                            break

                # check flight cards (left click)
                if event.button == 1:
                    for p in panels:
                        f = p.handle_mouse(event)
                        if f:
                            if not context_menu.active:
                                detail.show(f)

            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
                context_menu.handle_motion(event.pos)
                # hover for buttons
                for btn in [btn_new, btn_save, btn_load, btn_reset]:
                    btn.handle_event(event)
                detail.handle_motion(event.pos)
                for p in panels:
                    p.handle_mouse(event)

                # tooltips
                tooltip.hide()
                if top_bar.pause_rect.collidepoint(event.pos):
                    tooltip.show("Pausar / Reanudar simulación", top_bar.pause_rect)
                else:
                    for br, s in top_bar.speed_btn_rects:
                        if br.collidepoint(event.pos):
                            tooltip.show(f"Velocidad {s}×", br)
                            break
                if top_bar.airport_rect.collidepoint(event.pos):
                    tooltip.show("Cambiar aeropuerto", top_bar.airport_rect)
                elif btn_new.rect.collidepoint(event.pos):
                    tooltip.show("Añadir un nuevo vuelo", btn_new.rect)
                elif btn_save.rect.collidepoint(event.pos):
                    tooltip.show("Guardar vuelos a JSON", btn_save.rect)
                elif btn_load.rect.collidepoint(event.pos):
                    tooltip.show("Cargar vuelos desde JSON", btn_load.rect)
                elif btn_reset.rect.collidepoint(event.pos):
                    tooltip.show("Restaurar vuelos iniciales", btn_reset.rect)

        if changed_codes and pygame.time.get_ticks() - change_notify_start > 800:
            changed_codes.clear()

    pygame.quit()


if __name__ == "__main__":
    main()
