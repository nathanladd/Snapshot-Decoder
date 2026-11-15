"""
Anonymous usage metrics, posted to the collector on Rudi.

The Windows twin of the web app's src/infrastructure/metrics.ts. Same
collector, same events, same shapes -- the only difference on the wire is
the site name, "snapshot-desktop", which is how the Rudi dashboard tells
the two apps apart. Keep the event list below in step with metrics.ts and
with ALLOWED_EVENTS in rudi-ops/rudi-metrics/app.py: the collector drops
anything it doesn't know.

What it will not do:

  * Send anything from inside a snapshot's *values*. PID names go --
    `P_L_Battery_raw` is a field name out of the ECU map, the same on
    every machine of that type. Readings, file names and folder paths
    stay on this computer. `scrub_reason()` exists for the one place a
    file name could sneak out: a load error's message.
  * Identify anyone. The install id is a random UUID this app made up for
    itself, kept in %APPDATA%\\SnapshotDecoder\\metrics.json. The user's
    IP is turned into a country/state by the collector and then dropped.
  * Interrupt anything. Every failure is swallowed and nothing is retried.
    Sending happens on a background thread, so a slow or missing network
    never stalls the UI. Metrics are never worth a broken app.

There is deliberately no user setting to turn this off (decided with Nate,
2026-11-15). The About box says what is sent.

It only sends from the built app (`sys.frozen`), so running from source
can't quietly write into real numbers. Set SNAPSHOT_METRICS_FORCE=1 to
send from a dev run when testing.
"""

from __future__ import annotations

import atexit
import json
import ntpath
import os
import re
import sys
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional

from domain.user_paths import backup_corrupt_file, user_data_file
from version import APP_VERSION

ENDPOINT = "https://rudi-hq.com/api/events"
SITE = "snapshot-desktop"
FORCE_ENV = "SNAPSHOT_METRICS_FORCE"
ID_FILE = "metrics.json"

# Longer than the web's 3 s: a classroom of installs shares one address,
# and the collector's rate limit is per address.
FLUSH_DELAY_SECONDS = 10.0
MAX_QUEUE = 20
SEND_TIMEOUT_SECONDS = 5.0
# On exit the app waits this long at most -- closing must never feel slow.
EXIT_TIMEOUT_SECONDS = 2.0

# Same caps the web uses. The collector discards a detail over 2 KB
# outright, so a 40-PID chart would otherwise cost the whole event.
MAX_PIDS = 12
MAX_REASON = 200

ALLOWED_EVENTS = frozenset({
    "app_open",
    "snapshot_opened",
    "snapshot_failed",
    "quick_chart",
    "my_chart",
    "custom_chart",
    "my_chart_saved",
    "chart_to_cart",
    "pdf_exported",
    "subplots_toggled",
    "data_table_viewed",
    "parse_timing",
    "client_error",
})

Sender = Callable[[Dict[str, Any], float], None]


def _post(payload: Dict[str, Any], timeout: float) -> None:
    """POST one batch. Imported lazily so a dev run never pays for httpx."""
    import httpx

    httpx.post(
        ENDPOINT,
        json=payload,
        timeout=timeout,
        headers={"User-Agent": f"SnapshotDecoder/{APP_VERSION}"},
    )


