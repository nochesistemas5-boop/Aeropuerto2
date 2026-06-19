from dataclasses import dataclass, field
from typing import List, Optional
import json

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
        return [
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


def flight_to_dict(f: Flight) -> dict:
    return {
        "code": f.code, "destination": f.destination,
        "flight_type": f.flight_type, "direction": f.direction,
        "status": f.status, "passengers": f.passengers,
        "scheduled_time": f.scheduled_time, "delay": f.delay,
        "gate": f.gate, "progress": f.progress,
    }


def flight_from_dict(d: dict) -> Flight:
    return Flight(
        code=d["code"], destination=d["destination"],
        flight_type=d["flight_type"], direction=d["direction"],
        status=d["status"], passengers=d["passengers"],
        scheduled_time=d["scheduled_time"], delay=d.get("delay", 0),
        gate=d.get("gate", ""), progress=d.get("progress", 0),
    )


def save_flights(flights: List[Flight], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([flight_to_dict(fi) for fi in flights], f, ensure_ascii=False, indent=2)


def load_flights(path: str) -> List[Flight]:
    with open(path, "r", encoding="utf-8") as f:
        return [flight_from_dict(d) for d in json.load(f)]
