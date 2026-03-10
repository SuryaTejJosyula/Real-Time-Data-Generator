"""
Thin Kafka producer wrapper for Azure Event Hubs / Fabric Eventstream
Kafka-compatible endpoint.

Connection details are derived from a standard SAS connection string:
  Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=...

Bootstrap server  → <namespace>.servicebus.windows.net:9093
SASL username     → $ConnectionString
SASL password     → the full connection string
"""

import json
import re


def _bootstrap_from_conn_str(connection_string: str) -> str:
    """Parse 'namespace.servicebus.windows.net:9093' from a SAS connection string."""
    m = re.search(r"Endpoint=sb://([^/;]+)", connection_string)
    if not m:
        raise ValueError(
            "Cannot parse Kafka bootstrap server — "
            "expected 'Endpoint=sb://<host>/' in the connection string."
        )
    host = m.group(1).rstrip("/")
    return f"{host}:9093"


class KafkaClient:
    """
    Wraps kafka-python KafkaProducer for Azure Event Hubs / Fabric Eventstream.
    Exposes the same interface as EventHubClient (connect / close / send_event).
    """

    def __init__(self, connection_string: str, topic_name: str):
        self._conn_str = connection_string
        self._topic = topic_name
        self._producer = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Open connection (call from the worker thread, not the main thread)."""
        from kafka import KafkaProducer  # deferred import — optional dependency

        bootstrap = _bootstrap_from_conn_str(self._conn_str)
        self._producer = KafkaProducer(
            bootstrap_servers=[bootstrap],
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
            sasl_plain_username="$ConnectionString",
            sasl_plain_password=self._conn_str,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            request_timeout_ms=30_000,
            connections_max_idle_ms=60_000,
        )

    def close(self) -> None:
        if self._producer:
            try:
                self._producer.flush(timeout=10)
                self._producer.close(timeout=5)
            except Exception:
                pass
            self._producer = None

    # ── Send ──────────────────────────────────────────────────────────────────

    def send_event(self, event_dict: dict) -> None:
        """
        Fire-and-forget send.  The internal Kafka producer buffers events
        and flushes automatically; no per-event flush needed.
        """
        if not self._producer:
            raise RuntimeError("Client not connected. Call connect() first.")
        self._producer.send(self._topic, value=event_dict)

    # ── Test ──────────────────────────────────────────────────────────────────

    @staticmethod
    def test_connection(connection_string: str, topic_name: str) -> tuple[bool, str]:
        """
        Attempts to connect, send one test event, and flush.
        Returns (True, "OK") or (False, error_message).
        Safe to call from any thread.
        """
        try:
            client = KafkaClient(connection_string, topic_name)
            client.connect()
            client.send_event({"test": True, "source": "FabricDataGenerator"})
            client.close()
            return True, "Connection successful"
        except Exception as exc:
            return False, str(exc)
