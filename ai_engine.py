import random
import math
from typing import List, Dict, Optional, Tuple
from flight import Flight
from config import *

class AIEngine:
    def __init__(self):
        self.weather = "Despejado"
        self.weather_timer = 0
        self.sim_hour = 6
        self.sim_min = 0
        self.tick_count = 0
        self.gates_dep: Dict[str, Optional[str]] = {g: None for g in GATES_DEP}
        self.gates_arr: Dict[str, Optional[str]] = {g: None for g in GATES_ARR}
        self.stats = {
            "total": 0, "on_time": 0, "delayed": 0,
            "cancelled": 0, "avg_delay": 0.0,
        }
        self.flight_history: List[dict] = []

    def update(self, flights: List[Flight]):
        self.tick_count += 1
        self._update_time()
        self._update_weather()
        self._update_gates(flights)
        self._update_stats(flights)

        for f in flights:
            self._process_flight(f, flights)

    def _update_time(self):
        self.sim_min += 3
        if self.sim_min >= 60:
            self.sim_min = 0
            self.sim_hour = (self.sim_hour + 1) % 24

    def _update_weather(self):
        self.weather_timer += 1
        if self.weather_timer >= 15:
            self.weather_timer = 0
            idx = WEATHERS.index(self.weather)
            r = random.random()
            if r < 0.5:
                pass
            elif r < 0.8:
                idx = max(0, idx - 1)
            elif r < 0.95:
                idx = min(len(WEATHERS) - 1, idx + 1)
            else:
                idx = random.randint(0, len(WEATHERS) - 1)
            self.weather = WEATHERS[idx]

    def _update_gates(self, flights: List[Flight]):
        for g in self.gates_dep:
            self.gates_dep[g] = None
        for g in self.gates_arr:
            self.gates_arr[g] = None
        for f in flights:
            if f.gate:
                if f.direction == "Salida" and f.status not in ["Despegó", "En vuelo"]:
                    self.gates_dep[f.gate] = f.code
                elif f.direction == "Llegada" and f.status not in ["En puerta"]:
                    self.gates_arr[f.gate] = f.code

    def _update_stats(self, flights: List[Flight]):
        total = len(flights)
        delayed = sum(1 for f in flights if f.delay > 15 or f.status == "Retardado")
        cancelled = sum(1 for f in flights if f.status == "Cancelado")
        delays = [f.delay for f in flights if f.delay > 0]
        avg_delay = sum(delays) / len(delays) if delays else 0.0
        self.stats = {
            "total": total,
            "on_time": total - delayed - cancelled,
            "delayed": delayed,
            "cancelled": cancelled,
            "avg_delay": round(avg_delay, 1),
            "weather": self.weather,
            "time": f"{self.sim_hour:02d}:{self.sim_min:02d}",
        }

    def _get_congestion(self, flights: List[Flight]) -> float:
        active = sum(1 for f in flights if f.status not in ["En vuelo", "Despegó", "En puerta", "Cancelado"])
        max_active = max(1, len(flights) * 3 // 4)
        return min(1.0, active / max_active)

    def _assign_gate(self, f: Flight) -> str:
        if f.direction == "Salida":
            pool = GATES_DEP
            used = self.gates_dep
        else:
            pool = GATES_ARR
            used = self.gates_arr

        if f.flight_type == "Internacional" and f.direction == "Salida":
            preferred = [g for g in pool if g.startswith("C")]
            for g in preferred:
                if used[g] is None:
                    used[g] = f.code
                    return g

        available = [g for g in pool if used[g] is None]
        if available:
            g = available[0]
            used[g] = f.code
            return g
        return ""

    def _predict_delay(self, f: Flight, flights: List[Flight]) -> int:
        base = WEATHER_DELAY[self.weather]
        congestion = self._get_congestion(flights)
        hour_factor = 1.0
        if 6 <= self.sim_hour <= 9 or 17 <= self.sim_hour <= 20:
            hour_factor = 1.5
        elif 22 <= self.sim_hour or self.sim_hour <= 4:
            hour_factor = 0.5
        delay = int(base * hour_factor + congestion * 8)
        return max(0, delay)

    def _process_flight(self, f: Flight, flights: List[Flight]):
        progress_speed = 1.0
        weather_factor = WEATHER_DELAY[self.weather]
        if weather_factor > 0:
            progress_speed -= weather_factor * 0.03
        congestion = self._get_congestion(flights)
        if congestion > 0.5:
            progress_speed -= congestion * 0.15

        progress_speed = max(0.3, progress_speed)
        f.progress = min(MAX_PROGRESS, f.progress + int(PROGRESS_PER_TICK * progress_speed))

        if f.status == "Cancelado":
            return

        predicted_delay = self._predict_delay(f, flights)
        delay_prob = WEATHER_DELAY[self.weather] * 0.03 + congestion * 0.2

        if f.delay < predicted_delay and random.random() < delay_prob:
            f.delay += random.randint(1, max(1, predicted_delay))
            if f.delay > 15 and f.status != "Retardado":
                f.status = "Retardado"

        if f.delay > 60 and random.random() < 0.1 and self.weather == "Tormenta":
            f.status = "Cancelado"
            return

        if f.status == "Retardado" and f.delay == 0:
            self._restore_base_status(f)

        if f.direction == "Salida":
            self._transition_departure(f)
        else:
            self._transition_arrival(f)

        if not f.gate:
            f.gate = self._assign_gate(f)

    def _restore_base_status(self, f: Flight):
        if f.direction == "Salida":
            for s in STATUS_TRANSITIONS_DEP:
                threshold = PROGRESS_THRESHOLDS_DEP.get(s, MAX_PROGRESS)
                if f.progress < threshold:
                    f.status = s
                    return
            f.status = "En vuelo"
        else:
            for s in STATUS_TRANSITIONS_ARR:
                threshold = PROGRESS_THRESHOLDS_ARR.get(s, MAX_PROGRESS)
                if f.progress < threshold:
                    f.status = s
                    return
            f.status = "En puerta"

    def _transition_departure(self, f: Flight):
        if f.status == "Programado" and f.progress >= PROGRESS_THRESHOLDS_DEP["Programado"]:
            f.status = "Abordando"
        elif f.status == "Abordando" and f.progress >= PROGRESS_THRESHOLDS_DEP["Abordando"]:
            f.status = "Despegó"
            self.gates_dep[f.gate] = None if f.gate in self.gates_dep else None
        elif f.status == "Despegó" and f.progress >= PROGRESS_THRESHOLDS_DEP["Despegó"]:
            f.status = "En vuelo"

    def _transition_arrival(self, f: Flight):
        if f.status == "En vuelo" and f.progress >= PROGRESS_THRESHOLDS_ARR["En vuelo"]:
            f.status = "Aterrizó"
        elif f.status == "Aterrizó" and f.progress >= PROGRESS_THRESHOLDS_ARR["Aterrizó"]:
            f.status = "En puerta"
            self.gates_arr[f.gate] = None if f.gate in self.gates_arr else None

    def get_delay_reason(self, f: Flight) -> str:
        reasons = []
        w = WEATHER_DELAY[self.weather]
        if w > 0:
            reasons.append(f"Clima: {self.weather}")
        c = self._get_congestion_fake_name()
        if c:
            reasons.append(f"Congestión: {c}")
        if 6 <= self.sim_hour <= 9:
            reasons.append("Hora pico matutina")
        elif 17 <= self.sim_hour <= 20:
            reasons.append("Hora pico vespertina")
        return " | ".join(reasons) if reasons else "Sin demora significativa"

    def _get_congestion_fake_name(self) -> str:
        return ""
