import random
import time
from colorama import Fore, Style, init

# Inicializar colorama para colores en consola
init(autoreset=True)

class AeropuertoIA:
    def __init__(self):
        self.vuelos = [
            {"vuelo": "AV123", "destino": "Bogotá", "estado": "En espera", "pasajeros": 0, "demora": 0},
            {"vuelo": "LA456", "destino": "Miami", "estado": "En espera", "pasajeros": 0, "demora": 0},
            {"vuelo": "IB789", "destino": "Madrid", "estado": "En espera", "pasajeros": 0, "demora": 0},
        ]
        self.pasajeros = []

    def registrar_pasajero(self, nombre, vuelo):
        pasajero = {"nombre": nombre, "vuelo": vuelo, "estado": "Check-in"}
        self.pasajeros.append(pasajero)
        for v in self.vuelos:
            if v["vuelo"] == vuelo:
                v["pasajeros"] += 1
        print(Fore.CYAN + f"🛂 Pasajero {nombre} registrado en vuelo {vuelo}")

    def control_seguridad(self):
        for pasajero in self.pasajeros:
            if pasajero["estado"] == "Check-in":
                pasajero["estado"] = "Seguridad"
                print(Fore.YELLOW + f"🔍 Pasajero {pasajero['nombre']} pasó por seguridad")

    def embarque(self):
        for pasajero in self.pasajeros:
            if pasajero["estado"] == "Seguridad":
                pasajero["estado"] = "Embarcado"
                print(Fore.GREEN + f"✈️ Pasajero {pasajero['nombre']} embarcó en vuelo {pasajero['vuelo']}")

    def actualizar_vuelos(self):
        for vuelo in self.vuelos:
            vuelo["estado"] = random.choice(["En espera", "Embarcando", "Despegó", "Retardado"])
            if vuelo["estado"] == "Retardado":
                vuelo["demora"] = random.randint(10, 60)  # minutos de demora
            else:
                vuelo["demora"] = 0

    def mostrar_estado(self):
        print("\n📋 Estado de vuelos:")
        for v in self.vuelos:
            if v["estado"] == "Retardado":
                print(Fore.RED + f"{v['vuelo']} → {v['estado']} ({v['demora']} min de demora) | Pasajeros: {v['pasajeros']}")
            elif v["estado"] == "Despegó":
                print(Fore.GREEN + f"{v['vuelo']} → {v['estado']} | Pasajeros: {v['pasajeros']}")
            elif v["estado"] == "Embarcando":
                print(Fore.BLUE + f"{v['vuelo']} → {v['estado']} | Pasajeros: {v['pasajeros']}")
            else:
                print(Fore.YELLOW + f"{v['vuelo']} → {v['estado']} | Pasajeros: {v['pasajeros']}")

        print("\n📋 Estado de pasajeros:")
        for p in self.pasajeros:
            if p["estado"] == "Check-in":
                print(Fore.CYAN + f"{p['nombre']} → {p['estado']} en vuelo {p['vuelo']}")
            elif p["estado"] == "Seguridad":
                print(Fore.YELLOW + f"{p['nombre']} → {p['estado']} en vuelo {p['vuelo']}")
            elif p["estado"] == "Embarcado":
                print(Fore.GREEN + f"{p['nombre']} → {p['estado']} en vuelo {p['vuelo']}")

    def simulacion(self):
        print("=== Simulación de Aeropuerto con IA Distributiva ===")
        self.registrar_pasajero("Carlos", "AV123")
        self.registrar_pasajero("María", "LA456")
        self.registrar_pasajero("Lucía", "IB789")
        self.registrar_pasajero("Pedro", "AV123")

        time.sleep(1)
        self.control_seguridad()

        time.sleep(1)
        self.embarque()

        time.sleep(1)
        self.actualizar_vuelos()
        self.mostrar_estado()

# Ejecutar simulación
if __name__ == "__main__":
    aeropuerto = AeropuertoIA()
    aeropuerto.simulacion()