class _Metrics:
    def __init__(self, sender: Sender = _post, enabled: Optional[bool] = None):
        self._sender = sender
        self._enabled = enabled
        self._queue: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._visitor: Optional[str] = None
        # A new session each launch, like a new browser tab.
        self._session = uuid.uuid4().hex

    # ------------------------------------------------------------------
    # Switches and ids
    # ------------------------------------------------------------------
    def enabled(self) -> bool:
        if self._enabled is not None:
            return self._enabled
        return bool(getattr(sys, "frozen", False)) or os.environ.get(FORCE_ENV) == "1"

    def visitor(self) -> str:
        """This install's random id, made once and kept in %APPDATA%."""
        if self._visitor:
            return self._visitor
        path = user_data_file(ID_FILE)
        try:
            with open(path, "r", encoding="utf-8") as f:
                stored = json.load(f).get("visitor")
            if isinstance(stored, str) and 0 < len(stored) <= 64:
                self._visitor = stored
                return stored
        except FileNotFoundError:
            pass
        except Exception:
            backup_corrupt_file(path)

        self._visitor = uuid.uuid4().hex
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"visitor": self._visitor}, f)
        except Exception:
            # An id that can't be kept just makes the next launch look like
            # a new install -- a rounding error, not a failure.
            pass
        return self._visitor

    # ------------------------------------------------------------------
    # Recording and sending
    # ------------------------------------------------------------------
    def track(self, event: str, action_id: Optional[str] = None,
              detail: Optional[Dict[str, Any]] = None) -> None:
        if event not in ALLOWED_EVENTS or not self.enabled():
            return
        item: Dict[str, Any] = {"event": event}
        if action_id:
            item["action_id"] = action_id
        if detail:
            item["detail"] = detail

        with self._lock:
            self._queue.append(item)
            full = len(self._queue) >= MAX_QUEUE
            if not full and self._timer is None:
                self._timer = threading.Timer(FLUSH_DELAY_SECONDS, self.flush)
                self._timer.daemon = True
                self._timer.start()
        if full:
            self.flush()

    def _take(self) -> List[Dict[str, Any]]:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            pending, self._queue = self._queue, []
        return pending

    def _payload(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "site": SITE,
            "visitor": self.visitor(),
            "session": self._session,
            "events": events,
        }

    def _send(self, events: List[Dict[str, Any]], timeout: float) -> None:
        try:
            self._sender(self._payload(events), timeout)
        except Exception:
            # Offline, proxy, firewall, collector down -- all fine. Gone
            # rather than retried: a queue that survives failure would
            # eventually replay a stale burst.
            pass

    def flush(self) -> None:
        """Send what's queued, on a background thread."""
        pending = self._take()
        if pending:
            threading.Thread(
                target=self._send, args=(pending, SEND_TIMEOUT_SECONDS), daemon=True
            ).start()

    def flush_on_exit(self) -> None:
        """Send what's queued now, waiting at most EXIT_TIMEOUT_SECONDS."""
        pending = self._take()
        if pending:
            self._send(pending, EXIT_TIMEOUT_SECONDS)


_metrics = _Metrics()


def track(event: str, action_id: Optional[str] = None,
          detail: Optional[Dict[str, Any]] = None) -> None:
    """Record one event. Cheap, safe to call from anywhere, never raises."""
    try:
        _metrics.track(event, action_id, detail)
    except Exception:
        pass


def start_metrics() -> None:
    """Count this launch and make sure a part-full queue is sent on exit."""
    if not _metrics.enabled():
        return
    track("app_open", detail={"version": APP_VERSION})
    atexit.register(_metrics.flush_on_exit)


# ----------------------------------------------------------------------
# Helpers for the call sites
# ----------------------------------------------------------------------
_WINDOWS_PATH = re.compile(r"[A-Za-z]:[\\/][^'\"\n]*")
_UNC_PATH = re.compile(r"\\\\[^'\"\n]+")


def scrub_reason(message: str, file_path: Optional[str] = None) -> str:
    """A load error's text with the file's name and any path taken out.

    Load errors are pipeline messages ("Missing header row"), but Python's
    own errors quote the path -- and a file is often named after the
    customer or the machine. The web only ever sends the message; this
    makes the desktop match.
    """
    text = str(message)
    if file_path:
        # ntpath splits on both \\ and /, so this also works when the tests
        # feed it a Windows path on Linux.
        name = ntpath.basename(file_path)
        stem = ntpath.splitext(name)[0]
        for found in (file_path, file_path.replace("\\", "\\\\"), name, stem):
            if found:
                text = text.replace(found, "<file>")
    text = _UNC_PATH.sub("<path>", text)
    text = _WINDOWS_PATH.sub("<path>", text)
    return text[:MAX_REASON]


def pid_detail(primary: List[str], secondary: List[str]) -> Dict[str, List[str]]:
    """A chart's PIDs, capped the way the web caps them."""
    return {"primary": list(primary)[:MAX_PIDS], "secondary": list(secondary)[:MAX_PIDS]}
