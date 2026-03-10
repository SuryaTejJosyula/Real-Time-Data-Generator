"""
Healthcare industry generators — 6 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from faker import Faker

from core.generators.base import BaseGenerator, UseCase
from core.correlation import HEALTHCARE as _H

_fake = Faker()

_PATIENT_IDS = _H["patient_ids"]
_DEVICE_IDS  = _H["device_ids"]
_DOCTOR_IDS  = _H["doctor_ids"]


# ── 1 · Patient Vitals ────────────────────────────────────────────────────────

class PatientVitalsGenerator(BaseGenerator):
    WARDS = ["ICU", "Emergency", "General", "Cardiology", "Neurology", "Pediatrics", "Oncology"]

    def _generate_normal(self) -> dict:
        spo2 = random.uniform(88.0, 100.0)
        return {
            "reading_id":     str(uuid.uuid4()),
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "patient_id":     random.choice(_PATIENT_IDS),
            "device_id":      random.choice(_DEVICE_IDS),
            "ward":           random.choice(self.WARDS),
            "heart_rate_bpm": random.randint(45, 160),
            "bp_systolic":    random.randint(85, 185),
            "bp_diastolic":   random.randint(50, 115),
            "spo2_pct":       round(spo2, 1),
            "temp_celsius":   round(random.uniform(35.2, 40.5), 1),
            "resp_rate":      random.randint(10, 35),
            "alert":          spo2 < 92.0 or random.random() < 0.05,
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "heart_rate_bpm": 195, "spo2_pct": 72.0,
            "bp_systolic": 220, "temp_celsius": 42.1, "alert": True,
            "_anomaly": True, "_anomaly_type": "cardiac_crisis",
        })
        return evt


# ── 2 · ER Admissions ─────────────────────────────────────────────────────────

class ERAdmissionGenerator(BaseGenerator):
    TRIAGES    = ["Red", "Orange", "Yellow", "Green", "Blue"]
    COMPLAINTS = ["Chest Pain", "Stroke Symptoms", "Trauma", "Abdominal Pain",
                  "Respiratory Distress", "Fever", "Fracture", "Allergic Reaction"]
    TRANSPORT  = ["Ambulance", "Walk-in", "Police", "Air-Evac", "Referred"]

    def _generate_normal(self) -> dict:
        return {
            "admission_id":   str(uuid.uuid4()),
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "patient_id":     random.choice(_PATIENT_IDS),
            "triage_level":   random.choice(self.TRIAGES),
            "chief_complaint": random.choice(self.COMPLAINTS),
            "age":            random.randint(0, 95),
            "gender":         random.choice(["M", "F", "Other"]),
            "transport_mode": random.choice(self.TRANSPORT),
            "wait_time_min":  random.randint(0, 240),
            "er_bay":         f"BAY-{random.randint(1, 40):02d}",
            "attending_id":   random.choice(_DOCTOR_IDS),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "triage_level": "Red", "transport_mode": "Air-Evac",
            "wait_time_min": 0, "chief_complaint": "Mass Casualty Trauma",
            "_anomaly": True, "_anomaly_type": "mass_casualty",
        })
        return evt


# ── 3 · Medication Dispensing ─────────────────────────────────────────────────

class MedicationDispensingGenerator(BaseGenerator):
    MEDS    = ["Metformin", "Lisinopril", "Atorvastatin", "Amoxicillin", "Omeprazole",
               "Amlodipine", "Levothyroxine", "Metoprolol", "Albuterol", "Ibuprofen"]
    ROUTES  = ["Oral", "IV", "IM", "Subcutaneous", "Topical", "Inhaled"]
    STATUSES = ["Dispensed", "Returned", "Out-of-stock", "Expired", "Substituted"]

    def _generate_normal(self) -> dict:
        return {
            "dispense_id":  str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "patient_id":   random.choice(_PATIENT_IDS),
            "medication":   random.choice(self.MEDS),
            "dose_mg":      random.choice([5, 10, 20, 25, 50, 100, 250, 500]),
            "route":        random.choice(self.ROUTES),
            "quantity":     random.randint(1, 30),
            "pharmacy_id":  f"PHARM-{random.randint(1, 20):02d}",
            "prescriber_id": random.choice(_DOCTOR_IDS),
            "status":       random.choice(self.STATUSES),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "dose_mg": 10000, "status": "Dispensed",
            "_anomaly": True, "_anomaly_type": "wrong_dose",
        })
        return evt


# ── 4 · Lab Results ───────────────────────────────────────────────────────────

class LabResultGenerator(BaseGenerator):
    TESTS  = ["CBC", "BMP", "HbA1c", "Lipid Panel", "CRP", "TSH", "COVID-19 PCR",
              "Blood Culture", "Urinalysis", "Troponin"]
    STATUS = ["Normal", "Abnormal", "Critical", "Inconclusive", "Pending"]

    def _generate_normal(self) -> dict:
        return {
            "result_id":    str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "patient_id":   random.choice(_PATIENT_IDS),
            "test_type":    random.choice(self.TESTS),
            "lab_id":       f"LAB-{random.randint(1, 10):02d}",
            "result_value": round(random.uniform(0.1, 500.0), 2),
            "unit":         random.choice(["mg/dL", "mmol/L", "U/L", "%", "cells/μL", "ng/mL"]),
            "reference_low": round(random.uniform(0.0, 50.0), 1),
            "reference_high": round(random.uniform(100.0, 600.0), 1),
            "status":       random.choice(self.STATUS),
            "critical_flag": random.random() < 0.08,
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "status": "Critical", "critical_flag": True,
            "result_value": round(random.uniform(900.0, 9999.0), 2),
            "_anomaly": True, "_anomaly_type": "critical_value",
        })
        return evt


# ── 5 · Medical Device Alerts ─────────────────────────────────────────────────

class DeviceAlertGenerator(BaseGenerator):
    DEVICES   = ["Ventilator", "Infusion Pump", "ECG Monitor", "Pulse Oximeter",
                 "Defibrillator", "CPAP", "Dialysis Machine", "Incubator"]
    SEVERITIES = ["Info", "Warning", "Critical", "System"]

    def _generate_normal(self) -> dict:
        return {
            "alert_id":    str(uuid.uuid4()),
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "device_id":   random.choice(_DEVICE_IDS),
            "device_type": random.choice(self.DEVICES),
            "ward":        random.choice(PatientVitalsGenerator.WARDS),
            "severity":    random.choice(self.SEVERITIES),
            "code":        f"E{random.randint(1000, 9999)}",
            "message":     _fake.sentence(nb_words=6),
            "patient_id":  random.choice(_PATIENT_IDS) if random.random() > 0.3 else None,
            "acknowledged": False,
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "severity": "Critical", "code": "E9999",
            "message": "Device failure: critical hardware fault detected. Immediate service required.",
            "acknowledged": False,
            "_anomaly": True, "_anomaly_type": "device_failure",
        })
        return evt


# ── 6 · Appointment Events ────────────────────────────────────────────────────

class AppointmentEventGenerator(BaseGenerator):
    EVENTS       = ["SCHEDULED", "CONFIRMED", "CHECKED_IN", "IN_PROGRESS", "COMPLETED",
                    "CANCELLED", "NO_SHOW", "RESCHEDULED"]
    SPECIALTIES  = ["Cardiology", "Orthopedics", "Dermatology", "Neurology",
                    "Oncology", "Pediatrics", "Radiology", "General Practice"]

    def _generate_normal(self) -> dict:
        return {
            "appt_id":      str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "patient_id":   random.choice(_PATIENT_IDS),
            "doctor_id":    random.choice(_DOCTOR_IDS),
            "specialty":    random.choice(self.SPECIALTIES),
            "event_type":   random.choice(self.EVENTS),
            "duration_min": random.choice([15, 20, 30, 45, 60, 90]),
            "clinic_id":    f"CLINIC-{random.randint(1, 50):02d}",
            "telehealth":   random.random() < 0.30,
            "insurance":    random.choice(["Medicare", "Medicaid", "BlueCross", "Aetna", "Self-Pay"]),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "event_type": "CANCELLED", "duration_min": 0,
            "_anomaly": True, "_anomaly_type": "mass_cancellation",
        })
        return evt


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="health_vitals",
        title="Patient Vitals Monitoring",
        description="Continuous vital signs stream from bedside monitors — HR, BP, SpO₂, temperature, and alert flags.",
        schema_preview='{ "patient_id", "heart_rate_bpm", "bp_systolic", "spo2_pct", "alert" }',
        generator_class=PatientVitalsGenerator,
    ),
    UseCase(
        id="health_er",
        title="ER Admissions",
        description="Real-time emergency department admissions with triage level, chief complaint, and wait time.",
        schema_preview='{ "admission_id", "triage_level", "chief_complaint", "wait_time_min" }',
        generator_class=ERAdmissionGenerator,
    ),
    UseCase(
        id="health_medication",
        title="Medication Dispensing",
        description="Pharmacy dispense events including medication, dose, route, and dispensing status.",
        schema_preview='{ "patient_id", "medication", "dose_mg", "route", "status" }',
        generator_class=MedicationDispensingGenerator,
    ),
    UseCase(
        id="health_lab",
        title="Lab Results",
        description="Laboratory test result stream with values, reference ranges, and critical flags.",
        schema_preview='{ "test_type", "result_value", "unit", "status", "critical_flag" }',
        generator_class=LabResultGenerator,
    ),
    UseCase(
        id="health_device",
        title="Medical Device Alerts",
        description="Real-time alerts from ventilators, infusion pumps, ECG monitors, and other clinical devices.",
        schema_preview='{ "device_type", "severity", "code", "message", "acknowledged" }',
        generator_class=DeviceAlertGenerator,
    ),
    UseCase(
        id="health_appointments",
        title="Appointment Events",
        description="Appointment lifecycle events: scheduled, confirmed, checked-in, completed, cancelled, no-show.",
        schema_preview='{ "patient_id", "specialty", "event_type", "duration_min", "telehealth" }',
        generator_class=AppointmentEventGenerator,
    ),
]
