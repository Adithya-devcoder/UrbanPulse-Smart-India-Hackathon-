"""
UrbanPulse — YOLO → FastAPI Bridge
Sends detection events from run.py to the backend API in real-time.
Import this in run.py and call bridge.post_detection(event_type, data, loc).
"""

import json
import threading
import queue
import time
try:
    import urllib.request
    import urllib.error
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False

# ── Config ────────────────────────────────────────────────────────────────────
BACKEND_URL    = "http://127.0.0.1:8000"
BRIDGE_SECRET  = "urbanpulse-sih-secret"
ENDPOINT       = f"{BACKEND_URL}/api/v1/ai/detections"
MAX_QUEUE      = 500
BATCH_INTERVAL = 2.0   # seconds between flushes

# Mapping from run.py event types to backend module_type values
MODULE_MAP = {
    "POTHOLE":      "pothole",
    "WATERLOGGING": "pothole",      # road defect category
    "ACCIDENT":     "vehicle",      # vehicle event
    "HTR":          "vehicle",
    "OBSTACLE":     "pedestrian",
    "SIGN_ISSUE":   "traffic_sign",
    "TRAFFIC":      "vehicle",
}

SEVERITY_MAP = {
    "POTHOLE":      "medium",
    "WATERLOGGING": "medium",
    "ACCIDENT":     "critical",
    "HTR":          "critical",
    "OBSTACLE":     "low",
    "SIGN_ISSUE":   "low",
    "TRAFFIC":      "low",
}


class YoloBridge:
    """
    Non-blocking queue-based bridge.
    Collects detection events and flushes to the backend every BATCH_INTERVAL seconds.
    Falls back silently if backend is unreachable.
    """

    def __init__(self):
        self._q       = queue.Queue(maxsize=MAX_QUEUE)
        self._online  = False
        self._thread  = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        self._check_backend()

    def _check_backend(self):
        """Quick health check — don't crash if backend is down."""
        try:
            req = urllib.request.Request(
                f"{BACKEND_URL}/health",
                headers={"Accept": "application/json"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=2):
                self._online = True
                print(f"  ✓ Backend bridge connected → {BACKEND_URL}")
        except Exception:
            self._online = False
            print(f"  ⚠ Backend not reachable at {BACKEND_URL} — bridge disabled (detections saved locally)")

    def post_detection(self, event_type: str, loc: dict, extra: dict = None):
        """
        Queue a detection for sending to the backend.
        Non-blocking — drops if queue is full.
        """
        if not self._online:
            return
        payload = {
            "module_type":     MODULE_MAP.get(event_type, "vehicle"),
            "severity":        SEVERITY_MAP.get(event_type, "low"),
            "event_type":      event_type,
            "latitude":        loc.get("latitude", 13.0827),
            "longitude":       loc.get("longitude", 80.2707),
            "bus_id":          loc.get("bus_id", "MTC-DEMO-001"),
            "timestamp":       loc.get("timestamp", ""),
            "confidence":      (extra or {}).get("confidence", 0.5),
            "description":     f"{event_type} detected by UrbanPulse YOLO engine",
            "extra":           extra or {}
        }
        try:
            self._q.put_nowait(payload)
        except queue.Full:
            pass   # silently drop if queue is full

    def _worker(self):
        """Background thread — drains queue and POSTs to backend."""
        while True:
            time.sleep(BATCH_INTERVAL)
            batch = []
            while not self._q.empty():
                try:
                    batch.append(self._q.get_nowait())
                except queue.Empty:
                    break

            for item in batch:
                self._send(item)

    def _send(self, payload: dict):
        try:
            data = json.dumps(payload).encode("utf-8")
            req  = urllib.request.Request(
                ENDPOINT,
                data=data,
                headers={
                    "Content-Type":    "application/json",
                    "X-Bridge-Secret": BRIDGE_SECRET,
                    "Accept":          "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5):
                pass
        except Exception:
            pass   # silently fail — detections are already saved as JSON locally


# ── Singleton ─────────────────────────────────────────────────────────────────
bridge = YoloBridge()
