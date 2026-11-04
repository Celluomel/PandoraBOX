"""Text-only Lumina provider backed by the local Codex app-server.

The provider uses the user's existing Codex sign-in through the supported
app-server protocol. Each inference is an ephemeral, read-only thread: Lumina
continues to own conversation history, memory, tools, and body capabilities.
"""
from __future__ import annotations

import json
import logging
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import atexit
import base64
from pathlib import Path
from typing import Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class CodexAppServerProvider:
    """Run inference through a local ``codex app-server`` process."""

    def __init__(
        self,
        model: str = "gpt-6.1-sol",
        executable: str = "codex",
        timeout: float = 120.0,
        **kwargs,
    ):
        self.executable = executable or "codex"
        self.model = model
        self.extra = kwargs
        self.timeout = max(10.0, float(timeout))
        self._process: Optional[subprocess.Popen] = None
        self._events: "queue.Queue[dict]" = queue.Queue()
        self._notifications: List[dict] = []
        self._rpc_id = 0
        self._lock = threading.RLock()
        self._workdir = tempfile.mkdtemp(prefix="lumina-codex-")
        atexit.register(self.close)

    def _resolve_executable(self) -> Optional[str]:
        if os.path.isfile(self.executable):
            return os.path.abspath(self.executable)
        candidate = shutil.which(self.executable)
        if candidate:
            return candidate
        # The Windows Codex installer puts versioned binaries under this
        # stable parent; start.bat may not inherit the Codex PATH shim.
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            install_root = Path(local_app_data) / "OpenAI" / "Codex" / "bin"
            try:
                candidates = list(install_root.glob("*/codex.exe"))
                if candidates:
                    return str(max(candidates, key=lambda path: path.stat().st_mtime))
            except OSError:
                pass
        return None

    def is_available(self) -> bool:
        """Check that Codex is installed and the existing CLI session is valid."""
        executable = self._resolve_executable()
        if not executable:
            return False
        try:
            result = subprocess.run(
                [executable, "login", "status"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                check=False,
                cwd=self._workdir,
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def generate(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> str:
        messages: List[Dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self._generate_messages(messages, **kwargs)

    def generate_stream(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> Iterator[str]:
        messages: List[Dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        yield from self._generate_messages_stream(messages, **kwargs)

    def generate_with_history(
        self,
        prompt: str,
        history: List[Dict],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        messages: List[Dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return self._generate_messages(messages, **kwargs)

    def generate_with_history_stream(
        self,
        prompt: str,
        history: List[Dict],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Iterator[str]:
        try:
            from managers.settings_manager import config
            ctx_limit = max(int(getattr(config, "LLM_CTX", 4096)), 512)
        except Exception:
            ctx_limit = 4096
        budget = int((ctx_limit - 800) * 3.5)
        fixed = len(system_prompt or "") + len(prompt or "")
        trimmed = list(history)
        while trimmed and fixed + sum(len(str(m.get("content", ""))) for m in trimmed) > budget:
            trimmed = trimmed[2:]
        messages: List[Dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(trimmed)
        messages.append({"role": "user", "content": prompt})
        yield from self._generate_messages_stream(messages, **kwargs)

    def _ensure_server(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        executable = self._resolve_executable()
        if not executable:
            raise RuntimeError("Codex CLI is not installed or not on PATH")
        self._events = queue.Queue()
        self._notifications = []
        self._process = subprocess.Popen(
            [executable, "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=self._workdir,
        )
        threading.Thread(target=self._read_stdout, daemon=True, name="codex-app-server-out").start()
        threading.Thread(target=self._read_stderr, daemon=True, name="codex-app-server-err").start()
        initialized = self._rpc(
            "initialize",
            {"clientInfo": {"name": "lumina", "title": "Lumina", "version": "1.0"}},
            timeout=30.0,
        )
        if not isinstance(initialized, dict) or "error" in initialized:
            raise RuntimeError(f"Codex app-server initialization failed: {initialized}")
        self._notify("initialized", {})

    def _read_stdout(self) -> None:
        assert self._process is not None and self._process.stdout is not None
        for line in self._process.stdout:
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    self._events.put(item)
            except json.JSONDecodeError:
                logger.debug("Ignoring non-JSON Codex app-server stdout line")
        self._events.put({"_eof": True})

    def _read_stderr(self) -> None:
        assert self._process is not None and self._process.stderr is not None
        for line in self._process.stderr:
            logger.debug("Codex app-server: %s", line.rstrip())

    def _send(self, message: dict) -> None:
        if not self._process or not self._process.stdin:
            raise RuntimeError("Codex app-server is not running")
        self._process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self._process.stdin.flush()

    def _notify(self, method: str, params: dict) -> None:
        self._send({"method": method, "params": params})

    def _rpc(self, method: str, params: dict, timeout: Optional[float] = None) -> dict:
        self._rpc_id += 1
        request_id = self._rpc_id
        self._send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + (timeout or self.timeout)
        while time.monotonic() < deadline:
            try:
                message = self._events.get(timeout=max(0.05, deadline - time.monotonic()))
            except queue.Empty:
                break
            if message.get("_eof"):
                raise RuntimeError("Codex app-server exited unexpectedly")
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message.get("result", {})
            if "method" in message:
                self._notifications.append(message)
        raise TimeoutError(f"Codex app-server RPC timed out: {method}")

    @staticmethod
    def _conversation(messages: List[Dict]) -> tuple[str, str]:
        system_parts = [
            str(message.get("content", ""))
            for message in messages
            if message.get("role") == "system" and message.get("content")
        ]
        turns = [m for m in messages if m.get("role") != "system"]
        # The manager's history cap is 20 messages; retain that contract even
        # for direct/background calls that do not pass through stream trimming.
        turns = turns[-20:]
        transcript = "\n".join(
            f"<{message.get('role', 'user')}>\n{message.get('content', '')}\n</{message.get('role', 'user')}>"
            for message in turns
        )
        system = "\n\n".join(system_parts)
        system += (
            "\n\nYou are Lumina's language model. Answer the supplied conversation. "
            "Do not use tools, access files, run commands, control sensors, or claim "
            "an action occurred unless the supplied conversation provides evidence."
        )
        return system.strip(), transcript

    def _start_turn(
        self, messages: List[Dict], image_path: Optional[str] = None, **kwargs
    ) -> tuple[str, str]:
        self._ensure_server()
        system, transcript = self._conversation(messages)
        model = str(kwargs.get("model") or self.model)
        thread = self._rpc(
            "thread/start",
            {
                "model": model,
                "ephemeral": True,
                "approvalPolicy": "never",
                "sandbox": "read-only",
                "cwd": self._workdir,
                "baseInstructions": system,
            },
        )
        thread_id = thread.get("thread", {}).get("id")
        if not thread_id:
            raise RuntimeError("Codex app-server did not return a thread id")
        self._notifications.clear()
        user_input = [{"type": "text", "text": transcript}]
        if image_path:
            user_input.append({"type": "localImage", "path": image_path})
        self._rpc(
            "turn/start",
            {
                "threadId": thread_id,
                "input": user_input,
                "approvalPolicy": "never",
                "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
            },
        )
        return thread_id, model

    def _consume_turn(self, thread_id: str) -> Iterator[str]:
        deadline = time.monotonic() + self.timeout
        pending = self._notifications
        self._notifications = []
        while time.monotonic() < deadline:
            if pending:
                message = pending.pop(0)
            else:
                try:
                    message = self._events.get(timeout=max(0.05, deadline - time.monotonic()))
                except queue.Empty:
                    break
            method = message.get("method")
            params = message.get("params", {})
            if method == "item/agentMessage/delta" and params.get("threadId") == thread_id:
                delta = params.get("delta")
                if delta:
                    yield str(delta)
            elif method == "turn/completed" and params.get("threadId") == thread_id:
                turn = params.get("turn", {})
                if turn.get("status") != "completed":
                    error = turn.get("error") or turn.get("status") or "unknown failure"
                    raise RuntimeError(f"Codex turn did not complete: {error}")
                # Some app-server builds provide only the completed item, not
                # incremental deltas. Emit the final assistant message then.
                if not getattr(self, "_turn_emitted_text", False):
                    for item in turn.get("items", []):
                        if item.get("type") == "agentMessage" and item.get("text"):
                            yield str(item["text"])
                            break
                return
            elif "method" in message:
                # Retain unrelated notifications for the next RPC/turn.
                self._notifications.append(message)
        raise TimeoutError("Codex app-server response timed out")

    def _generate_messages_stream(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        with self._lock:
            try:
                self._turn_emitted_text = False
                thread_id, _ = self._start_turn(messages, **kwargs)
                for token in self._consume_turn(thread_id):
                    self._turn_emitted_text = True
                    yield token
            except Exception as exc:
                logger.exception("Codex app-server inference failed")
                yield f"Error: Codex provider unavailable: {exc}"

    def _generate_messages(self, messages: List[Dict], **kwargs) -> str:
        return "".join(self._generate_messages_stream(messages, **kwargs))

    def generate_with_vision(
        self,
        prompt: str,
        image_base64: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """Send a single image through the app-server's local-image input."""
        image_path = None
        try:
            encoded = str(image_base64 or "").strip()
            if encoded.startswith("data:"):
                encoded = encoded.split(",", 1)[-1]
            payload = base64.b64decode(encoded, validate=False)
            extension = ".png" if payload.startswith(b"\x89PNG\r\n\x1a\n") else ".jpg"
            fd, image_path = tempfile.mkstemp(prefix="lumina-vision-", suffix=extension, dir=self._workdir)
            with os.fdopen(fd, "wb") as image_file:
                image_file.write(payload)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            tokens = []
            with self._lock:
                self._turn_emitted_text = False
                thread_id, selected_model = self._start_turn(
                    messages, image_path=image_path, model=model, **kwargs
                )
                for token in self._consume_turn(thread_id):
                    tokens.append(token)
            text = "".join(tokens).strip()
            return {
                "text": text,
                "model": selected_model,
                "success": bool(text) and not text.startswith("Error:"),
            }
        except Exception as exc:
            logger.exception("Codex app-server vision inference failed")
            return {"text": f"Error: Codex vision provider unavailable: {exc}", "success": False}
        finally:
            if image_path:
                try:
                    os.remove(image_path)
                except OSError:
                    pass

    def close(self) -> None:
        with self._lock:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            self._process = None
            shutil.rmtree(self._workdir, ignore_errors=True)
