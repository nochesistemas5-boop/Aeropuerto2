import pygame, random, time, math

pygame.init()
screen = pygame.display.set_mode((1800, 900))
pygame.display.set_caption("Aeropuerto IA Distributiva")

# Colores
colors = {
    "En espera": (255, 165, 0),
    "Embarcando": (0, 0, 255),
    "Despegó": (0, 200, 0),
    "Retardado": (200, 0, 0),
    "Pronto a llegar": (0, 150, 255),
    "Llegó": (0, 255, 100)
}
BLACK = (0,0,0)
GREEN = (0,255,0)
WHITE = (255,255,255)

# Listas de vuelos
salidas_nacionales = [
    {"vuelo":"AV101","destino":"Medellín","estado":"En espera","pasajeros":90,"demora":0,"hora_salida":"19:40"},
    {"vuelo":"AV202","destino":"Cali","estado":"Embarcando","pasajeros":110,"demora":0,"hora_salida":"20:10"},
]
llegadas_nacionales = [
    {"vuelo":"AV303","destino":"Cartagena","estado":"Retardado","pasajeros":75,"demora":15,"hora_llegada":"21:00"},
]
salidas_internacionales = [
    {"vuelo":"IB321","destino":"Madrid","estado":"Retardado","pasajeros":60,"demora":25,"hora_salida":"21:15"},
    {"vuelo":"AF654","destino":"París","estado":"En espera","pasajeros":70,"demora":0,"hora_salida":"22:00"},
]
llegadas_internacionales = [
    {"vuelo":"UA555","destino":"Nueva York","estado":"Despegó","pasajeros":95,"demora":0,"hora_llegada":"18:45"},
]

# Radar: aviones simulados
aviones = []
for i in range(12):
    angulo = random.uniform(0, 2*math.pi)
    distancia = random.randint(100, 350)
    aviones.append({
        "vuelo": f"AV{i+200}",
        "angulo": angulo,
        "distancia": distancia,
        "velocidad": random.uniform(-0.01,0.01)
    })
angulo_barrido = 0

# Evento para actualizar cada 3 segundos
UPDATE_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(UPDATE_EVENT, 3000)

# Fuentes
font = pygame.font.SysFont("Consolas", 22, bold=True)
clock_font = pygame.font.SysFont("Consolas", 32, bold=True)
title_font = pygame.font.SysFont("Consolas", 36, bold=True)

search_text = ""
selected_flight = None

def dibujar_panel(lista, titulo, x, y_inicio, clickable_areas):
    label = title_font.render(titulo, True, (200, 200, 255))
    screen.blit(label, (x, y_inicio-50))
    y = y_inicio
    for v in lista:
        if search_text.lower() in v["vuelo"].lower() or search_text.lower() in v["destino"].lower() or search_text == "":
            datos = [v.get("vuelo","-"), v.get("destino","-"), v.get("estado","-"),
                     str(v.get("pasajeros","-")), str(v.get("demora","-"))+" min" if v.get("estado")=="Retardado" else "-"]
            row_rect = pygame.Rect(x, y, 700, 40)
            clickable_areas.append((row_rect, v))
            pygame.draw.rect(screen, (30,30,60), row_rect)
            for i, d in enumerate(datos):
                label = font.render(d, True, colors.get(v["estado"],(255,255,255)) if i==2 else (255,255,255))
                screen.blit(label, (x + i*140, y+10))
            y += 40

def crear_vuelo():
    print("\n=== Crear nuevo vuelo ===")
    tipo = input("¿Nacional o Internacional? (N/I): ").strip().upper()
    panel = input("¿Salida o Llegada? (S/L): ").strip().upper()
    vuelo = input("Código de vuelo: ").strip()
    destino = input("Destino: ").strip()
    estado = random.choice(list(colors.keys()))
    pasajeros = random.randint(50,200)
    hora = time.strftime("%H:%M")
    nuevo = {"vuelo":vuelo,"destino":destino,"estado":estado,"pasajeros":pasajeros,"demora":0}
    if panel=="S": nuevo["hora_salida"]=hora
    else: nuevo["hora_llegada"]=hora

    if tipo=="N" and panel=="S": salidas_nacionales.append(nuevo)
    elif tipo=="N" and panel=="L": llegadas_nacionales.append(nuevo)
    elif tipo=="I" and panel=="S": salidas_internacionales.append(nuevo)
    elif tipo=="I" and panel=="L": llegadas_internacionales.append(nuevo)
    print("✅ Vuelo agregado correctamente!")

clock = pygame.time.Clock()
running = True
while running:
    screen.fill((10, 10, 30))
    clickable_areas = []

    # Título y reloj
    title_label = title_font.render("✈️ Tablero de Vuelos - Aeropuerto IA", True, (255, 255, 0))
    screen.blit(title_label, (500, 20))
    current_time = time.strftime("%H:%M:%S")
    clock_label = clock_font.render(f"🕒 Hora actual: {current_time}", True, (255, 255, 255))
    screen.blit(clock_label, (650, 70))

    # Cuadro búsqueda
    pygame.draw.rect(screen, (255, 255, 255), (600, 120, 400, 35), 2)
    search_label = font.render("Buscar vuelo/destino: " + search_text, True, (255, 255, 255))
    screen.blit(search_label, (610, 125))

    # Paneles
    dibujar_panel(salidas_nacionales, "Salidas Nacionales", 80, 220, clickable_areas)
    dibujar_panel(llegadas_nacionales, "Llegadas Nacionales", 900, 220, clickable_areas)
    dibujar_panel(salidas_internacionales, "Salidas Internacionales", 80, 500, clickable_areas)
    dibujar_panel(llegadas_internacionales, "Llegadas Internacionales", 900, 500, clickable_areas)

    # Radar en esquina derecha
    radar_center = (1450, 450)
    pygame.draw.circle(screen, GREEN, radar_center, 350, 2)
    pygame.draw.circle(screen, GREEN, radar_center, 250, 1)
    pygame.draw.circle(screen, GREEN, radar_center, 150, 1)
    # Línea de barrido
    x = radar_center[0] + 350*math.cos(angulo_barrido)
    y = radar_center[1] + 350*math.sin(angulo_barrido)
    pygame.draw.line(screen, GREEN, radar_center, (x,y), 2)
    angulo_barrido += 0.02
    if angulo_barrido > 2*math.pi:
        angulo_barrido = 0
    # Aviones en radar
    for avion in aviones:
        avion["angulo"] += avion["velocidad"]
        ax = radar_center[0] + avion["distancia"]*math.cos(avion["angulo"])
        ay = radar_center[1] + avion["distancia"]*math.sin(avion["angulo"])
        pygame.draw.circle(screen, WHITE, (int(ax),int(ay)), 4)
        label = font.render(avion["vuelo"], True, WHITE)
        screen.blit(label, (int(ax)+5,int(ay)+5))

        pygame.display.flip()
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == UPDATE_EVENT:
            for lista in [salidas_nacionales, llegadas_nacionales, salidas_internacionales, llegadas_internacionales]:
                for v in lista:
                    v["estado"] = random.choice(list(colors.keys()))
                    v["pasajeros"] += random.randint(0, 5)
                    v["demora"] = random.randint(10, 60) if v["estado"] == "Retardado" else 0
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                search_text = search_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                selected_flight = None
            elif event.key == pygame.K_n:   # tecla N crea vuelo
                crear_vuelo()
            else:
                if event.unicode.isprintable():
                    search_text += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for rect, vuelo in clickable_areas:
                if rect.collidepoint(pos):
                    selected_flight = vuelo

pygame.quit()
