"""Optional HTP-backed monocular relative-depth inference for Body camera frames."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from typing import Any, Callable

LOG = logging.getLogger("lumina.body.midas")


class MiDaSDepthService:
    MODEL_TYPE = "MiDaS-V2-Small-HTP"
    DEFAULT_PYTHON = "/home/arduino/.venvs/yolox-infer/bin/python"
    DEFAULT_MODEL = "/home/arduino/models/midas-qualcomm/midas-float.dlc"

    def __init__(self, config: Callable[[str, Any], Any], frame_provider: Callable[[], dict]):
        self._config = config
        self._frame_provider = frame_provider
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._process: subprocess.Popen | None = None
        self._last_frame_id = None
        self._raw_output_until = 0.0
        self._analyzed_frame: dict[str, Any] | None = None
        self._retry_at = 0.0
        self._failure_count = 0
        self._latest: dict[str, Any] = {
            "state": "disabled", "frame_id": None, "depth_jpeg_base64": None,
            "latency_ms": None, "depth_type": "relative", "device": None,
        }

    def _value(self, suffix: str, default: Any) -> Any:
        return self._config("BODY_MIDAS_" + suffix, default)

    @staticmethod
    def _remaining_cadence_wait(cadence: float, started_at: float, now: float) -> float:
        return max(0.0, cadence - (now - started_at))

    def settings(self) -> dict:
        runtime = str(self._value("RUNTIME", "htp_auto") or "htp_auto").strip().lower()
        if runtime not in {"htp_auto", "htp", "cpu"}:
            runtime = "htp_auto"
        return {
            "enabled": bool(self._value("ENABLED", False)),
            "interval_s": max(0.15, min(30.0, float(self._value("INTERVAL_S", 0.5) or 0.5))),
            "python": str(self._value("PYTHON", self.DEFAULT_PYTHON)),
            "model_path": str(self._value("MODEL_PATH", self.DEFAULT_MODEL)),
            **self.status(),
            "runtime": runtime,
            "model": self.MODEL_TYPE,
        }

    def status(self) -> dict:
        with self._lock:
            return dict(self._latest)

    def request_raw_output(self, seconds: float = 60.0) -> None:
        with self._lock:
            self._raw_output_until = max(self._raw_output_until, time.monotonic() + max(0.0, seconds))

    def _raw_output_requested(self) -> bool:
        with self._lock:
            return time.monotonic() < self._raw_output_until

    def analyzed_frame(self, frame_id: str | None = None) -> dict[str, Any] | None:
        """Return the bounded camera frame used for the latest MiDaS result."""
        with self._lock:
            frame = self._analyzed_frame
            if not frame or (frame_id is not None and str(frame.get("frame_id")) != str(frame_id)):
                return None
            return dict(frame)

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
            self._last_frame_id = None
            self._latest.update(state="starting", error=None, device=None, runtime=self.settings()["runtime"])
            self._thread = threading.Thread(target=self._run, name="body-midas-htp", daemon=True)
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
            thread.join(timeout=3.0)
        self._thread = None

    def reconfigure(self) -> None:
        self.stop()
        self.start()

    def _worker(self) -> subprocess.Popen:
        python = str(self._value("PYTHON", self.DEFAULT_PYTHON) or self.DEFAULT_PYTHON).strip()
        model = str(self._value("MODEL_PATH", self.DEFAULT_MODEL) or self.DEFAULT_MODEL).strip()
        runtime = str(self._value("RUNTIME", "htp_auto") or "htp_auto").strip().lower()
        if runtime not in {"htp_auto", "htp", "cpu"}:
            raise RuntimeError(f"unsupported MiDaS runtime: {runtime}")
        if not os.path.isfile(python):
            raise RuntimeError(f"MiDaS AppBuilder Python not found: {python}")
        if not os.path.isfile(model):
            raise RuntimeError(f"MiDaS HTP DLC not found: {model}")
        env = os.environ.copy()
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
        dsp_paths = [
            os.path.expanduser("~/.local/share/pandorabox/yolox-dsp"),
            "/usr/lib/dsp/cdsp",
            "/usr/lib/rfsa/adsp",
        ]
        configured_dsp_path = env.get("ADSP_LIBRARY_PATH", "")
        env["ADSP_LIBRARY_PATH"] = ";".join(
            [*dsp_paths, *(path for path in configured_dsp_path.split(";") if path)]
        )
        process = subprocess.Popen(
            [python, "-u", "-m", "body_runtime_host.midas_worker", "--model", model, "--runtime", runtime],
            cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1,
        )
        self._process = process
        return process

    def _infer(self, frame: dict) -> dict:
        process = self._process
        if process is None or process.poll() is not None:
            process = self._worker()
        request = {
            "frame_id": frame.get("frame_id"),
            "captured_at": frame.get("captured_at"),
            "image_base64": frame.get("image_base64"),
            "include_raw": self._raw_output_requested(),
        }
        assert process.stdin is not None and process.stdout is not None
        process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(f"MiDaS HTP worker exited ({process.poll()}); see Body runtime log")
        result = json.loads(line)
        if not result.get("ok"):
            raise RuntimeError(str(result.get("error") or "MiDaS HTP inference failed"))
        return result

    def _run(self) -> None:
        try:
            while not self._stop.is_set():
                cadence = max(0.15, min(30.0, float(self._value("INTERVAL_S", 0.5) or 0.5)))
                if time.monotonic() < self._retry_at:
                    self._stop.wait(min(cadence, self._retry_at - time.monotonic()))
                    continue
                cycle_started = time.monotonic()
                frame = self._frame_provider() or {}
                frame_id = frame.get("frame_id")
                if frame.get("image_base64") and frame_id != self._last_frame_id:
                    self._last_frame_id = frame_id
                    started = time.monotonic()
                    worker_received_at = time.time()
                    try:
                        result = self._infer(frame)
                        actual_runtime = str(result.get("runtime") or "unknown")
                        published_at = time.time()
                        result.update({
                            "state": "ready", "runtime": actual_runtime, "device": actual_runtime,
                            "frame_id": frame_id, "captured_at": frame.get("captured_at"),
                            "depth_type": "relative", "worker_received_at": worker_received_at,
                            "published_at": published_at,
                        })
                        with self._lock:
                            self._latest = result
                            self._analyzed_frame = {
                                key: frame[key] for key in (
                                    "frame_id", "captured_at", "image_base64", "mime_type",
                                    "width", "height", "source", "camera_profile",
                                ) if key in frame
                            }
                        self._failure_count = 0
                        self._retry_at = 0.0
                    except Exception as exc:
                        LOG.warning("MiDaS inference unavailable: %s", str(exc)[:240])
                        self._failure_count = min(5, self._failure_count + 1)
                        self._retry_at = time.monotonic() + min(60.0, 2.0 ** self._failure_count)
                        with self._lock:
                            self._latest.update(
                                state="error", runtime=self.settings()["runtime"], device=None,
                                error=str(exc)[:240], frame_id=frame_id,
                                latency_ms=round((time.monotonic() - started) * 1000.0, 1),
                            )
                cadence = max(0.15, min(30.0, float(self._value("INTERVAL_S", cadence) or cadence)))
                remaining = self._remaining_cadence_wait(cadence, cycle_started, time.monotonic())
                self._stop.wait(remaining)
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
            with self._lock:
                if self._latest.get("state") not in {"error", "disabled"}:
                    self._latest["state"] = "stopped"
