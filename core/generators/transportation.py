"""
Transportation & Logistics industry generators — 6 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from faker import Faker

from core.generators.base import BaseGenerator, UseCase

_fake = Faker()

_STATUSES   = ["On-Time", "Delayed", "Early", "Cancelled", "Diverted"]
_VEHICLE_TYPES = ["Truck", "Van", "Motorcycle", "Container Ship", "Rail", "Drone", "Plane"]


# ── 1 · GPS Fleet Tracking ────────────────────────────────────────────────────

class GPSFleetGenerator(BaseGenerator):
    def generate(self) -> dict:
        lat = round(random.uniform(25.0, 60.0), 6)
        lon = round(random.uniform(-130.0, 40.0), 6)
        speed = round(random.uniform(0, 110), 1)
        return {
            "event_id":    str(uuid.uuid4()),
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "vehicle_id":  f"VEH-{random.randint(1, 5000):05d}",
            "driver_id":   f"DRV-{random.randint(1, 2000):05d}",
            "latitude":    lat,
            "longitude":   lon,
            "speed_kmh":   speed,
            "heading_deg": random.randint(0, 359),
            "fuel_pct":    round(random.uniform(5, 100), 1),
            "engine_on":   speed > 0 or random.random() > 0.2,
            "odometer_km": random.randint(0, 500000),
            "cargo_weight_kg": random.randint(0, 30000),
        }


# ── 2 · Package Status Updates ───────────────────────────────────────────────

class PackageStatusGenerator(BaseGenerator):
    STATUSES = ["LABEL_CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY",
                "DELIVERED", "FAILED_DELIVERY", "RETURNED", "EXCEPTION"]
    CARRIERS = ["FedEx", "UPS", "DHL", "USPS", "Amazon Logistics", "OnTrac"]

    def generate(self) -> dict:
        return {
            "event_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "tracking_id":  f"{random.randint(1000000000, 9999999999)}",
            "carrier":      random.choice(self.CARRIERS),
            "status":       random.choice(self.STATUSES),
            "facility_id":  f"HUB-{random.randint(1, 300):04d}",
            "city":         _fake.city(),
            "country":      _fake.country_code(),
            "weight_kg":    round(random.uniform(0.1, 70.0), 2),
            "service_type": random.choice(["Standard", "Express", "Overnight", "Economy"]),
            "signature_req": random.random() > 0.6,
        }


# ── 3 · Traffic Incidents ─────────────────────────────────────────────────────

class TrafficIncidentGenerator(BaseGenerator):
    TYPES = ["Accident", "Road Closure", "Construction", "Vehicle Breakdown",
             "Congestion", "Weather Hazard", "Road Work", "Special Event"]
    SEVERITY = ["Minor", "Moderate", "Severe", "Critical"]

    def generate(self) -> dict:
        lat = round(random.uniform(25.0, 60.0), 5)
        lon = round(random.uniform(-130.0, 40.0), 5)
        return {
            "incident_id":   str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "type":          random.choice(self.TYPES),
            "severity":      random.choice(self.SEVERITY),
            "latitude":      lat,
            "longitude":     lon,
            "road":          _fake.street_name(),
            "city":          _fake.city(),
            "delay_min":     random.randint(0, 180),
            "lanes_blocked": random.randint(0, 4),
            "vehicles_involved": random.randint(0, 10),
            "cleared":       random.random() < 0.2,
        }


# ── 4 · Cargo / Shipment Updates ─────────────────────────────────────────────

class CargoUpdateGenerator(BaseGenerator):
    EVENTS = ["BOOKING", "LOADED", "DEPARTED", "IN_TRANSIT", "CUSTOMS",
              "ARRIVED", "UNLOADED", "FINAL_DELIVERY", "EXCEPTION"]

    def generate(self) -> dict:
        return {
            "cargo_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "shipment_ref": f"SHP-{random.randint(100000, 999999)}",
            "event":        random.choice(self.EVENTS),
            "origin":       _fake.city() + ", " + _fake.country_code(),
            "destination":  _fake.city() + ", " + _fake.country_code(),
            "weight_tons":  round(random.uniform(0.5, 50000.0), 2),
            "volume_m3":    round(random.uniform(1.0, 5000.0), 2),
            "vessel":       _fake.company() + " Carrier",
            "eta":          _fake.future_date(end_date="+30d").isoformat(),
            "temperature_c": round(random.uniform(-25.0, 40.0), 1) if random.random() > 0.5 else None,
        }


# ── 5 · Driver Behaviour ─────────────────────────────────────────────────────

class DriverBehaviourGenerator(BaseGenerator):
    EVENTS = ["HARSH_BRAKE", "RAPID_ACCEL", "SHARP_TURN", "SPEEDING",
              "IDLE_EXCESS", "FATIGUE_ALERT", "LANE_DEPARTURE", "MOBILE_USE"]

    def generate(self) -> dict:
        return {
            "event_id":    str(uuid.uuid4()),
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "driver_id":   f"DRV-{random.randint(1, 2000):05d}",
            "vehicle_id":  f"VEH-{random.randint(1, 5000):05d}",
            "event_type":  random.choice(self.EVENTS),
            "severity_g":  round(random.uniform(0.2, 4.5), 2),
            "speed_kmh":   round(random.uniform(0, 140), 1),
            "latitude":    round(random.uniform(25.0, 60.0), 5),
            "longitude":   round(random.uniform(-130.0, 40.0), 5),
            "score_delta": round(random.uniform(-15.0, 0.0), 1),
            "driver_score": random.randint(40, 100),
        }


# ── 6 · Fuel Readings ─────────────────────────────────────────────────────────

class FuelReadingGenerator(BaseGenerator):
    def generate(self) -> dict:
        fuel_before = round(random.uniform(10, 100), 1)
        consumed    = round(random.uniform(0.1, 30.0), 2)
        return {
            "reading_id":   str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "vehicle_id":   f"VEH-{random.randint(1, 5000):05d}",
            "fuel_type":    random.choice(["Diesel", "Petrol", "LNG", "Electric", "Hybrid"]),
            "level_before": fuel_before,
            "level_after":  round(max(0.0, fuel_before - consumed), 1),
            "consumed_l":   consumed,
            "distance_km":  round(random.uniform(0.5, 500.0), 1),
            "efficiency_lp100km": round(random.uniform(4.0, 40.0), 1),
            "refuelled_l":  round(random.uniform(0, 200), 1) if random.random() < 0.1 else 0,
            "odometer_km":  random.randint(0, 500000),
        }


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="trans_gps",
        title="GPS Fleet Tracking",
        description="Real-time vehicle location pings with speed, heading, fuel, and cargo weight.",
        schema_preview='{ "vehicle_id", "latitude", "longitude", "speed_kmh", "fuel_pct" }',
        generator_class=GPSFleetGenerator,
    ),
    UseCase(
        id="trans_packages",
        title="Package Status Updates",
        description="Parcel lifecycle events from label creation to final delivery across major carriers.",
        schema_preview='{ "tracking_id", "carrier", "status", "city", "service_type" }',
        generator_class=PackageStatusGenerator,
    ),
    UseCase(
        id="trans_traffic",
        title="Traffic Incidents",
        description="Real-time traffic incident reports including type, severity, location, and estimated delays.",
        schema_preview='{ "type", "severity", "road", "city", "delay_min", "lanes_blocked" }',
        generator_class=TrafficIncidentGenerator,
    ),
    UseCase(
        id="trans_cargo",
        title="Cargo & Shipment Updates",
        description="Cargo lifecycle events from booking through customs clearance to final delivery.",
        schema_preview='{ "shipment_ref", "event", "origin", "destination", "weight_tons" }',
        generator_class=CargoUpdateGenerator,
    ),
    UseCase(
        id="trans_driver",
        title="Driver Behaviour Events",
        description="Driver safety event stream — harsh braking, rapid acceleration, speeding, and fatigue alerts.",
        schema_preview='{ "driver_id", "event_type", "severity_g", "speed_kmh", "driver_score" }',
        generator_class=DriverBehaviourGenerator,
    ),
    UseCase(
        id="trans_fuel",
        title="Fuel Consumption Readings",
        description="Vehicle fuel telemetry including consumption per trip, efficiency in L/100km, and refuel events.",
        schema_preview='{ "vehicle_id", "consumed_l", "efficiency_lp100km", "distance_km" }',
        generator_class=FuelReadingGenerator,
    ),
]
