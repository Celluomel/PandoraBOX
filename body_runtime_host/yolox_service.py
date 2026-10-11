"""Bounded, optional YOLOX inference bridge for the Body camera stream."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from typing import Any, Callable

LOG = logging.getLogger("lumina.body.yolox")


class YoloXService:
    def __init__(self, config: Callable[[str, Any], Any], frame_provider: Callable[[], dict],
                 ambiguous_callback: Callable[[dict, dict], None] | None = None):
        self._config = config
        self._frame_provider = frame_provider
        self._ambiguous_callback = ambiguous_callback
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._process: subprocess.Popen | None = None
        self._last_frame_id = None
        self._last_fallback_at = 0.0
        self._failure_count = 0
        self._retry_at = 0.0
        self._status: dict[str, Any] = {"state": "disabled", "detections": [], "latency_ms": None}
        self._analyzed_frame: dict[str, Any] | None = None

    def _value(self, suffix: str, default: Any) -> Any:
        return self._config("BODY_YOLO_" + suffix, default)

    def settings(self) -> dict:
        return {
            "enabled": bool(self._value("ENABLED", False)),
            "python": str(self._value("PYTHON", "/home/arduino/.venvs/yolox-infer/bin/python")),
            "model_path": str(self._value("MODEL_PATH", "/home/arduino/models/yolox-qairt245/yolox-qnn_dlc-w8a8/yolox.dlc")),
            "runtime": str(self._value("RUNTIME", "htp_auto")),
            "confidence": float(self._value("CONFIDENCE", 0.25)),
            "ambiguity_margin": float(self._value("AMBIGUITY_MARGIN", 0.12)),
            "vlm_fallback": bool(self._value("VLM_FALLBACK", True)),
            "vlm_cooldown_s": float(self._value("VLM_COOLDOWN_S", 15.0)),
            "interval_s": float(self._value("INTERVAL_S", 0.5)),
            **self.status(),
        }

    def status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def analyzed_frame(self, frame_id: str | None = None) -> dict | None:
        with self._lock:
            frame = self._analyzed_frame
            if not frame or (frame_id is not None and str(frame.get("frame_id")) != str(frame_id)):
                return None
            return dict(frame)

    def start(self) -> None:
        if not bool(self._value("ENABLED", False)):
            self.stop()
            with self._lock:
                self._status.update(state="disabled", detections=[])
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._status.update(state="starting", error=None)
            self._thread = threading.Thread(target=self._run, name="body-yolox", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        process = self._process
        self._process = None
        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=3)
        self._thread = None

    def reconfigure(self) -> None:
        self.stop()
        self.start()

    def _worker(self) -> subprocess.Popen:
        python = str(self._value("PYTHON", sys.executable) or sys.executable).strip()
        model = str(self._value("MODEL_PATH", "") or "").strip()
        runtime = str(self._value("RUNTIME", "htp_auto") or "htp_auto")
        if not model:
            raise RuntimeError("Set the YOLOX model path in Body camera settings")
        if not os.path.isfile(python):
            raise RuntimeError(f"YOLOX Python interpreter not found: {python}")
        env = os.environ.copy()
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
        process = subprocess.Popen(
            [python, "-u", "-m", "body_runtime_host.yolox_worker", "--model", model, "--runtime", runtime],
            cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1,
        )
        self._process = process
        return process

    def _infer(self, frame: dict) -> dict:
        process = self._process
        if process is None or process.poll() is not None:
            process = self._worker()
        request = {"frame_id": frame.get("frame_id"), "captured_at": frame.get("captured_at"),
                   "width": frame.get("width"), "height": frame.get("height"),
                   "image_base64": frame.get("image_base64"),
                   "confidence": float(self._value("CONFIDENCE", 0.25)),
                   "ambiguity_margin": float(self._value("AMBIGUITY_MARGIN", 0.12))}
        assert process.stdin is not None and process.stdout is not None
        process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(f"YOLOX worker exited ({process.poll()}); see Body runtime log")
        response = json.loads(line)
        if not response.get("ok"):
            raise RuntimeError(str(response.get("error") or "YOLOX inference failed"))
        return response

    def _run(self) -> None:
        cadence = max(0.15, min(5.0, float(self._value("INTERVAL_S", 0.5) or 0.5)))
        try:
            while not self._stop.is_set():
                if time.monotonic() < self._retry_at:
                    self._stop.wait(min(cadence, self._retry_at - time.monotonic()))
                    continue
                frame = self._frame_provider() or {}
                frame_id = frame.get("frame_id")
                if frame.get("image_base64") and frame_id != self._last_frame_id:
                    self._last_frame_id = frame_id
                    started = time.monotonic()
                    try:
                        result = self._infer(frame)
                        detections = result.get("detections") or []
                        result.update({"state": "ready", "frame_id": frame_id,
                                       "captured_at": frame.get("captured_at"),
                                       "latency_ms": round((time.monotonic() - started) * 1000, 1)})
                        with self._lock:
                            self._status = result
                            self._analyzed_frame = dict(frame)
                        self._failure_count = 0
                        self._retry_at = 0.0
                        self._maybe_fallback(frame, result)
                    except Exception as exc:
                        LOG.warning("YOLOX inference unavailable: %s", str(exc)[:240])
                        with self._lock:
                            self._status.update(state="error", error=str(exc)[:240],
                                                frame_id=frame_id, detections=[],
                                                latency_ms=round((time.monotonic() - started) * 1000, 1))
                        self._failure_count = min(5, self._failure_count + 1)
                        self._retry_at = time.monotonic() + min(30.0, 2.0 ** self._failure_count)
                self._stop.wait(cadence)
        finally:
            process, self._process = self._process, None
            if process is not None:
                try:
                    process.terminate()
                    process.wait(timeout=1)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass
            if bool(self._value("ENABLED", False)):
                with self._lock:
                    if self._status.get("state") != "error":
                        self._status["state"] = "stopped"

    def _maybe_fallback(self, frame: dict, result: dict) -> None:
        if not bool(self._value("VLM_FALLBACK", True)) or self._ambiguous_callback is None:
            return
        if not result.get("ambiguous"):
            return
        now = time.monotonic()
        cooldown = max(5.0, min(300.0, float(self._value("VLM_COOLDOWN_S", 15.0) or 15.0)))
        with self._lock:
            if now - self._last_fallback_at < cooldown:
                return
            self._last_fallback_at = now
        try:
            self._ambiguous_callback(frame, result)
        except Exception:
            LOG.debug("YOLOX ambiguity fallback could not be queued", exc_info=True)
