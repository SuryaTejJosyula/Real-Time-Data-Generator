"""
StreamWorker — QObject + moveToThread() pattern for background event streaming.

Signals emitted (all cross-thread safe):
  event_sent(str json)          — one sample event (for log display)
  stats_updated(int total, float eps) — periodic stats tick
  status_changed(str)           — state label: "streaming" | "paused" | "stopped" | "error"
  error(str message)            — fatal error while streaming
  log_message(str, str)         — (message, level) for the log display

High-rate design (100ms tick batching):
  Every TICK_INTERVAL seconds the worker generates and sends a whole batch
  of events equal to (eps_target * TICK_INTERVAL).  This avoids the
  per-event sleep imprecision on Windows and keeps Event Hub sends efficient.
"""

import time
import json

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from core.eventhub_client import EventHubClient
from config import DEFAULT_EVENTS_PER_SECOND

TICK_INTERVAL = 0.5   # 500 ms ticks → large batches amortise network RTT → accurate high EPS


class StreamWorker(QObject):
    event_sent     = pyqtSignal(str)           # JSON string of one sample event
    stats_updated  = pyqtSignal(int, float)    # total_sent, events_per_sec
    status_changed = pyqtSignal(str)           # "streaming" | "paused" | "stopped" | "error"
    error          = pyqtSignal(str)           # error description
    log_message    = pyqtSignal(str, str)      # message, level
    finished       = pyqtSignal()

    def __init__(
        self,
        connection_string: str,
        eventhub_name: str,
        generator,                             # BaseGenerator instance
        events_per_second: int = DEFAULT_EVENTS_PER_SECOND,
    ):
        super().__init__()
        self._conn_str   = connection_string
        self._hub_name   = eventhub_name
        self._generator  = generator
        self._eps_target = max(1, events_per_second)

        self._running  = False
        self._paused   = False
        self._total    = 0
        self._client   = None

    # ── Control ───────────────────────────────────────────────────────────────

    def set_eps(self, eps: int) -> None:
        self._eps_target = max(1, eps)

    def pause(self) -> None:
        self._paused = True
        self.status_changed.emit("paused")
        self.log_message.emit("Streaming paused.", "PAUSED")

    def resume(self) -> None:
        self._paused = False
        self.status_changed.emit("streaming")
        self.log_message.emit("Streaming resumed.", "SUCCESS")

    def stop(self) -> None:
        self._running = False
        self._paused  = False

    # ── Main loop (runs in worker thread) ─────────────────────────────────────

    @pyqtSlot()
    def run(self):
        self._running = True
        self._total   = 0

        self.log_message.emit("Connecting to Fabric Eventstream…", "SYSTEM")
        self.status_changed.emit("streaming")

        try:
            self._client = EventHubClient(self._conn_str, self._hub_name)
            self._client.connect()
            self.log_message.emit("Connected. Streaming started.", "SUCCESS")

            window_start     = time.perf_counter()
            events_in_window = 0
            token_carry      = 0.0   # fractional-event carry for long-run accuracy

            while self._running:
                tick_start = time.perf_counter()

                if self._paused:
                    # Sleep in 100 ms chunks so pause/stop is responsive
                    for _ in range(int(TICK_INTERVAL / 0.1)):
                        if not self._paused or not self._running:
                            break
                        time.sleep(0.1)
                    continue

                # Token-bucket: accumulate fractional events so the long-run
                # rate stays exact regardless of tick jitter.
                token_carry += self._eps_target * TICK_INTERVAL
                batch_size   = int(token_carry)
                token_carry -= batch_size
                batch_size   = max(1, batch_size)

                # Generate all events for this tick
                events = [self._generator.generate() for _ in range(batch_size)]

                # Send as a single batch (efficient for high rates)
                self._client.send_batch_events(events)
                self._total       += batch_size
                events_in_window  += batch_size

                # Emit one sample event to the log display (avoid flooding the UI)
                self.event_sent.emit(json.dumps(events[0], default=str))

                # Stats update roughly every second
                now     = time.perf_counter()
                elapsed = now - window_start
                if elapsed >= 1.0:
                    eps = events_in_window / elapsed
                    self.stats_updated.emit(self._total, round(eps, 1))
                    window_start     = now
                    events_in_window = 0

                # Sleep for remainder of tick interval to honour target EPS
                tick_elapsed = time.perf_counter() - tick_start
                sleep_time   = max(0.0, TICK_INTERVAL - tick_elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as exc:
            self.log_message.emit(f"Error: {exc}", "ERROR")
            self.error.emit(str(exc))
            self.status_changed.emit("error")
        finally:
            if self._client:
                self._client.close()
            self.log_message.emit(
                f"Streaming stopped. Total events sent: {self._total}", "STOPPED"
            )
            self.stats_updated.emit(self._total, 0.0)
            self.status_changed.emit("stopped")
            self.finished.emit()

