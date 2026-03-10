"""
Energy & Utilities industry generators — 6 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from core.generators.base import BaseGenerator, UseCase

_METERS  = [f"MTR-{i:07d}" for i in range(1, 201)]
_GRIDS   = [f"GRID-{i:03d}" for i in range(1, 31)]
_REGIONS = ["North", "South", "East", "West", "Central"]


# ── 1 · Smart Meter Readings ──────────────────────────────────────────────────

class SmartMeterGenerator(BaseGenerator):
    TARIFFS = ["Flat", "Time-of-Use", "Tiered", "EV", "Commercial"]

    def generate(self) -> dict:
        consumption = round(random.uniform(0.0, 15.0), 3)
        return {
            "reading_id":      str(uuid.uuid4()),
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "meter_id":        random.choice(_METERS),
            "account_id":      f"ACC-{random.randint(1, 5000000):08d}",
            "consumption_kwh": consumption,
            "demand_kw":       round(random.uniform(0.0, 20.0), 2),
            "voltage_v":       round(random.uniform(110.0, 250.0), 1),
            "power_factor":    round(random.uniform(0.70, 1.00), 3),
            "tariff":          random.choice(self.TARIFFS),
            "tamper_alert":    random.random() < 0.005,
        }


# ── 2 · Grid Load Monitoring ──────────────────────────────────────────────────

class GridLoadGenerator(BaseGenerator):
    def generate(self) -> dict:
        capacity = round(random.uniform(100.0, 5000.0), 1)
        load     = round(capacity * random.uniform(0.3, 1.05), 1)
        return {
            "reading_id":    str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "grid_id":       random.choice(_GRIDS),
            "region":        random.choice(_REGIONS),
            "load_mw":       load,
            "capacity_mw":   capacity,
            "utilisation_pct": round((load / capacity) * 100, 1),
            "frequency_hz":  round(random.uniform(49.5, 50.5), 3),
            "voltage_kv":    round(random.uniform(100.0, 400.0), 1),
            "overload":      load > capacity,
        }


# ── 3 · Renewable Energy Output ───────────────────────────────────────────────

class RenewableOutputGenerator(BaseGenerator):
    SOURCE_TYPES = ["Solar", "Wind", "Hydro", "Geothermal", "Tidal"]

    def generate(self) -> dict:
        rated = round(random.uniform(1.0, 2000.0), 1)
        actual = round(rated * random.uniform(0.0, 1.05), 1)
        return {
            "event_id":      str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "plant_id":      f"REN-{random.randint(1, 500):04d}",
            "source":        random.choice(self.SOURCE_TYPES),
            "region":        random.choice(_REGIONS),
            "rated_mw":      rated,
            "output_mw":     min(actual, rated),
            "capacity_factor": round((min(actual, rated) / rated), 3),
            "curtailed_mw":  round(max(0, actual - rated), 2),
            "co2_avoided_t": round(actual * 0.233 * random.uniform(0.8, 1.2), 2),
        }


# ── 4 · Pipeline / Gas Pressure ───────────────────────────────────────────────

class PipelinePressureGenerator(BaseGenerator):
    FLUIDS = ["Natural Gas", "Crude Oil", "Water", "Steam", "Hydrogen", "CO2"]

    def generate(self) -> dict:
        max_p  = round(random.uniform(20.0, 200.0), 1)
        actual = round(max_p * random.uniform(0.5, 1.15), 2)
        return {
            "reading_id":   str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "segment_id":   f"PIPE-{random.randint(1, 500):04d}",
            "fluid":        random.choice(self.FLUIDS),
            "region":       random.choice(_REGIONS),
            "pressure_bar": actual,
            "max_safe_bar": max_p,
            "flow_m3h":     round(random.uniform(0, 10000), 1),
            "temp_celsius": round(random.uniform(-10.0, 80.0), 1),
            "leak_detected": actual > max_p * 1.1 or random.random() < 0.01,
        }


# ── 5 · Outage Events ─────────────────────────────────────────────────────────

class OutageEventGenerator(BaseGenerator):
    CAUSES    = ["Equipment Failure", "Weather", "Animal Contact", "Human Error",
                 "Maintenance", "Overload", "Cyber Incident", "Unknown"]
    STATUSES  = ["OPEN", "IN_PROGRESS", "RESTORED", "PARTIAL_RESTORE"]

    def generate(self) -> dict:
        cust = random.randint(1, 50000)
        return {
            "outage_id":       str(uuid.uuid4()),
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "grid_id":         random.choice(_GRIDS),
            "region":          random.choice(_REGIONS),
            "cause":           random.choice(self.CAUSES),
            "status":          random.choice(self.STATUSES),
            "customers_affected": cust,
            "mwh_lost":        round(random.uniform(0.1, 5000.0), 2),
            "duration_min":    random.randint(0, 4320),
            "priority":        random.choice(["Low", "Medium", "High", "Critical"]),
            "crew_dispatched": random.randint(0, 20),
        }


# ── 6 · Demand Forecast ───────────────────────────────────────────────────────

class DemandForecastGenerator(BaseGenerator):
    HORIZON = ["1H", "6H", "24H", "48H", "7D"]
    MODELS  = ["ARIMA", "LSTM", "XGBoost", "Prophet", "EnsembleV2"]

    def generate(self) -> dict:
        forecast = round(random.uniform(200.0, 8000.0), 1)
        actual   = round(forecast * random.uniform(0.90, 1.10), 1)
        return {
            "forecast_id":   str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "region":        random.choice(_REGIONS),
            "horizon":       random.choice(self.HORIZON),
            "model":         random.choice(self.MODELS),
            "forecast_mw":   forecast,
            "actual_mw":     actual,
            "mape_pct":      round(abs(actual - forecast) / forecast * 100, 2),
            "confidence_pct": round(random.uniform(80.0, 99.5), 1),
            "temperature_c": round(random.uniform(-20.0, 45.0), 1),
        }


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="energy_meter",
        title="Smart Meter Readings",
        description="Interval-based smart meter consumption, demand, and voltage readings with tamper detection.",
        schema_preview='{ "meter_id", "consumption_kwh", "demand_kw", "voltage_v", "tamper_alert" }',
        generator_class=SmartMeterGenerator,
    ),
    UseCase(
        id="energy_grid",
        title="Grid Load Monitoring",
        description="Real-time grid segment load vs capacity, utilisation percentage, and frequency measurement.",
        schema_preview='{ "grid_id", "load_mw", "capacity_mw", "utilisation_pct", "overload" }',
        generator_class=GridLoadGenerator,
    ),
    UseCase(
        id="energy_renewable",
        title="Renewable Energy Output",
        description="Live generation output from solar, wind, hydro, and geothermal plants with CO₂ avoidance.",
        schema_preview='{ "source", "output_mw", "capacity_factor", "curtailed_mw", "co2_avoided_t" }',
        generator_class=RenewableOutputGenerator,
    ),
    UseCase(
        id="energy_pipeline",
        title="Pipeline Pressure Monitoring",
        description="Gas and oil pipeline segment pressure, flow rate, temperature, and leak detection alerts.",
        schema_preview='{ "segment_id", "fluid", "pressure_bar", "max_safe_bar", "leak_detected" }',
        generator_class=PipelinePressureGenerator,
    ),
    UseCase(
        id="energy_outage",
        title="Grid Outage Events",
        description="Power outage events with cause, affected customers, MWh lost, duration, and crew dispatch.",
        schema_preview='{ "grid_id", "cause", "status", "customers_affected", "mwh_lost" }',
        generator_class=OutageEventGenerator,
    ),
    UseCase(
        id="energy_forecast",
        title="Demand Forecast",
        description="Rolling demand forecasts from ML models vs actual load with MAPE accuracy scoring.",
        schema_preview='{ "region", "horizon", "model", "forecast_mw", "actual_mw", "mape_pct" }',
        generator_class=DemandForecastGenerator,
    ),
]
