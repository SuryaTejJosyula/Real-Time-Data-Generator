"""
Thin wrapper around azure-eventhub EventHubProducerClient (sync).
Uses a connection string + entity name to send JSON event batches.
"""

import json
from azure.eventhub import EventHubProducerClient, EventData


class EventHubClient:
    """
    Wraps the synchronous EventHubProducerClient.
    One instance per active stream; created on the sending thread.
    """

    def __init__(self, connection_string: str, eventhub_name: str):
        self._conn_str = connection_string
        self._hub_name = eventhub_name
        self._producer: EventHubProducerClient | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Open connection (call from the worker thread, not the main thread)."""
        self._producer = EventHubProducerClient.from_connection_string(
            conn_str=self._conn_str,
            eventhub_name=self._hub_name,
        )

    def close(self) -> None:
        if self._producer:
            try:
                self._producer.close()
            except Exception:
                pass
            self._producer = None

    # ── Send ──────────────────────────────────────────────────────────────────

    def send_event(self, event_dict: dict) -> None:
        """Send a single event. Must be called after connect()."""
        if not self._producer:
            raise RuntimeError("Client not connected. Call connect() first.")
        batch = self._producer.create_batch()
        batch.add(EventData(json.dumps(event_dict, default=str)))
        self._producer.send_batch(batch)

    def send_batch_events(self, events: list) -> None:
        """Send multiple events in a single batch. More efficient for high-rate streaming."""
        if not self._producer:
            raise RuntimeError("Client not connected. Call connect() first.")
        batch = self._producer.create_batch()
        for event_dict in events:
            batch.add(EventData(json.dumps(event_dict, default=str)))
        self._producer.send_batch(batch)

    # ── Test ──────────────────────────────────────────────────────────────────

    @staticmethod
    def test_connection(connection_string: str, eventhub_name: str) -> tuple[bool, str]:
        """
        Verifies the connection string is valid and the Event Hub is reachable
        by creating a producer client and fetching partition properties.
        Does NOT send any messages.
        Returns (True, "OK") or (False, error_message).
        Safe to call from any thread.
        """
        try:
            from azure.eventhub import EventHubProducerClient
            client = EventHubProducerClient.from_connection_string(
                connection_string, eventhub_name=eventhub_name
            )
            with client:
                # get_eventhub_properties() opens the connection without sending data
                client.get_eventhub_properties()
            return True, "Connection successful"
        except Exception as exc:
            return False, str(exc)
