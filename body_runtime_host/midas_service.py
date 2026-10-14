"""Optional, low-rate monocular relative-depth inference for the Body camera."""
from __future__ import annotations

import base64
import logging
import threading
import time
from typing import Any, Callable

LOG = logging.getLogger("lumina.body.midas")


class MiDaSDepthService:
    MODEL_TYPE = "MiDaS_small"

    def __init__(self, config: Callable[[str, Any], Any], frame_provider: Callable[[], dict]):
        self._config = config
        self._frame_provider = frame_provider
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._model = None
        self._transform = None
        self._torchvision_ops_library = None
        self._device = "cpu"
        self._last_frame_id = None
        self._retry_at = 0.0
        self._failure_count = 0
        self._latest: dict[str, Any] = {
            "state": "disabled", "frame_id": None, "depth_jpeg_base64": None,
            "latency_ms": None, "depth_type": "relative",
        }

    def _value(self, suffix: str, default: Any) -> Any:
        return self._config("BODY_MIDAS_" + suffix, default)

    def settings(self) -> dict:
        return {
            "enabled": bool(self._value("ENABLED", False)),
            "interval_s": max(1.0, min(30.0, float(self._value("INTERVAL_S", 2.0) or 2.0))),
            "model": self.MODEL_TYPE,
            **self.status(),
        }

    def status(self) -> dict:
        with self._lock:
            return dict(self._latest)

    def start(self) -> None:
        if not bool(self._value("ENABLED", False)):
            self.stop()
            with self._lock:
                self._latest.update(state="disabled", depth_jpeg_base64=None)
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._latest.update(state="starting", error=None)
            self._thread = threading.Thread(target=self._run, name="body-midas-depth", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=3.0)
        self._thread = None

    def reconfigure(self) -> None:
        self.stop()
        self.start()

    def _load_model(self) -> None:
        import torch

        # The Ventuno CPU Torch build omits these optional torchvision operators;
        # MiDaS needs torchvision imports but never calls either NMS operation.
        library = torch.library.Library("torchvision", "FRAGMENT")
        for name in ("nms", "qnms"):
            try:
                torch._C._dispatch_find_schema_or_throw(f"torchvision::{name}", "")
            except RuntimeError:
                library.define(
                    f"{name}(Tensor boxes, Tensor scores, float iou_threshold) -> Tensor"
                )
        self._torchvision_ops_library = library
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        model = torch.hub.load("isl-org/MiDaS", self.MODEL_TYPE, trust_repo=True)
        transforms = torch.hub.load("isl-org/MiDaS", "transforms", trust_repo=True)
        model.to(self._device).eval()
        self._model = model
        self._transform = transforms.small_transform

    def _infer(self, frame: dict) -> dict:
        import cv2
        import numpy as np
        import torch

        if self._model is None:
            self._load_model()
        raw = base64.b64decode(frame["image_base64"])
        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError("Could not decode captured camera frame")
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        started = time.monotonic()
        with torch.inference_mode():
            sample = self._transform(rgb).to(self._device)
            prediction = self._model(sample)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1), size=rgb.shape[:2], mode="bicubic", align_corners=False,
            ).squeeze()
        depth = prediction.float().cpu().numpy()
        low, high = np.percentile(depth, (2, 98))
        normalized = np.clip((depth - low) / max(float(high - low), 1e-6), 0.0, 1.0)
        gray = np.asarray(normalized * 255.0, dtype=np.uint8)
        colored = cv2.applyColorMap(gray, cv2.COLORMAP_TURBO)
        gray_ok, gray_encoded = cv2.imencode(".jpg", gray, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
        if not gray_ok:
            raise RuntimeError("Could not encode MiDaS relative-depth samples")
        ok, encoded = cv2.imencode(".jpg", colored, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            raise RuntimeError("Could not encode MiDaS depth visualization")
        return {
            "state": "ready", "frame_id": frame.get("frame_id"),
            "captured_at": frame.get("captured_at"), "depth_type": "relative",
            "width": int(rgb.shape[1]), "height": int(rgb.shape[0]),
            "device": self._device,
            "latency_ms": round((time.monotonic() - started) * 1000.0, 1),
            "depth_gray_jpeg_base64": base64.b64encode(gray_encoded.tobytes()).decode("ascii"),
            "depth_jpeg_base64": base64.b64encode(encoded.tobytes()).decode("ascii"),
        }

    def _run(self) -> None:
        cadence = max(1.0, min(30.0, float(self._value("INTERVAL_S", 2.0) or 2.0)))
        try:
            while not self._stop.is_set():
                frame = self._frame_provider() or {}
                frame_id = frame.get("frame_id")
                if (frame.get("image_base64") and frame_id != self._last_frame_id
                        and time.monotonic() >= self._retry_at):
                    self._last_frame_id = frame_id
                    try:
                        result = self._infer(frame)
                        with self._lock:
                            self._latest = result
                        self._failure_count = 0
                        self._retry_at = 0.0
                    except Exception as exc:
                        LOG.warning("MiDaS depth inference unavailable: %s", str(exc)[:240])
                        self._failure_count = min(5, self._failure_count + 1)
                        self._retry_at = time.monotonic() + min(60.0, 2.0 ** self._failure_count)
                        with self._lock:
                            self._latest.update(state="error", error=str(exc)[:240], frame_id=frame_id)
                self._stop.wait(cadence)
        finally:
            with self._lock:
                if self._latest.get("state") not in {"error", "disabled"}:
                    self._latest["state"] = "stopped"
