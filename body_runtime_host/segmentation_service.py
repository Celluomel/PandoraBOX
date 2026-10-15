"""Optional HTP-first semantic segmentation for Body camera frames."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
from typing import Any, Callable

LOG = logging.getLogger("lumina.body.segmentation")


class SemanticSegmentationService:
    MODEL_TYPE = "SegFormer-ADE20K-COCOStuff-247-HTP"
    DEFAULT_PYTHON = "/home/arduino/.venvs/yolox-infer/bin/python"
    DEFAULT_MODEL = "/home/arduino/PandoraBOX/models/indoor-segmentation/segformer-ade-coco-247.dlc"
    DEFAULT_TAXONOMY = "/home/arduino/PandoraBOX/models/indoor-segmentation/taxonomy.json"

    def __init__(self, config: Callable[[str, Any], Any], frame_provider: Callable[[], dict]):
        self._config = config
        self._frame_provider = frame_provider
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._process: subprocess.Popen | None = None
        self._last_frame_id = None
        self._retry_at = 0.0
        self._failure_count = 0
        self._latest: dict[str, Any] = {
            "state": "disabled", "frame_id": None, "mask_png_base64": None,
            "latency_ms": None, "device": None, "classes": [],
        }

    def _value(self, suffix: str, default: Any) -> Any:
        return self._config("BODY_SEGMENTATION_" + suffix, default)

    def settings(self) -> dict:
        runtime = str(self._value("RUNTIME", "htp_auto") or "htp_auto").strip().lower()
        if runtime not in {"htp_auto", "htp", "cpu"}:
            runtime = "htp_auto"
        return {
            "enabled": bool(self._value("ENABLED", False)),
            "interval_s": max(0.2, min(30.0, float(self._value("INTERVAL_S", 1.0) or 1.0))),
            "python": str(self._value("PYTHON", self.DEFAULT_PYTHON)),
            "model_path": str(self._value("MODEL_PATH", self.DEFAULT_MODEL)),
            "taxonomy_path": str(self._value("TAXONOMY_PATH", self.DEFAULT_TAXONOMY)),
            "runtime": runtime,
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
                self._latest.update(state="disabled", mask_png_base64=None, classes=[])
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._last_frame_id = None
            self._latest.update(state="starting", error=None, device=None)
            self._thread = threading.Thread(target=self._run, name="body-segmentation", daemon=True)
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
        python = str(self._value("PYTHON", self.DEFAULT_PYTHON) or self.DEFAULT_PYTHON).strip()
        model = str(self._value("MODEL_PATH", self.DEFAULT_MODEL) or self.DEFAULT_MODEL).strip()
        taxonomy = str(self._value("TAXONOMY_PATH", self.DEFAULT_TAXONOMY) or self.DEFAULT_TAXONOMY).strip()
        runtime = str(self._value("RUNTIME", "htp_auto") or "htp_auto").strip().lower()
        if runtime not in {"htp_auto", "htp", "cpu"}:
            raise RuntimeError(f"unsupported segmentation runtime: {runtime}")
        if not os.path.isfile(python):
            raise RuntimeError(f"Segmentation AppBuilder Python not found: {python}")
        if not os.path.isfile(model):
            raise RuntimeError(f"SegFormer DLC not found: {model}")
        if not os.path.isfile(taxonomy):
            raise RuntimeError(f"SegFormer taxonomy not found: {taxonomy}")
        env = os.environ.copy()
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
        dsp_paths = [
            os.path.expanduser("~/.local/share/pandorabox/yolox-dsp"),
            "/usr/lib/dsp/cdsp", "/usr/lib/rfsa/adsp",
        ]
        configured = env.get("ADSP_LIBRARY_PATH", "")
        env["ADSP_LIBRARY_PATH"] = ";".join([*dsp_paths, *(p for p in configured.split(";") if p)])
        process = subprocess.Popen(
            [python, "-u", "-m", "body_runtime_host.segmentation_worker", "--model", model,
             "--taxonomy", taxonomy, "--runtime", runtime],
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
            "frame_id": frame.get("frame_id"), "captured_at": frame.get("captured_at"),
            "image_base64": frame.get("image_base64"),
        }
        assert process.stdin is not None and process.stdout is not None
        process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(f"Segmentation worker exited ({process.poll()}); see Body runtime log")
        result = json.loads(line)
        if not result.get("ok"):
            raise RuntimeError(str(result.get("error") or "Segmentation inference failed"))
        return result

    def _run(self) -> None:
        cadence = max(0.2, min(30.0, float(self._value("INTERVAL_S", 1.0) or 1.0)))
        try:
            while not self._stop.is_set():
                if time.monotonic() < self._retry_at:
                    self._stop.wait(min(cadence, self._retry_at - time.monotonic()))
                    continue
                cycle_started = time.monotonic()
                frame = self._frame_provider() or {}
                frame_id = frame.get("frame_id")
                if frame.get("image_base64") and frame_id != self._last_frame_id:
                    self._last_frame_id = frame_id
                    started = time.monotonic()
                    try:
                        result = self._infer(frame)
                        actual_runtime = str(result.get("runtime") or "unknown")
                        result.update({
                            "state": "ready", "runtime": actual_runtime, "device": actual_runtime,
                            "frame_id": frame_id, "captured_at": frame.get("captured_at"),
                        })
                        with self._lock:
                            self._latest = result
                        self._failure_count = 0
                        self._retry_at = 0.0
                    except Exception as exc:
                        LOG.warning("Semantic segmentation unavailable: %s", str(exc)[:240])
                        self._failure_count = min(5, self._failure_count + 1)
                        self._retry_at = time.monotonic() + min(60.0, 2.0 ** self._failure_count)
                        with self._lock:
                            self._latest.update(
                                state="error", runtime=self.settings()["runtime"], device=None,
                                error=str(exc)[:240], frame_id=frame_id,
                                latency_ms=round((time.monotonic() - started) * 1000.0, 1),
                            )
                self._stop.wait(max(0.0, cadence - (time.monotonic() - cycle_started)))
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
