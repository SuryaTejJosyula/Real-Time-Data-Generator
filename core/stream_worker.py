"""
StreamWorker — QObject + moveToThread() pattern for background event streaming.

Signals emitted (all cross-thread safe):
  event_sent(str json)          — one sample event (for log display)
  stats_updated(int total, float eps) — periodic stats tick
  status_changed(str)           — state label: "streaming" | "paused" | "stopped" | "error"
  error(str message)            — fatal error while streaming
  log_message(str, str)         — (message, level) for the log display

High-rate design (pipeline producer-consumer):
  NUM_CONSUMERS dedicated threads each own one persistent AMQP connection.
  The tick loop (producer) paces event generation via a token-bucket and
  pushes small per-consumer chunks onto a shared bounded queue.
  Each consumer GREEDILY drains multiple chunks between send_batch() calls,
  naturally amortising network round-trip latency so the tick loop is never
  blocked waiting for a network call to complete.

  At 1000 EPS with ~250 ms network RTT:
    each consumer accumulates ~25 events across ~5 ticks per send,
    8 consumers x ~4 sends/sec x ~31 events/send = 1000+ ev/sec sustained.
"""

import time
import json
from queue import Queue, Empty, Full
from threading import Thread, Event

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from core.eventhub_client import EventHubClient
from config import DEFAULT_EVENTS_PER_SECOND

TICK_INTERVAL   = 0.05   # 50 ms pacing ticks
NUM_CONSUMERS   = 8      # parallel AMQP connections + dedicated sender threads
QUEUE_DEPTH     = 64     # bounded queue: backpressure after ~800 ms buffer


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

    # ── Control ───────────────────────────────────────────────────────────────

    def set_eps(self, eps: int) -> None:
        self._eps_target = max(1, eps)

    def set_anomaly_mode(self, mode: bool) -> None:
        self._generator.anomaly_mode = mode
        state = "enabled" if mode else "disabled"
        level = "WARNING" if mode else "SYSTEM"
        self.log_message.emit(f"Anomaly injection {state}.", level)

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
    def run(self):  # noqa: C901
        self._running = True
        self._total   = 0

        self.log_message.emit("Connecting to Fabric Eventstream…", "SYSTEM")
        self.status_changed.emit("streaming")

        stop_evt   = Event()
        send_err   = [None]           # consumer writes; producer reads after loop
        send_queue = Queue(maxsize=QUEUE_DEPTH)

        clients = [EventHubClient(self._conn_str, self._hub_name)
                   for _ in range(NUM_CONSUMERS)]
        threads: list[Thread] = []

        def consumer(client: EventHubClient) -> None:
            """Dedicated sender thread: greedily batch then send."""
            while not stop_evt.is_set():
                # Block until at least one chunk arrives
                try:
                    chunk = send_queue.get(timeout=0.3)
                except Empty:
                    continue
                if chunk is None:          # poison-pill → shut down
                    break

                # Greedily drain additional chunks without blocking so that a
                # single send_batch() call carries all events that accumulated
                # while the previous send was in flight over the network.
                batch = list(chunk)
                while True:
                    try:
                        nxt = send_queue.get_nowait()
                    except Empty:
                        break
                    if nxt is None:
                        send_queue.put(None)   # return pill for sibling consumers
                        break
                    batch.extend(nxt)

                try:
                    client.send_batch_events(batch)
                except Exception as exc:
                    if send_err[0] is None:
                        send_err[0] = exc
                    stop_evt.set()

        try:
            for c in clients:
                c.connect()

            threads = [
                Thread(target=consumer, args=(clients[i],), daemon=True)
                for i in range(NUM_CONSUMERS)
            ]
            for t in threads:
                t.start()

            self.log_message.emit(
                f"Connected ({NUM_CONSUMERS} channels). Streaming started.", "SUCCESS"
            )

            window_start     = time.perf_counter()
            events_in_window = 0
            token_carry      = 0.0

            while self._running and not stop_evt.is_set():
                tick_start = time.perf_counter()

                if self._paused:
                    for _ in range(int(TICK_INTERVAL / 0.01)):
                        if not self._paused or not self._running:
                            break
                        time.sleep(0.01)
                    continue

                # Token-bucket pacing
                token_carry += self._eps_target * TICK_INTERVAL
                batch_size   = int(token_carry)
                token_carry -= batch_size
                batch_size   = max(1, batch_size)

                events = [self._generator.generate() for _ in range(batch_size)]

                # Slice events across consumers and enqueue without blocking
                # except under genuine backpressure (queue full for >100 ms)
                chunks = [events[i::NUM_CONSUMERS] for i in range(NUM_CONSUMERS)]
                for chunk in chunks:
                    if not chunk:
                        continue
                    while self._running and not stop_evt.is_set():
                        try:
                            send_queue.put(chunk, timeout=0.1)
                            break
                        except Full:
                            pass   # queue full → retry until consumer drains it

                self._total      += batch_size
                events_in_window += batch_size

                self.event_sent.emit(json.dumps(events[0], default=str))

                now     = time.perf_counter()
                elapsed = now - window_start
                if elapsed >= 1.0:
                    eps = events_in_window / elapsed
                    self.stats_updated.emit(self._total, round(eps, 1))
                    window_start     = now
                    events_in_window = 0

                tick_elapsed = time.perf_counter() - tick_start
                sleep_time   = max(0.0, TICK_INTERVAL - tick_elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            if send_err[0] is not None:
                raise send_err[0]

        except Exception as exc:
            self.log_message.emit(f"Error: {exc}", "ERROR")
            self.error.emit(str(exc))
            self.status_changed.emit("error")
        finally:
            stop_evt.set()
            for _ in range(NUM_CONSUMERS):   # poison-pill each consumer thread
                try:
                    send_queue.put_nowait(None)
                except Full:
                    pass
            for t in threads:
                t.join(timeout=5)
            for c in clients:
                c.close()
            self.log_message.emit(
                f"Streaming stopped. Total events sent: {self._total}", "STOPPED"
            )
            self.stats_updated.emit(self._total, 0.0)
            self.status_changed.emit("stopped")
            self.finished.emit()

