from dataclasses import dataclass, field
from typing import List, Optional
import json
import random

CAPTAINS = ["Cap. Gómez", "Cap. Ramírez", "Cap. Torres", "Cap. Mendoza",
            "Cap. Rojas", "Cap. Silva", "Cap. Vargas", "Cap. Castro"]
COPILOTS = ["Co. Pérez", "Co. López", "Co. Díaz", "Co. Martínez",
            "Co. García", "Co. Sánchez", "Co. Fernández"]
CREW = ["María Ruiz", "Pedro Gil", "Laura Paz", "Carlos Rey",
        "Ana Sol", "Luis Feo", "Sonia Calle", "Jorge Cruz",
        "Elena Mar", "Diego Roa"]

CREW_ASSIGNMENTS = {}


def assign_crew(code: str) -> tuple:
    if code in CREW_ASSIGNMENTS:
        return CREW_ASSIGNMENTS[code]
    cap = random.choice(CAPTAINS)
    cop = random.choice([c for c in COPILOTS if c != cap.replace("Cap.", "Co.")])
    cab1 = random.choice(CREW)
    cab2 = random.choice([c for c in CREW if c != cab1])
    result = (cap, cop, cab1, cab2)
    CREW_ASSIGNMENTS[code] = result
    return result


@dataclass
class Flight:
    code: str
    destination: str
    flight_type: str
    direction: str
    status: str
    passengers: int
    scheduled_time: str
    delay: int = 0
    gate: str = ""
    progress: int = 0
    prev_status: str = ""
    captain: str = ""
    copilot: str = ""
    cabin_crew: str = ""

    def __post_init__(self):
        if not self.prev_status:
            self.prev_status = self.status

    @property
    def has_changed(self) -> bool:
        return self.status != self.prev_status

    def ack_change(self):
        self.prev_status = self.status

    def display_time(self) -> str:
        return self.scheduled_time

    def info_lines(self) -> List[str]:
        lines = [
            f"Vuelo: {self.code}",
            f"Destino: {self.destination}",
            f"Tipo: {self.flight_type} - {self.direction}",
            f"Estado: {self.status}",
            f"Pasajeros: {self.passengers}",
            f"Hora: {self.scheduled_time}",
            f"Puerta: {self.gate if self.gate else 'Sin asignar'}",
            f"Demora: {self.delay} min" if self.delay > 0 else "Demora: 0 min",
            f"Progreso: {self.progress}%",
        ]
        if self.captain:
            lines.append(f"Piloto: {self.captain}")
        if self.copilot:
            lines.append(f"Copiloto: {self.copilot}")
        if self.cabin_crew:
            lines.append(f"Tripulación: {self.cabin_crew}")
        return lines


def flight_to_dict(f: Flight) -> dict:
    return {
        "code": f.code, "destination": f.destination,
        "flight_type": f.flight_type, "direction": f.direction,
        "status": f.status, "passengers": f.passengers,
        "scheduled_time": f.scheduled_time, "delay": f.delay,
        "gate": f.gate, "progress": f.progress,
        "captain": f.captain, "copilot": f.copilot, "cabin_crew": f.cabin_crew,
    }


def flight_from_dict(d: dict) -> Flight:
    return Flight(
        code=d["code"], destination=d["destination"],
        flight_type=d["flight_type"], direction=d["direction"],
        status=d["status"], passengers=d["passengers"],
        scheduled_time=d["scheduled_time"], delay=d.get("delay", 0),
        gate=d.get("gate", ""), progress=d.get("progress", 0),
        captain=d.get("captain", ""),
        copilot=d.get("copilot", ""),
        cabin_crew=d.get("cabin_crew", ""),
    )


def save_flights(flights: List[Flight], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([flight_to_dict(fi) for fi in flights], f, ensure_ascii=False, indent=2)


def load_flights(path: str) -> List[Flight]:
    with open(path, "r", encoding="utf-8") as f:
        return [flight_from_dict(d) for d in json.load(f)]
