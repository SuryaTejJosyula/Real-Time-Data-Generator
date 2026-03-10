"""
Manufacturing industry generators — 6 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from core.generators.base import BaseGenerator, UseCase

_MACHINES  = [f"MACH-{i:04d}" for i in range(1, 201)]
_LINES     = [f"LINE-{i:02d}" for i in range(1, 21)]
_PLANTS    = [f"PLANT-{i:02d}" for i in range(1, 6)]
_SHIFTS    = ["Morning", "Afternoon", "Night"]


# ── 1 · Machine Sensor Readings ───────────────────────────────────────────────

class MachineSensorGenerator(BaseGenerator):
    SENSORS = ["Temperature", "Vibration", "Pressure", "RPM", "Current", "Voltage", "Torque"]

    def generate(self) -> dict:
        sensor = random.choice(self.SENSORS)
        ranges = {
            "Temperature": (15.0, 350.0, "°C"),
            "Vibration":   (0.0,  20.0,  "mm/s"),
            "Pressure":    (0.5,  250.0, "bar"),
            "RPM":         (100,  8000,  "rpm"),
            "Current":     (0.5,  300.0, "A"),
            "Voltage":     (200,  480,   "V"),
            "Torque":      (10,   5000,  "Nm"),
        }
        lo, hi, unit = ranges[sensor]
        value = round(random.uniform(float(lo), float(hi)), 2)
        threshold = hi * 0.90
        return {
            "reading_id": str(uuid.uuid4()),
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "machine_id": random.choice(_MACHINES),
            "line_id":    random.choice(_LINES),
            "plant":      random.choice(_PLANTS),
            "sensor_type": sensor,
            "value":      value,
            "unit":       unit,
            "threshold":  round(threshold, 2),
            "alarm":      value > threshold,
        }


# ── 2 · Quality Defects ───────────────────────────────────────────────────────

class QualityDefectGenerator(BaseGenerator):
    DEFECT_TYPES = ["Dimensional", "Surface Scratch", "Wrong Assembly", "Contamination",
                    "Missing Component", "Weld Failure", "Color Mismatch", "Weight OOT"]
    SEVERITY     = ["Minor", "Major", "Critical"]
    DISPOSITIONS = ["Rework", "Scrap", "Accept as-is", "Hold for Review"]

    def generate(self) -> dict:
        return {
            "defect_id":    str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "part_number":  f"PN-{random.randint(100000, 999999)}",
            "batch_id":     f"BATCH-{random.randint(1000, 9999)}",
            "line_id":      random.choice(_LINES),
            "plant":        random.choice(_PLANTS),
            "defect_type":  random.choice(self.DEFECT_TYPES),
            "severity":     random.choice(self.SEVERITY),
            "qty_defective": random.randint(1, 100),
            "disposition":  random.choice(self.DISPOSITIONS),
            "inspector_id": f"QC-{random.randint(1, 50):03d}",
        }


# ── 3 · Production Throughput ─────────────────────────────────────────────────

class ProductionThroughputGenerator(BaseGenerator):
    def generate(self) -> dict:
        target = random.randint(100, 2000)
        actual = int(target * random.uniform(0.65, 1.10))
        return {
            "record_id":     str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "line_id":       random.choice(_LINES),
            "plant":         random.choice(_PLANTS),
            "shift":         random.choice(_SHIFTS),
            "product_code":  f"PROD-{random.randint(1, 500):04d}",
            "target_units":  target,
            "actual_units":  actual,
            "oee_pct":       round(random.uniform(55.0, 98.0), 1),
            "downtime_min":  random.randint(0, 60),
            "scrap_units":   random.randint(0, int(actual * 0.05)),
        }


# ── 4 · Energy Consumption per Machine ───────────────────────────────────────

class MachineEnergyGenerator(BaseGenerator):
    def generate(self) -> dict:
        active_kw = round(random.uniform(0.5, 500.0), 2)
        return {
            "reading_id":   str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "machine_id":   random.choice(_MACHINES),
            "plant":        random.choice(_PLANTS),
            "active_kw":    active_kw,
            "reactive_kvar": round(active_kw * random.uniform(0.1, 0.6), 2),
            "power_factor": round(random.uniform(0.70, 1.00), 3),
            "kwh_today":    round(random.uniform(0.0, 1000.0), 2),
            "cost_today_usd": round(random.uniform(0.0, 120.0), 2),
            "state":        random.choice(["Running", "Idle", "Standby", "Off"]),
        }


# ── 5 · Maintenance Alerts ────────────────────────────────────────────────────

class MaintenanceAlertGenerator(BaseGenerator):
    TYPES    = ["Predictive", "Preventive", "Corrective", "Emergency", "Routine"]
    SEVERITY = ["Low", "Medium", "High", "Critical"]
    COMPS    = ["Bearing", "Motor", "Gearbox", "Hydraulics", "Belt", "Valve",
                "Filter", "Coolant System", "Conveyor", "Spindle"]

    def generate(self) -> dict:
        return {
            "alert_id":    str(uuid.uuid4()),
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "machine_id":  random.choice(_MACHINES),
            "plant":       random.choice(_PLANTS),
            "alert_type":  random.choice(self.TYPES),
            "component":   random.choice(self.COMPS),
            "severity":    random.choice(self.SEVERITY),
            "mtbf_hours":  random.randint(500, 50000),
            "last_service_days": random.randint(0, 365),
            "est_downtime_hr": round(random.uniform(0.5, 48.0), 1),
            "work_order":  f"WO-{random.randint(10000, 99999)}",
            "technician":  f"TECH-{random.randint(1, 100):03d}",
        }


# ── 6 · Raw Material Usage ────────────────────────────────────────────────────

class RawMaterialUsageGenerator(BaseGenerator):
    MATERIALS = ["Steel", "Aluminium", "Copper", "Plastic Resin", "Rubber",
                 "Glass Fibre", "Chemical A", "Chemical B", "Lubricant", "Paint"]
    UNITS     = ["kg", "litres", "tonnes", "pieces", "metres"]

    def generate(self) -> dict:
        return {
            "usage_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "material":     random.choice(self.MATERIALS),
            "batch_id":     f"BATCH-{random.randint(1000, 9999)}",
            "plant":        random.choice(_PLANTS),
            "quantity_used": round(random.uniform(0.1, 5000.0), 2),
            "unit":         random.choice(self.UNITS),
            "stock_before": round(random.uniform(100, 50000), 2),
            "stock_after":  round(random.uniform(0, 50000), 2),
            "cost_per_unit": round(random.uniform(0.10, 500.0), 2),
            "supplier_id":  f"SUP-{random.randint(1, 200):04d}",
        }


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="mfg_sensors",
        title="Machine Sensor Readings",
        description="Continuous sensor telemetry from factory machines — temperature, vibration, pressure, RPM, and alarm flags.",
        schema_preview='{ "machine_id", "sensor_type", "value", "unit", "threshold", "alarm" }',
        generator_class=MachineSensorGenerator,
    ),
    UseCase(
        id="mfg_defects",
        title="Quality Defects",
        description="Real-time quality inspection events with defect type, severity, batch, and disposition decisions.",
        schema_preview='{ "part_number", "defect_type", "severity", "qty_defective", "disposition" }',
        generator_class=QualityDefectGenerator,
    ),
    UseCase(
        id="mfg_throughput",
        title="Production Throughput",
        description="Line-level production output per shift — actual vs target units, OEE %, and downtime minutes.",
        schema_preview='{ "line_id", "shift", "target_units", "actual_units", "oee_pct", "downtime_min" }',
        generator_class=ProductionThroughputGenerator,
    ),
    UseCase(
        id="mfg_energy",
        title="Machine Energy Consumption",
        description="Per-machine energy readings — active power kW, power factor, daily kWh, and estimated cost.",
        schema_preview='{ "machine_id", "active_kw", "power_factor", "kwh_today", "state" }',
        generator_class=MachineEnergyGenerator,
    ),
    UseCase(
        id="mfg_maintenance",
        title="Maintenance Alerts",
        description="Predictive and corrective maintenance alerts including component, severity, and estimated downtime.",
        schema_preview='{ "machine_id", "alert_type", "component", "severity", "est_downtime_hr" }',
        generator_class=MaintenanceAlertGenerator,
    ),
    UseCase(
        id="mfg_materials",
        title="Raw Material Usage",
        description="Real-time material consumption events tracking stock level changes and cost per batch.",
        schema_preview='{ "material", "quantity_used", "unit", "stock_after", "cost_per_unit" }',
        generator_class=RawMaterialUsageGenerator,
    ),
]
