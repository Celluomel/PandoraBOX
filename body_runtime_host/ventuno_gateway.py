"""VENTUNO Q Linux gateway for a FNK0031 servo board.

The VENTUNO Q is the network/AI computer.  The FNK0031 board remains the
motor and servo controller.  This process keeps PandoraBOX's robot protocol
stable while forwarding validated requests to the FNK0031 board over HTTP.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import os
import subprocess
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from body_runtime_host.fnk0031_protocol import normalize_command, normalize_sensors

LOG = logging.getLogger("ventuno.fnk0031.gateway")
ALLOWED_COMMANDS = frozenset({
    "forward", "backward", "turn_left", "turn_right", "sprint", "retreat",
    "wait", "grab", "release", "push", "stop",
})


def _json_request(method: str, url: str, payload: Optional[Dict[str, Any]] = None,
                  token: str = "", timeout: float = 3.0) -> Any:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def validate_command(payload: Any) -> tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "command must be a JSON object"
    command = str(payload.get("type") or "").strip().lower()
    if command not in ALLOWED_COMMANDS:
        return False, f"unsupported command: {command or 'empty'}"
    if payload.get("params") is not None and not isinstance(payload.get("params"), dict):
        return False, "command params must be an object"
    return True, ""


class VentunoGateway:
    def __init__(self, board_url: str, board_token: str = "", gateway_token: str = "",
                 actuation_enabled: bool = False, watchdog_seconds: float = 2.0,
                 timeout: float = 3.0, deploy_enabled: bool = False,
                 deploy_dir: str = "/opt/pandorabox/deployments",
                 body_service: str = "pandorabox-body",
                 body_health_url: str = "http://127.0.0.1:8766/health",
                 restart_timeout: float = 30.0) -> None:
        self.board_url = str(board_url or "").rstrip("/")
        self.board_token = str(board_token or "")
        self.gateway_token = str(gateway_token or "")
        self.actuation_enabled = bool(actuation_enabled)
        self.watchdog_seconds = max(0.5, float(watchdog_seconds or 2.0))
        self.timeout = max(0.5, float(timeout or 3.0))
        self.deploy_enabled = bool(deploy_enabled)
        self.deploy_dir = Path(deploy_dir).expanduser()
        self.body_service = str(body_service or "").strip()
        self.body_health_url = str(body_health_url or "").strip()
        self.restart_timeout = max(5.0, float(restart_timeout or 30.0))
        self._lock = threading.RLock()
        self._last_command_at = 0.0
        self._last_command = ""
        self._last_error = ""
        self._stop_sent = False

    def authorized(self, authorization: str) -> bool:
        return not self.gateway_token or authorization == f"Bearer {self.gateway_token}"

    def health(self) -> Dict[str, Any]:
        board = {"reachable": False}
        try:
            board = _json_request("GET", f"{self.board_url}/health", token=self.board_token, timeout=self.timeout) or {}
            board = {"reachable": True, **(board if isinstance(board, dict) else {})}
        except Exception as exc:
            board = {"reachable": False, "error": str(exc)[:180]}
        with self._lock:
            return {
                "ok": bool(board.get("reachable")),
                "gateway": "ventuno_q_linux",
                "actuator": "fnk0031_servo_board",
                "board": board,
                "actuation_enabled": self.actuation_enabled,
                "deploy_enabled": self.deploy_enabled,
                "last_command": self._last_command,
                "last_error": self._last_error,
            }

    def stage_bundle(self, raw: bytes) -> Dict[str, Any]:
        """Validate and stage a Body bundle without activating it."""
        if not self.deploy_enabled:
            raise PermissionError("deployment staging is disabled on the VENTUNO gateway")
        if not raw:
            raise ValueError("deployment bundle is empty")
        try:
            source = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile as exc:
            raise ValueError("deployment bundle is not a valid ZIP") from exc
        with source:
            names = source.namelist()
            for name in names:
                candidate = Path(name)
                if candidate.is_absolute() or ".." in candidate.parts:
                    raise ValueError("deployment bundle contains an unsafe path")
            manifest = {}
            if "BODY_BUNDLE_MANIFEST.json" in names:
                try:
                    manifest = json.loads(source.read("BODY_BUNDLE_MANIFEST.json").decode("utf-8"))
                except (ValueError, UnicodeDecodeError) as exc:
                    raise ValueError("deployment manifest is invalid") from exc
            if manifest.get("contract") != "pandorabox.body_bundle.v1":
                raise ValueError("unsupported Body bundle contract")
            self.deploy_dir.mkdir(parents=True, exist_ok=True)
            stage = self.deploy_dir / f"bundle-{int(time.time() * 1000)}"
            stage.mkdir()
            source.extractall(stage)
        return {"staged": True, "stage_id": stage.name, "path": str(stage), "manifest": manifest}

    def deployment_status(self) -> Dict[str, Any]:
        self.deploy_dir.mkdir(parents=True, exist_ok=True)
        current = self.deploy_dir / "current"
        active = None
        if current.is_symlink():
            active = current.resolve().name
        elif (self.deploy_dir / "current.json").exists():
            try:
                active = str(json.loads((self.deploy_dir / "current.json").read_text(encoding="utf-8")).get("active_stage") or "") or None
            except (OSError, ValueError):
                active = None
        staged = sorted(path.name for path in self.deploy_dir.glob("bundle-*") if path.is_dir())
        return {"deploy_enabled": self.deploy_enabled, "active_stage": active, "staged": staged}

    def activate_bundle(self, stage_id: str) -> Dict[str, Any]:
        """Point the VENTUNO release marker at a validated staged bundle."""
        if not self.deploy_enabled:
            raise PermissionError("deployment activation is disabled on the VENTUNO gateway")
        requested = Path(str(stage_id or "").strip())
        if not requested.name.startswith("bundle-") or requested.name != str(requested):
            raise ValueError("stage_id must be a bundle name")
        stage = (self.deploy_dir / requested.name).resolve()
        root = self.deploy_dir.resolve()
        if root not in stage.parents or not stage.is_dir():
            raise ValueError("staged bundle was not found")
        manifest_path = stage / "BODY_BUNDLE_MANIFEST.json"
        if not manifest_path.exists():
            raise ValueError("staged bundle has no manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("contract") != "pandorabox.body_bundle.v1":
            raise ValueError("unsupported Body bundle contract")
        current = self.deploy_dir / "current"
        previous = current.resolve().name if current.is_symlink() else None
        if previous is None and (self.deploy_dir / "current.json").exists():
            try:
                previous = str(json.loads((self.deploy_dir / "current.json").read_text(encoding="utf-8")).get("active_stage") or "") or None
            except (OSError, ValueError):
                previous = None
        (self.deploy_dir / "previous.json").write_text(json.dumps({"active_stage": previous}), encoding="utf-8")
        try:
            temporary = self.deploy_dir / ".current.new"
            if temporary.exists() or temporary.is_symlink():
                temporary.unlink()
            temporary.symlink_to(stage, target_is_directory=True)
            os.replace(temporary, current)
            marker = "symlink"
        except OSError:
            # Windows development hosts may not grant symlink privileges.
            # The VENTUNO target normally uses the atomic symlink path above;
            # the marker keeps local packaging/tests and Windows gateways usable.
            marker_path = self.deploy_dir / "current.json"
            temporary_marker = self.deploy_dir / ".current.new.json"
            temporary_marker.write_text(json.dumps({"active_stage": stage.name}, indent=2), encoding="utf-8")
            os.replace(temporary_marker, marker_path)
            marker = "json-marker"
        return {
            "activated": True,
            "active_stage": stage.name,
            "previous_stage": previous,
            "restart_required": True,
            "activation_marker": marker,
            "manifest": manifest,
        }

    def _switch_active(self, stage_id: str) -> str:
        stage = (self.deploy_dir / stage_id).resolve()
        root = self.deploy_dir.resolve()
        if root not in stage.parents or not stage.is_dir():
            raise ValueError("staged bundle was not found")
        current = self.deploy_dir / "current"
        try:
            temporary = self.deploy_dir / ".current.new"
            if temporary.exists() or temporary.is_symlink():
                temporary.unlink()
            temporary.symlink_to(stage, target_is_directory=True)
            os.replace(temporary, current)
            return "symlink"
        except OSError:
            marker_path = self.deploy_dir / "current.json"
            temporary_marker = self.deploy_dir / ".current.new.json"
            temporary_marker.write_text(json.dumps({"active_stage": stage.name}, indent=2), encoding="utf-8")
            os.replace(temporary_marker, marker_path)
            return "json-marker"

    def restart_body(self) -> Dict[str, Any]:
        """Restart the configured Body service and rollback if health fails."""
        if not self.deploy_enabled:
            raise PermissionError("deployment restart is disabled on the VENTUNO gateway")
        if not self.body_service:
            raise ValueError("body service name is not configured")
        current = self.deployment_status().get("active_stage")
        if not current:
            raise ValueError("no active Body bundle is selected")
        if not self.body_health_url:
            raise ValueError("Body health URL is not configured")
        try:
            completed = subprocess.run(
                ["systemctl", "restart", self.body_service],
                check=False, capture_output=True, text=True, timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"could not restart Body service: {exc}") from exc
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or "systemctl restart failed").strip()[:240])
        deadline = time.monotonic() + self.restart_timeout
        last_error = ""
        while time.monotonic() < deadline:
            try:
                with urlopen(self.body_health_url, timeout=2.0) as response:
                    if 200 <= response.status < 300:
                        raw = response.read().decode("utf-8")
                        return {"ok": True, "active_stage": current, "health": json.loads(raw) if raw else {}}
            except Exception as exc:
                last_error = str(exc)[:180]
            time.sleep(0.5)
        previous_path = self.deploy_dir / "previous.json"
        previous = None
        if previous_path.exists():
            try:
                previous = json.loads(previous_path.read_text(encoding="utf-8")).get("active_stage")
            except (OSError, ValueError):
                previous = None
        if previous and previous != current:
            self._switch_active(str(previous))
            subprocess.run(["systemctl", "restart", self.body_service], check=False, timeout=15)
        raise RuntimeError(f"Body health check failed after restart; rollback={bool(previous and previous != current)}: {last_error}")

    def sensors(self) -> Any:
        return normalize_sensors(_json_request("GET", f"{self.board_url}/sensors", token=self.board_token, timeout=self.timeout))

    def stop(self, reason: str = "gateway stop") -> Any:
        with self._lock:
            self._stop_sent = True
            self._last_command = "stop"
            self._last_command_at = time.monotonic()
        try:
            return _json_request("POST", f"{self.board_url}/stop", {"reason": reason}, self.board_token, self.timeout)
        except Exception as exc:
            with self._lock:
                self._last_error = str(exc)
            raise

    def command(self, payload: Dict[str, Any]) -> Any:
        payload = normalize_command(payload)
        valid, reason = validate_command(payload)
        if not valid:
            raise ValueError(reason)
        command = str(payload["type"]).strip().lower()
        if command == "stop":
            return self.stop("command requested stop")
        if not self.actuation_enabled:
            raise PermissionError("physical actuation is disabled on the VENTUNO gateway")
        with self._lock:
            self._last_command = command
            self._last_command_at = time.monotonic()
            self._stop_sent = False
        try:
            return _json_request("POST", f"{self.board_url}/command", payload, self.board_token, self.timeout)
        except Exception as exc:
            with self._lock:
                self._last_error = str(exc)
            raise

    def watchdog_loop(self, stop_event: threading.Event) -> None:
        while not stop_event.wait(0.2):
            with self._lock:
                expired = (
                    self.actuation_enabled and self._last_command_at > 0
                    and time.monotonic() - self._last_command_at > self.watchdog_seconds
                    and not self._stop_sent
                )
            if expired:
                try:
                    LOG.warning("FNK0031 command watchdog expired; sending stop")
                    self.stop("VENTUNO gateway watchdog expired")
                except Exception as exc:
                    LOG.error("FNK0031 watchdog stop failed: %s", exc)


def serve(gateway: VentunoGateway, host: str, port: int) -> None:
    stop_event = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        server_version = "PandoraBOX-VENTUNO-Gateway/1"

        def _reply(self, payload: Any, status: int = 200) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self) -> bool:
            return gateway.authorized(self.headers.get("Authorization", ""))

        def _body(self) -> Dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            value = json.loads(raw.decode("utf-8"))
            return value if isinstance(value, dict) else value

        def _raw_body(self) -> bytes:
            length = int(self.headers.get("Content-Length", "0") or 0)
            return self.rfile.read(length) if length else b""

        def do_GET(self) -> None:  # noqa: N802
            if not self._authorized():
                self._reply({"error": "unauthorized"}, 401)
                return
            try:
                if self.path == "/health":
                    self._reply(gateway.health())
                elif self.path == "/sensors":
                    self._reply(gateway.sensors())
                elif self.path == "/capabilities":
                    board = _json_request("GET", f"{gateway.board_url}/capabilities", gateway.board_token, gateway.timeout)
                    if not isinstance(board, dict):
                        board = {}
                    self._reply({
                        **board,
                        "platform": "ventuno_q_gateway",
                        "gateway": "ventuno_q",
                        "actuator": board.get("actuator", "fnk0031_servo_board"),
                        "commands": board.get("commands") or sorted(ALLOWED_COMMANDS),
                        # Optional VENTUNO peripherals are advertised by their
                        # own drivers; do not mark them detected here.
                        "modules": board.get("modules") or [],
                    })
                elif self.path == "/modules/status":
                    self._reply(_json_request("GET", f"{gateway.board_url}/modules/status", gateway.board_token, gateway.timeout))
                elif self.path == "/deploy/status":
                    self._reply(gateway.deployment_status())
                else:
                    self._reply({"error": "not found"}, 404)
            except Exception as exc:
                self._reply({"error": str(exc)[:240]}, 503)

        def do_POST(self) -> None:  # noqa: N802
            if not self._authorized():
                self._reply({"error": "unauthorized"}, 401)
                return
            try:
                if self.path == "/deploy":
                    self._reply(gateway.stage_bundle(self._raw_body()))
                    return
                payload = self._body()
                if self.path == "/command":
                    self._reply(gateway.command(payload))
                elif self.path == "/stop":
                    self._reply(gateway.stop(str(payload.get("reason") or "gateway stop")))
                elif self.path == "/reset":
                    self._reply(_json_request("POST", f"{gateway.board_url}/reset", payload, gateway.board_token, gateway.timeout))
                elif self.path == "/deploy/activate":
                    self._reply(gateway.activate_bundle(str(payload.get("stage_id") or "")))
                elif self.path == "/deploy/restart":
                    self._reply(gateway.restart_body())
                else:
                    self._reply({"error": "not found"}, 404)
            except PermissionError as exc:
                self._reply({"error": str(exc)}, 403)
            except ValueError as exc:
                self._reply({"error": str(exc)}, 400)
            except (HTTPError, URLError, OSError) as exc:
                self._reply({"error": str(exc)[:240]}, 503)
            except Exception as exc:
                self._reply({"error": str(exc)[:240]}, 500)

        def log_message(self, fmt: str, *args: Any) -> None:
            LOG.info("%s - %s", self.address_string(), fmt % args)

    server = ThreadingHTTPServer((host, int(port)), Handler)
    watchdog = threading.Thread(target=gateway.watchdog_loop, args=(stop_event,), daemon=True)
    watchdog.start()
    LOG.info("VENTUNO Q gateway listening on http://%s:%s -> FNK0031 at %s", host, port, gateway.board_url)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        stop_event.set()
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="VENTUNO Q gateway for FNK0031 servos")
    parser.add_argument("--host", default=os.getenv("VENTUNO_GATEWAY_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("VENTUNO_GATEWAY_PORT", "9100")))
    parser.add_argument("--board-url", default=os.getenv("FNK0031_BOARD_URL", "http://fnk0031.local:9100"))
    parser.add_argument("--board-token", default=os.getenv("FNK0031_BOARD_TOKEN", ""))
    parser.add_argument("--gateway-token", default=os.getenv("VENTUNO_GATEWAY_TOKEN", ""))
    parser.add_argument("--watchdog", type=float, default=float(os.getenv("VENTUNO_WATCHDOG_SECONDS", "2.0")))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("VENTUNO_BOARD_TIMEOUT", "3.0")))
    parser.add_argument("--enable-actuation", action="store_true", default=os.getenv("VENTUNO_ACTUATION_ENABLED", "0") == "1")
    parser.add_argument("--enable-deploy", action="store_true", default=os.getenv("VENTUNO_DEPLOY_ENABLED", "0") == "1")
    parser.add_argument("--deploy-dir", default=os.getenv("VENTUNO_DEPLOY_DIR", "/opt/pandorabox/deployments"))
    parser.add_argument("--body-service", default=os.getenv("PANDORABOX_BODY_SERVICE", "pandorabox-body"))
    parser.add_argument("--body-health-url", default=os.getenv("PANDORABOX_BODY_HEALTH_URL", "http://127.0.0.1:8766/health"))
    parser.add_argument("--restart-timeout", type=float, default=float(os.getenv("PANDORABOX_RESTART_TIMEOUT", "30")))
    args = parser.parse_args()
    logging.basicConfig(level=os.getenv("VENTUNO_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    gateway = VentunoGateway(
        args.board_url, args.board_token, args.gateway_token,
        actuation_enabled=args.enable_actuation,
        watchdog_seconds=args.watchdog,
        timeout=args.timeout,
        deploy_enabled=args.enable_deploy,
        deploy_dir=args.deploy_dir,
        body_service=args.body_service,
        body_health_url=args.body_health_url,
        restart_timeout=args.restart_timeout,
    )
    serve(gateway, args.host, args.port)


if __name__ == "__main__":
    main()
