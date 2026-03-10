"""
Smart City / IoT industry generators — 6 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from faker import Faker

from core.generators.base import BaseGenerator, UseCase
from core.correlation import SMART_CITY as _SC

_fake = Faker()

_DISTRICTS = _SC["districts"]
_CITIES    = _SC["cities"]


# ── 1 · Vehicle / Traffic Count ───────────────────────────────────────────────

class TrafficCountGenerator(BaseGenerator):
    VEHICLE_TYPES = ["Car", "Truck", "Motorcycle", "Bus", "Cyclist", "Pedestrian", "Van"]
    DIRECTIONS    = ["North", "South", "East", "West"]

    def generate(self) -> dict:
        return {
            "event_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "sensor_id":    f"TRF-{random.randint(1, 2000):04d}",
            "intersection": _fake.street_name() + " & " + _fake.street_name(),
            "city":         random.choice(_CITIES),
            "district":     random.choice(_DISTRICTS),
            "direction":    random.choice(self.DIRECTIONS),
            "vehicle_type": random.choice(self.VEHICLE_TYPES),
            "count":        random.randint(0, 50),
            "avg_speed_kmh": round(random.uniform(0, 80), 1),
            "congestion_index": round(random.uniform(0, 1), 3),
        }


# ── 2 · Air Quality ───────────────────────────────────────────────────────────

class AirQualityGenerator(BaseGenerator):
    CATEGORIES = ["Good", "Moderate", "Unhealthy for Sensitive Groups", "Unhealthy",
                  "Very Unhealthy", "Hazardous"]

    def generate(self) -> dict:
        aqi = random.randint(0, 500)
        cat_idx = min(5, aqi // 50)
        return {
            "reading_id":   str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "station_id":   f"AQI-{random.randint(1, 500):04d}",
            "city":         random.choice(_CITIES),
            "district":     random.choice(_DISTRICTS),
            "aqi":          aqi,
            "category":     self.CATEGORIES[cat_idx],
            "pm25_ugm3":    round(random.uniform(0.0, 500.0), 1),
            "pm10_ugm3":    round(random.uniform(0.0, 600.0), 1),
            "no2_ppb":      round(random.uniform(0.0, 200.0), 1),
            "co_ppm":       round(random.uniform(0.0, 50.0), 2),
            "o3_ppb":       round(random.uniform(0.0, 180.0), 1),
            "temperature_c": round(random.uniform(-10.0, 45.0), 1),
            "humidity_pct": round(random.uniform(10.0, 100.0), 1),
        }


# ── 3 · Waste Level Sensors ───────────────────────────────────────────────────

class WasteLevelGenerator(BaseGenerator):
    BIN_TYPES = ["General", "Recycling", "Organic", "Hazardous", "Glass", "Paper"]
    STATUSES  = ["OK", "FULL", "OVERFLOW", "FIRE_DETECTED", "MALFUNCTION"]

    def generate(self) -> dict:
        level = round(random.uniform(0, 100), 1)
        return {
            "reading_id":   str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "bin_id":       f"BIN-{random.randint(1, 5000):05d}",
            "city":         random.choice(_CITIES),
            "district":     random.choice(_DISTRICTS),
            "bin_type":     random.choice(self.BIN_TYPES),
            "fill_pct":     level,
            "weight_kg":    round(level * random.uniform(0.5, 2.0), 1),
            "temperature_c": round(random.uniform(5.0, 80.0), 1),
            "status":       "FULL" if level > 90 else random.choice(self.STATUSES[:2]),
            "last_emptied_h_ago": random.randint(0, 72),
        }


# ── 4 · Smart Parking ─────────────────────────────────────────────────────────

class SmartParkingGenerator(BaseGenerator):
    EVENTS = ["VEHICLE_ARRIVED", "VEHICLE_DEPARTED", "PAYMENT_MADE",
              "OVERSTAY_ALERT", "RESERVATION_START", "RESERVATION_END"]

    def generate(self) -> dict:
        return {
            "event_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "lot_id":       f"PKG-{random.randint(1, 500):04d}",
            "space_id":     f"SP-{random.randint(1, 200):04d}",
            "city":         random.choice(_CITIES),
            "event_type":   random.choice(self.EVENTS),
            "plate":        _fake.license_plate(),
            "duration_min": random.randint(5, 480),
            "fee_usd":      round(random.uniform(0.0, 50.0), 2),
            "ev_charging":  random.random() < 0.15,
            "handicap_bay": random.random() < 0.05,
            "occupancy_pct": round(random.uniform(0, 100), 1),
        }


# ── 5 · Transit / Public Transport ────────────────────────────────────────────

class TransitTrackingGenerator(BaseGenerator):
    MODES    = ["Metro", "Bus", "Tram", "Light Rail", "Ferry"]
    STATUSES = ["On Time", "Delayed", "Cancelled", "Diverted", "Boarding", "In Transit"]

    def generate(self) -> dict:
        return {
            "event_id":    str(uuid.uuid4()),
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "vehicle_id":  f"TRN-{random.randint(1, 1000):04d}",
            "route_id":    f"RT-{random.randint(1, 200):03d}",
            "city":        random.choice(_CITIES),
            "mode":        random.choice(self.MODES),
            "stop_id":     f"STOP-{random.randint(1, 1000):04d}",
            "stop_name":   _fake.street_name() + " Station",
            "status":      random.choice(self.STATUSES),
            "delay_min":   random.randint(0, 45),
            "passengers":  random.randint(0, 400),
            "capacity":    random.choice([80, 120, 200, 350, 400]),
            "latitude":    round(random.uniform(25.0, 60.0), 5),
            "longitude":   round(random.uniform(-130.0, 40.0), 5),
        }


# ── 6 · Environmental Sensors ─────────────────────────────────────────────────

class EnvironmentalSensorGenerator(BaseGenerator):
    SENSOR_TYPES = ["Weather Station", "Noise Meter", "UV Sensor",
                    "Earthquake Sensor", "River Level", "Flood Sensor"]

    def generate(self) -> dict:
        sensor = random.choice(self.SENSOR_TYPES)
        extra = {}
        if sensor == "Weather Station":
            extra = {"wind_speed_ms": round(random.uniform(0, 40), 1),
                     "rainfall_mm": round(random.uniform(0, 50), 1)}
        elif sensor == "Noise Meter":
            extra = {"noise_db": round(random.uniform(35, 120), 1)}
        elif sensor == "UV Sensor":
            extra = {"uv_index": round(random.uniform(0, 12), 1)}
        elif sensor == "River Level":
            extra = {"level_m": round(random.uniform(0, 15), 2),
                     "flood_warning": random.random() < 0.05}
        return {
            "reading_id":    str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "sensor_id":     f"ENV-{random.randint(1, 3000):05d}",
            "sensor_type":   sensor,
            "city":          random.choice(_CITIES),
            "district":      random.choice(_DISTRICTS),
            "latitude":      round(random.uniform(25.0, 60.0), 5),
            "longitude":     round(random.uniform(-130.0, 40.0), 5),
            "temperature_c": round(random.uniform(-20.0, 50.0), 1),
            "humidity_pct":  round(random.uniform(10.0, 100.0), 1),
            **extra,
        }


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="sc_traffic",
        title="Traffic & Vehicle Count",
        description="Intersection-level vehicle count by type and direction, with congestion index and average speed.",
        schema_preview='{ "sensor_id", "direction", "vehicle_type", "count", "congestion_index" }',
        generator_class=TrafficCountGenerator,
    ),
    UseCase(
        id="sc_air",
        title="Air Quality Monitoring",
        description="Station AQI readings with PM2.5, PM10, NOx, CO, O₃ and meteorological conditions.",
        schema_preview='{ "station_id", "aqi", "category", "pm25_ugm3", "pm10_ugm3", "no2_ppb" }',
        generator_class=AirQualityGenerator,
    ),
    UseCase(
        id="sc_waste",
        title="Waste Level Sensors",
        description="Smart bin monitoring — fill percentage, weight, temperature, and overflow/fire alerts.",
        schema_preview='{ "bin_id", "bin_type", "fill_pct", "weight_kg", "status" }',
        generator_class=WasteLevelGenerator,
    ),
    UseCase(
        id="sc_parking",
        title="Smart Parking Events",
        description="Real-time parking space events — arrivals, departures, payments, and EV charging sessions.",
        schema_preview='{ "lot_id", "space_id", "event_type", "duration_min", "fee_usd", "ev_charging" }',
        generator_class=SmartParkingGenerator,
    ),
    UseCase(
        id="sc_transit",
        title="Public Transit Tracking",
        description="Live bus, metro, and tram GPS positions with status, delay, and passenger counts.",
        schema_preview='{ "vehicle_id", "mode", "stop_name", "status", "delay_min", "passengers" }',
        generator_class=TransitTrackingGenerator,
    ),
    UseCase(
        id="sc_environment",
        title="Environmental Sensors",
        description="Multi-type environmental sensor events — weather, noise, UV, river levels, and flood warnings.",
        schema_preview='{ "sensor_type", "temperature_c", "humidity_pct", + type-specific fields }',
        generator_class=EnvironmentalSensorGenerator,
    ),
]
