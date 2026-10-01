"""Optional local PC camera capture for the independent Body process.

OpenCV is deliberately optional: a Body host without a camera dependency must
still start and expose its management API.  When available, this class keeps
one bounded latest-frame buffer so camera capture cannot block the sensor loop.
"""
from __future__ import annotations

import base64
import logging
import platform
import threading
import time
from typing import Any

LOG = logging.getLogger("lumina.body.camera")


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


class LocalCameraCapture:
    def __init__(self, device_index: int = 0, interval: float = 0.5,
                 width: int = 640, height: int = 480, profile: str = "low_body_front"):
        self.device_index = max(0, int(device_index or 0))
        self.interval = max(1.0 / 60.0, float(interval or 0.5))
        self.width = max(640, int(width or 640))
        self.height = max(480, int(height or 480))
        self.profile = str(profile or "low_body_front")
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._capture = None
        self._capture_backend = ""
        self._latest: dict[str, Any] = {}
        self._status = "stopped"
        self._error = ""
        self._started_at: float | None = None

    def start(self) -> dict[str, Any]:
        if self._thread and self._thread.is_alive():
            return self.status()
        self._stop.clear()
        self._status = "starting"
        self._error = ""
        self._started_at = time.time()
        self._thread = threading.Thread(target=self._run, name="body-pc-camera", daemon=True)
        self._thread.start()
        return self.status()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self._thread = None
        self._release()
        self._status = "stopped"
        return self.status()

    def reconfigure(self, **settings: Any) -> None:
        with self._lock:
            self.device_index = max(0, int(settings.get("device_index", self.device_index) or 0))
            self.interval = max(1.0 / 60.0, float(settings.get("interval", self.interval) or 0.5))
            self.width = max(640, int(settings.get("width", self.width) or 640))
            self.height = max(480, int(settings.get("height", self.height) or 480))
            self.profile = str(settings.get("profile", self.profile) or self.profile)
            capture = self._capture
            width, height = self.width, self.height

        # OpenCV accepts property changes while a capture is running on most
        # webcams. The loop still resizes every frame, so drivers that ignore
        # the request remain usable at the selected Body output dimensions.
        if capture is not None:
            try:
                import cv2
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            except Exception:
                LOG.debug("Could not apply live camera resolution", exc_info=True)

    def latest(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._latest)

    def status(self) -> dict[str, Any]:
        with self._lock:
            frame = dict(self._latest)
        captured_at = float(frame.get("captured_at") or 0.0)
        return {
            "status": self._status,
            "available": self._status in {"capturing", "starting"},
            "device_index": self.device_index,
            "interval": self.interval,
            "width": self.width,
            "height": self.height,
            "profile": self.profile,
            "frame_id": frame.get("frame_id"),
            "frame_age_s": round(max(0.0, time.time() - captured_at), 3) if captured_at else None,
            "last_error": self._error,
            "opencv": self._opencv_available(),
            "backend": self._capture_backend or None,
        }

    @staticmethod
    def _opencv_available() -> bool:
        try:
            import cv2  # noqa: F401
            return True
        except ImportError:
            return False

    def _release(self) -> None:
        capture = self._capture
        self._capture = None
        self._capture_backend = ""
        if capture is not None:
            try:
                capture.release()
            except Exception:
                LOG.debug("Could not release local camera", exc_info=True)

    @staticmethod
    def _open_capture(cv2, device_index: int):
        system = platform.system()
        backends = {
            "Windows": (("CAP_DSHOW", "DirectShow"), ("CAP_MSMF", "Media Foundation"), ("CAP_ANY", "automatic")),
            "Linux": (("CAP_V4L2", "V4L2"), ("CAP_ANY", "automatic")),
            "Darwin": (("CAP_AVFOUNDATION", "AVFoundation"), ("CAP_ANY", "automatic")),
        }.get(system, (("CAP_ANY", "automatic"),))
        attempted = set()
        for constant, label in backends:
            backend = getattr(cv2, constant, None)
            if backend is None or backend in attempted:
                continue
            attempted.add(backend)
            capture = None
            try:
                capture = cv2.VideoCapture(device_index, backend)
                if capture is not None and capture.isOpened():
                    return capture, label
            except Exception:
                LOG.debug("Camera open failed using %s", label, exc_info=True)
            if capture is not None:
                try:
                    capture.release()
                except Exception:
                    pass
        return None, ""

    def _run(self) -> None:
        try:
            import cv2
        except ImportError:
            self._status = "unavailable"
            self._error = "OpenCV is not installed; install body_requirements.txt"
            LOG.warning("PC camera unavailable: %s", self._error)
            return
        self._capture, self._capture_backend = self._open_capture(cv2, self.device_index)
        if self._capture is None or not self._capture.isOpened():
            self._status = "unavailable"
            self._error = f"camera device {self.device_index} could not be opened"
            LOG.warning("PC camera unavailable: %s", self._error)
            self._release()
            return
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._status = "capturing"
        LOG.info("Local camera capture started (device=%d, backend=%s, requested=%dx%d)", self.device_index, self._capture_backend, self.width, self.height)
        try:
            while not self._stop.is_set():
                ok, frame = self._capture.read()
                if not ok:
                    self._error = "camera read failed"
                    self._stop.wait(min(1.0, self.interval))
                    continue
                actual_height, actual_width = frame.shape[:2]
                if actual_width != self.width or actual_height != self.height:
                    frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
                ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if not ok:
                    self._error = "JPEG encoding failed"
                    continue
                captured_at = time.time()
                payload = {
                    "image_base64": base64.b64encode(encoded.tobytes()).decode("ascii"),
                    "mime_type": "image/jpeg",
                    "width": self.width,
                    "height": self.height,
                    "frame_id": f"pc-camera-{int(captured_at * 1000)}",
                    "captured_at": captured_at,
                    "source": "pc_camera",
                    "device_index": self.device_index,
                    "camera_profile": self.profile,
                }
                with self._lock:
                    self._latest = payload
                    self._error = ""
                self._stop.wait(self.interval)
        finally:
            self._release()
            if self._status == "capturing":
                self._status = "stopped"
            LOG.info("PC camera capture stopped")
