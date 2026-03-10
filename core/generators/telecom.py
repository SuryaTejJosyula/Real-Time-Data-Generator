"""
Telecommunications industry generators — 6 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from faker import Faker

from core.generators.base import BaseGenerator, UseCase
from core.correlation import TELECOM as _TEL

_fake = Faker()

_REGIONS        = ["North-East", "South-West", "Midwest", "West-Coast", "Central"]
_CELL_IDS       = _TEL["cell_ids"]
_SUBSCRIBER_IDS = _TEL["subscriber_ids"]
_NODE_IDS       = _TEL["node_ids"]
_DEVICES        = ["iPhone 16", "Samsung S25", "Pixel 9", "Xiaomi 15", "OnePlus 13", "Motorola Edge"]


# ── 1 · Network Traffic ───────────────────────────────────────────────────────

class NetworkTrafficGenerator(BaseGenerator):
    PROTOCOLS = ["HTTP", "HTTPS", "DNS", "SMTP", "FTP", "VoIP", "IoT-MQTT", "Streaming"]

    def _generate_normal(self) -> dict:
        return {
            "event_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "node_id":      random.choice(_NODE_IDS),
            "region":       random.choice(_REGIONS),
            "protocol":     random.choice(self.PROTOCOLS),
            "bytes_in":     random.randint(64, 150_000_000),
            "bytes_out":    random.randint(64, 100_000_000),
            "packets":      random.randint(1, 100000),
            "latency_ms":   round(random.uniform(0.5, 500.0), 2),
            "packet_loss_pct": round(random.uniform(0.0, 5.0), 4),
            "active_sessions": random.randint(0, 100000),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "bytes_in": 150_000_000, "packet_loss_pct": 5.0,
            "active_sessions": 100000, "latency_ms": 500.0,
            "_anomaly": True, "_anomaly_type": "ddos_attack",
        })
        return evt


# ── 2 · Call Detail Records ───────────────────────────────────────────────────

class CDRGenerator(BaseGenerator):
    CALL_TYPES  = ["Voice", "Video", "Conference", "International", "Toll-Free"]
    TERMINATIONS = ["Normal", "Busy", "No Answer", "Failed", "Dropped"]

    def _generate_normal(self) -> dict:
        duration = random.randint(0, 7200)
        return {
            "cdr_id":         str(uuid.uuid4()),
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "caller_msisdn":  _fake.phone_number(),
            "callee_msisdn":  _fake.phone_number(),
            "call_type":      random.choice(self.CALL_TYPES),
            "duration_sec":   duration,
            "originating_cell": random.choice(_CELL_IDS),
            "terminating_cell": random.choice(_CELL_IDS),
            "termination":    random.choice(self.TERMINATIONS),
            "charge_usd":     round(duration / 60 * random.uniform(0.01, 0.35), 4),
            "roaming":        random.random() < 0.08,
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "duration_sec": 86400, "charge_usd": 504.0,
            "termination": "Normal",
            "_anomaly": True, "_anomaly_type": "infinite_call",
        })
        return evt


# ── 3 · Data Usage ────────────────────────────────────────────────────────────

class DataUsageGenerator(BaseGenerator):
    NETWORKS = ["4G LTE", "5G NR", "3G", "Wi-Fi Offload", "5G mmWave"]
    APPS     = ["YouTube", "Netflix", "TikTok", "WhatsApp", "Instagram",
                "Spotify", "Chrome", "Zoom", "Games", "Other"]

    def _generate_normal(self) -> dict:
        dl = random.randint(0, 500_000_000)
        ul = random.randint(0, 100_000_000)
        return {
            "session_id":   str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "subscriber_id": random.choice(_SUBSCRIBER_IDS),
            "device":       random.choice(_DEVICES),
            "network":      random.choice(self.NETWORKS),
            "cell_id":      random.choice(_CELL_IDS),
            "app_category": random.choice(self.APPS),
            "download_bytes": dl,
            "upload_bytes":   ul,
            "duration_sec":   random.randint(1, 3600),
            "throttled":      random.random() < 0.05,
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "download_bytes": 500_000_000, "upload_bytes": 100_000_000,
            "duration_sec": 60, "throttled": True,
            "_anomaly": True, "_anomaly_type": "data_bomb",
        })
        return evt


# ── 4 · Network Fault Events ──────────────────────────────────────────────────

class NetworkFaultGenerator(BaseGenerator):
    FAULT_TYPES = ["Link Down", "High BER", "Packet Loss Spike", "Congestion",
                   "Hardware Failure", "BGP Flap", "Power Fault", "Software Crash",
                   "Capacity Breach", "Security Anomaly"]
    SEVERITIES  = ["Warning", "Minor", "Major", "Critical"]

    def _generate_normal(self) -> dict:
        return {
            "fault_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "node_id":      random.choice(_NODE_IDS),
            "fault_type":   random.choice(self.FAULT_TYPES),
            "severity":     random.choice(self.SEVERITIES),
            "region":       random.choice(_REGIONS),
            "affected_subscribers": random.randint(0, 500000),
            "duration_sec": random.randint(0, 86400),
            "ticket_id":    f"TKT-{random.randint(100000, 999999)}",
            "resolved":     random.random() < 0.35,
            "mttr_min":     random.randint(0, 480),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "fault_type": "Hardware Failure", "severity": "Critical",
            "affected_subscribers": 500000, "resolved": False,
            "_anomaly": True, "_anomaly_type": "national_outage",
        })
        return evt


# ── 5 · Customer Churn Signals ────────────────────────────────────────────────

class ChurnSignalGenerator(BaseGenerator):
    SIGNALS = ["Long Silence", "Data Downgrade", "Complaint", "Late Payment",
               "Plan Change to Prepaid", "Port-Out Enquiry", "Repeated Drops",
               "Competitor Promo Response", "NPS Detractor", "Credit Decline"]
    PLANS   = ["Basic", "Standard", "Premium", "Business", "Unlimited", "Family"]

    def _generate_normal(self) -> dict:
        score = round(random.uniform(0.0, 1.0), 4)
        return {
            "signal_id":     str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "subscriber_id": random.choice(_SUBSCRIBER_IDS),
            "signal_type":   random.choice(self.SIGNALS),
            "churn_score":   score,
            "current_plan":  random.choice(self.PLANS),
            "tenure_months": random.randint(1, 120),
            "arpu_usd":      round(random.uniform(10.0, 150.0), 2),
            "action":        "RETENTION_OFFER" if score > 0.7 else "NONE",
            "channel":       random.choice(["App", "Web", "Store", "Call Center"]),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "churn_score": 1.0, "signal_type": "Port-Out Enquiry",
            "action": "RETENTION_OFFER",
            "_anomaly": True, "_anomaly_type": "mass_churn_signal",
        })
        return evt


# ── 6 · SMS / Messaging Events ────────────────────────────────────────────────

class SMSEventGenerator(BaseGenerator):
    TYPES    = ["P2P", "A2P", "P2A", "Bulk"]
    STATUSES = ["Sent", "Delivered", "Failed", "Queued", "Expired"]

    def _generate_normal(self) -> dict:
        return {
            "msg_id":     str(uuid.uuid4()),
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "sender":     _fake.phone_number(),
            "recipient":  _fake.phone_number(),
            "msg_type":   random.choice(self.TYPES),
            "segment_count": random.randint(1, 5),
            "status":     random.choice(self.STATUSES),
            "latency_ms": random.randint(50, 30000),
            "origin_cell": random.choice(_CELL_IDS),
            "spam_flag":  random.random() < 0.02,
            "roaming":    random.random() < 0.06,
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "msg_type": "A2P", "segment_count": 5,
            "spam_flag": True, "status": "Sent",
            "_anomaly": True, "_anomaly_type": "spam_burst",
        })
        return evt


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="tel_traffic",
        title="Network Traffic",
        description="Node-level network traffic telemetry — bytes in/out, latency, packet loss, and active sessions.",
        schema_preview='{ "node_id", "protocol", "bytes_in", "latency_ms", "packet_loss_pct" }',
        generator_class=NetworkTrafficGenerator,
    ),
    UseCase(
        id="tel_cdr",
        title="Call Detail Records",
        description="Voice and video call records including duration, termination reason, roaming, and charge.",
        schema_preview='{ "caller_msisdn", "call_type", "duration_sec", "termination", "charge_usd" }',
        generator_class=CDRGenerator,
    ),
    UseCase(
        id="tel_data",
        title="Data Usage Sessions",
        description="Subscriber data session events by app category, network type, download/upload bytes.",
        schema_preview='{ "subscriber_id", "network", "app_category", "download_bytes", "throttled" }',
        generator_class=DataUsageGenerator,
    ),
    UseCase(
        id="tel_faults",
        title="Network Fault Events",
        description="Network element fault events — link down, congestion, BGP flap, with severity and impact.",
        schema_preview='{ "fault_type", "severity", "affected_subscribers", "resolved", "mttr_min" }',
        generator_class=NetworkFaultGenerator,
    ),
    UseCase(
        id="tel_churn",
        title="Customer Churn Signals",
        description="ML-scored churn risk signals from subscriber behaviour patterns with retention triggers.",
        schema_preview='{ "subscriber_id", "signal_type", "churn_score", "current_plan", "action" }',
        generator_class=ChurnSignalGenerator,
    ),
    UseCase(
        id="tel_sms",
        title="SMS & Messaging Events",
        description="SMS delivery events including P2P and A2P, latency, spam detection, and status tracking.",
        schema_preview='{ "sender", "msg_type", "status", "latency_ms", "spam_flag" }',
        generator_class=SMSEventGenerator,
    ),
]
