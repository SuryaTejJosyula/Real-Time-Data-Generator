"""
Information Technology industry generators — 4 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from faker import Faker

from core.generators.base import BaseGenerator, UseCase
from core.correlation import IT as _IT_CORR

_fake = Faker()

_HOSTS       = _IT_CORR["hosts"]
_USERNAMES   = _IT_CORR["usernames"]
_ACTOR_IDS   = _IT_CORR["actor_ids"]
_INT_IPS     = _IT_CORR["internal_ips"]
_SESSION_IDS = _IT_CORR["session_ids"]


# ── 1 · Security Logs ─────────────────────────────────────────────────────────

class SecurityLogGenerator(BaseGenerator):
    EVENT_TYPES  = ["LOGIN_SUCCESS", "LOGIN_FAILURE", "PRIVILEGE_ESCALATION",
                    "POLICY_VIOLATION", "FIREWALL_BLOCK", "IDS_ALERT",
                    "MALWARE_DETECTED", "BRUTE_FORCE", "UNAUTHORIZED_ACCESS"]
    PROTOCOLS    = ["SSH", "RDP", "HTTPS", "HTTP", "FTP", "SMB", "SFTP"]
    SEVERITIES   = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    SEV_WEIGHTS  = [3, 8, 20, 35, 34]

    def _generate_normal(self) -> dict:
        sev = random.choices(self.SEVERITIES, weights=self.SEV_WEIGHTS, k=1)[0]
        return {
            "event_id":      str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "event_type":    random.choice(self.EVENT_TYPES),
            "severity":      sev,
            "source_ip":     _fake.ipv4_public(),
            "dest_ip":       random.choice(_INT_IPS),
            "protocol":      random.choice(self.PROTOCOLS),
            "port":          random.choice([22, 80, 443, 445, 3389, 21, 25]),
            "user":          random.choice(_USERNAMES),
            "host":          random.choice(_HOSTS),
            "country":       _fake.country_code(),
            "threat_score":  round(random.uniform(0.0, 10.0), 2),
            "blocked":       sev in ("CRITICAL", "HIGH"),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "event_type": "MALWARE_DETECTED", "severity": "CRITICAL",
            "threat_score": 10.0, "blocked": False,
            "_anomaly": True, "_anomaly_type": "active_breach",
        })
        return evt


# ── 2 · Audit Logs ────────────────────────────────────────────────────────────

class AuditLogGenerator(BaseGenerator):
    ACTIONS     = ["CREATE", "READ", "UPDATE", "DELETE", "EXPORT",
                   "SHARE", "LOGIN", "LOGOUT", "PERMISSION_CHANGE", "CONFIG_CHANGE"]
    RESOURCES   = ["user_account", "database_record", "file", "api_key",
                   "cloud_bucket", "vm_instance", "encryption_key", "report"]
    OUTCOMES    = ["SUCCESS", "FAILURE", "DENIED"]
    OUT_WEIGHTS = [75, 15, 10]
    APPS        = ["ActiveDirectory", "JIRA", "Confluence", "GitHub", "AWS Console",
                   "Azure Portal", "Salesforce", "ServiceNow", "Okta"]

    def _generate_normal(self) -> dict:
        outcome = random.choices(self.OUTCOMES, weights=self.OUT_WEIGHTS, k=1)[0]
        return {
            "audit_id":       str(uuid.uuid4()),
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "actor_id":       random.choice(_ACTOR_IDS),
            "actor_email":    _fake.email(),
            "action":         random.choice(self.ACTIONS),
            "resource_type":  random.choice(self.RESOURCES),
            "resource_id":    str(uuid.uuid4())[:8],
            "application":    random.choice(self.APPS),
            "outcome":        outcome,
            "ip_address":     random.choice(_INT_IPS),
            "session_id":     random.choice(_SESSION_IDS),
            "changes_count":  random.randint(0, 20) if outcome == "SUCCESS" else 0,
            "risk_flag":      outcome == "DENIED" or random.random() < 0.05,
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "action": "DELETE", "resource_type": "database_record",
            "outcome": "SUCCESS", "changes_count": 9999, "risk_flag": True,
            "_anomaly": True, "_anomaly_type": "insider_threat",
        })
        return evt


# ── 3 · Network Logs ──────────────────────────────────────────────────────────

class NetworkLogGenerator(BaseGenerator):
    PROTOCOLS = ["TCP", "UDP", "ICMP", "DNS", "HTTP", "HTTPS", "SMTP", "NTP"]
    DIRECTIONS = ["INBOUND", "OUTBOUND", "LATERAL"]
    FLAGS      = ["SYN", "ACK", "SYN-ACK", "FIN", "RST", "PSH"]

    def _generate_normal(self) -> dict:
        bytes_sent = random.randint(64, 1_500_000)
        return {
            "flow_id":       str(uuid.uuid4()),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "src_ip":        _fake.ipv4(),
            "src_port":      random.randint(1024, 65535),
            "dst_ip":        _fake.ipv4(),
            "dst_port":      random.choice([80, 443, 53, 22, 25, 8080, 3306, 27017]),
            "protocol":      random.choice(self.PROTOCOLS),
            "direction":     random.choice(self.DIRECTIONS),
            "bytes_sent":    bytes_sent,
            "bytes_recv":    random.randint(64, 1_500_000),
            "packets":       random.randint(1, 1000),
            "duration_ms":   round(random.uniform(0.1, 30000.0), 2),
            "tcp_flags":     random.choice(self.FLAGS),
            "latency_ms":    round(random.uniform(0.2, 500.0), 2),
            "anomaly_score": round(random.uniform(0.0, 1.0), 4),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "bytes_sent": 1_500_000, "direction": "OUTBOUND", "anomaly_score": 0.99,
            "_anomaly": True, "_anomaly_type": "data_exfiltration",
        })
        return evt


# ── 4 · System Logs ───────────────────────────────────────────────────────────

class SystemLogGenerator(BaseGenerator):
    LEVELS    = ["DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL", "ALERT"]
    LVL_WGTS  = [5, 40, 15, 20, 12, 5, 3]
    SERVICES  = ["sshd", "kernel", "systemd", "cron", "nginx", "postgres",
                 "docker", "kubelet", "journald", "auditd", "NetworkManager"]
    OS_LIST   = ["Ubuntu 24.04", "RHEL 9", "Windows Server 2022",
                 "Debian 12", "Amazon Linux 2023", "CentOS Stream 9"]

    def _generate_normal(self) -> dict:
        level = random.choices(self.LEVELS, weights=self.LVL_WGTS, k=1)[0]
        return {
            "log_id":       str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "host":         random.choice(_HOSTS),
            "os":           random.choice(self.OS_LIST),
            "service":      random.choice(self.SERVICES),
            "pid":          random.randint(1, 65535),
            "level":        level,
            "message":      _fake.sentence(nb_words=random.randint(6, 14)),
            "cpu_pct":      round(random.uniform(0.0, 100.0), 1),
            "mem_pct":      round(random.uniform(0.0, 100.0), 1),
            "disk_io_kbps": round(random.uniform(0.0, 50000.0), 1),
            "uptime_hours": round(random.uniform(0.1, 8760.0), 1),
            "exit_code":    0 if level in ("DEBUG", "INFO", "NOTICE") else random.choice([0, 1, 127, 255]),
        }

    def inject_anomaly(self) -> dict:
        evt = self._generate_normal()
        evt.update({
            "level": "CRITICAL", "service": "kernel",
            "cpu_pct": 100.0, "mem_pct": 100.0, "exit_code": 255,
            "_anomaly": True, "_anomaly_type": "kernel_panic",
        })
        return evt


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="it_security",
        title="Security Logs",
        description="Real-time security events including login attempts, firewall blocks, IDS alerts, and threat detections with severity scoring.",
        schema_preview='{ "event_type", "severity", "source_ip", "threat_score", "blocked" }',
        generator_class=SecurityLogGenerator,
    ),
    UseCase(
        id="it_audit",
        title="Audit Logs",
        description="Compliance-grade audit trail of user actions across applications — creates, updates, deletes, permission changes, and config modifications.",
        schema_preview='{ "actor_email", "action", "resource_type", "application", "outcome" }',
        generator_class=AuditLogGenerator,
    ),
    UseCase(
        id="it_network",
        title="Network Logs",
        description="Network flow telemetry capturing source/destination IPs, ports, protocols, byte counts, latency, and anomaly scores.",
        schema_preview='{ "src_ip", "dst_ip", "protocol", "bytes_sent", "anomaly_score" }',
        generator_class=NetworkLogGenerator,
    ),
    UseCase(
        id="it_system",
        title="System Logs",
        description="Operating system and service logs with severity levels, CPU/memory metrics, and process details across mixed-OS infrastructure.",
        schema_preview='{ "host", "service", "level", "message", "cpu_pct", "mem_pct" }',
        generator_class=SystemLogGenerator,
    ),
]
