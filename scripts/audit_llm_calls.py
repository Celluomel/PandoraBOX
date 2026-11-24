"""Run Lumina with opt-in, content-redacted LLM-call instrumentation.

This is a Phase 0 diagnostic launcher. It does not change production modules.
It records actual provider-boundary calls, opaque turn IDs, prompt sizes,
duration, visible/reasoning character counts, and provider-reported token usage.
It never records prompt or response text.
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import runpy
import sys
import threading
import time
from contextvars import ContextVar, copy_context
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = Path(os.environ.get(
    "LUMINA_LLM_AUDIT_LOG", str(ROOT / "logs" / "llm_call_audit.jsonl")
)).resolve()
_lock = threading.Lock()
_sequence: dict[str, int] = {}
_call_id = 0
_PATCHED = "__lumina_audit_wrapped__"
_executor_submission_origin: ContextVar[str] = ContextVar(
    "lumina_audit_executor_submission_origin", default="",
)


def _turn_id(kwargs: dict[str, Any]) -> str:
    candidate = str(kwargs.get("audit_turn_id") or "")
    if not candidate:
        context = sys.modules.get("core.turn_execution_context")
        var = getattr(context, "current_turn_id", None) if context else None
        try:
            candidate = str(var.get() or "") if var is not None else ""
        except Exception:
            candidate = ""
    return candidate[:120]


def _prompt_material(args: tuple[Any, ...]) -> str:
    if not args:
        return ""
    value = args[0]
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(value)


def _application_submission_site() -> str:
    """Find the Lumina caller that submitted a function to asyncio's executor."""
    frame = inspect.currentframe()
    try:
        frame = frame.f_back if frame else None
        while frame:
            module = str(frame.f_globals.get("__name__", ""))
            if not (
                module == __name__
                or module.startswith("asyncio.")
                or module == "asyncio"
                or module.startswith("concurrent.futures.")
            ):
                return f"{module}.{frame.f_code.co_name}"[:180]
            frame = frame.f_back
    finally:
        del frame
    return "unknown"


def _install_executor_provenance() -> None:
    """Preserve turn context and submission site across run_in_executor().

    asyncio.to_thread already copies ContextVars. run_in_executor does not;
    this diagnostic wrapper makes its provider calls attributable without
    changing application logic or recording prompt/response contents.
    """
    import asyncio

    loop_type = asyncio.BaseEventLoop
    original = loop_type.run_in_executor
    if getattr(original, _PATCHED, False):
        return

    def wrapped(loop, executor, function, *args):
        site = _application_submission_site()
        context = copy_context()

        def invoke():
            token = _executor_submission_origin.set(site)
            try:
                return function(*args)
            finally:
                _executor_submission_origin.reset(token)

        return original(loop, executor, context.run, invoke)

    wrapped.__name__ = original.__name__
    wrapped.__doc__ = original.__doc__
    setattr(wrapped, _PATCHED, True)
    loop_type.run_in_executor = wrapped


def _call_metadata(instance: Any, method: str, args: tuple[Any, ...], kwargs: dict[str, Any]):
    global _call_id
    inherited_turn_id = _turn_id(kwargs)
    manager = sys.modules.get("managers.llm_manager")
    role_var = getattr(manager, "current_llm_call_role", None) if manager else None
    origin_var = getattr(manager, "current_llm_call_origin", None) if manager else None
    execution_var = getattr(manager, "current_llm_call_execution_id", None) if manager else None
    cycle_var = getattr(manager, "current_llm_call_cycle_id", None) if manager else None
    operation_var = getattr(manager, "current_llm_call_operation", None) if manager else None
    try:
        call_role = str(role_var.get() or "") if role_var is not None else ""
    except Exception:
        call_role = ""
    try:
        call_origin = str(origin_var.get() or "") if origin_var is not None else ""
    except Exception:
        call_origin = ""
    try:
        cognitive_execution_id = str(execution_var.get() or "") if execution_var is not None else ""
    except Exception:
        cognitive_execution_id = ""
    try:
        cognitive_cycle_id = str(cycle_var.get() or "") if cycle_var is not None else ""
    except Exception:
        cognitive_cycle_id = ""
    try:
        cognitive_operation = str(operation_var.get() or "") if operation_var is not None else ""
    except Exception:
        cognitive_operation = ""
    dispatch_origin = str(_executor_submission_origin.get() or "")
    # A ContextVar turn ID can flow into background work. Keep it as a
    # parent reference, but only number the call as a turn call when the
    # manager explicitly marks the provider operation foreground.
    turn_id = inherited_turn_id if call_role.startswith("foreground_") else (
        "" if call_role == "background" else inherited_turn_id
    )
    with _lock:
        _call_id += 1
        call_id = _call_id
        if turn_id:
            _sequence[turn_id] = _sequence.get(turn_id, 0) + 1
        turn_call_number = _sequence.get(turn_id, 0) if turn_id else None
    caller = call_origin or "unknown"
    generic_executor_callers = {
        "concurrent.futures.thread.run",
        "asyncio.threads.to_thread",
        "unknown",
    }
    if dispatch_origin and caller in generic_executor_callers:
        caller = dispatch_origin
    caller_origin_present = bool(call_origin)
    caller_file = ""
    invocation_chain: list[str] = []
    infrastructure_modules = {
        __name__,
        "managers.llm_manager",
        type(instance).__module__,
    }
    frame = inspect.currentframe()
    try:
        frame = frame.f_back if frame else None
        while frame:
            module = str(frame.f_globals.get("__name__", ""))
            if module not in infrastructure_modules and not module.startswith("managers.llm_manager."):
                site = f"{module}.{frame.f_code.co_name}"
                if len(invocation_chain) < 4:
                    invocation_chain.append(site[:180])
                if not caller_origin_present and caller == "unknown":
                    caller = site
                caller_file = str(Path(frame.f_code.co_filename).resolve())
                try:
                    caller_file = Path(caller_file).relative_to(ROOT).as_posix()
                except ValueError:
                    caller_file = Path(caller_file).name
            frame = frame.f_back
    finally:
        del frame
    if call_origin and caller == call_origin:
        origin_module = call_origin.rsplit(".", 1)[0]
        caller_file = origin_module.replace(".", "/") + ".py"
    elif dispatch_origin and caller == dispatch_origin:
        origin_module = dispatch_origin.rsplit(".", 1)[0]
        caller_file = origin_module.replace(".", "/") + ".py"
    prompt = _prompt_material(args)
    return {
        "call_id": call_id,
        "turn_id": turn_id or None,
        "causal_parent_turn_id": (
            inherited_turn_id or None if call_role == "background" else None
        ),
        "turn_call_number": turn_call_number,
        "provider": type(instance).__name__,
        "model": str(kwargs.get("model") or getattr(instance, "model", "unknown"))[:120],
        "provider_method": method,
        "caller": caller[:180],
        "caller_file": caller_file[:120],
        "executor_submission_origin": dispatch_origin or None,
        "invocation_chain": invocation_chain,
        "execution": call_role or ("foreground_turn" if turn_id else "background_or_unattributed"),
        "cognitive_execution_id": cognitive_execution_id or None,
        "cognitive_cycle_id": cognitive_cycle_id or None,
        "cognitive_operation": cognitive_operation or None,
        "thread": threading.current_thread().name[:80],
        "prompt_chars": len(prompt),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8", errors="replace")).hexdigest(),
        "started_unix": time.time(),
    }


def _write_event(event: dict[str, Any]) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True, default=str)
        with _lock:
            with LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()
    except OSError as exc:
        print(f"[llm-audit] log write failed: {type(exc).__name__}", file=sys.stderr)


def _capture_item(event: dict[str, Any], item: Any) -> None:
    if isinstance(item, str):
        event["visible_chars"] = int(event.get("visible_chars", 0)) + len(item)
        return
    if not isinstance(item, dict):
        return
    kind = str(item.get("type") or "")
    if kind == "reasoning":
        event["reasoning_chars"] = int(event.get("reasoning_chars", 0)) + len(str(item.get("text") or ""))
    elif kind == "content":
        event["visible_chars"] = int(event.get("visible_chars", 0)) + len(str(item.get("text") or ""))
    elif kind == "finish":
        event["finish_reason"] = str(item.get("reason") or "")[:48]
    usage = item.get("usage")
    if isinstance(usage, dict):
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens"):
            value = usage.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                event[f"reported_{key}"] = value
    for key in ("reasoning_tokens", "reasoning_output_tokens"):
        value = item.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            event[f"reported_{key}"] = value


def _patch_provider_method(cls: type, method: str) -> None:
    original = cls.__dict__.get(method)
    if not callable(original) or getattr(original, _PATCHED, False):
        return
    if method == "_generate_messages_stream":
        def wrapped(self, *args, **kwargs):
            event = _call_metadata(self, method, args, kwargs)
            started = time.perf_counter()
            event["status"] = "completed"
            try:
                for item in original(self, *args, **kwargs):
                    _capture_item(event, item)
                    yield item
            except BaseException as exc:
                event["status"] = "failed"
                event["error_type"] = type(exc).__name__
                raise
            finally:
                event["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
                _write_event(event)
        wrapped.__name__ = original.__name__
        wrapped.__doc__ = original.__doc__
        setattr(wrapped, _PATCHED, True)
    else:
        def wrapped(self, *args, **kwargs):
            event = _call_metadata(self, method, args, kwargs)
            started = time.perf_counter()
            event["status"] = "completed"
            try:
                result = original(self, *args, **kwargs)
                if isinstance(result, str):
                    event["visible_chars"] = len(result)
                elif isinstance(result, dict):
                    text = result.get("text")
                    if isinstance(text, str):
                        event["visible_chars"] = len(text)
                    for key in ("completion_reason", "finish_reason", "status"):
                        if result.get(key) is not None:
                            event[key] = str(result[key])[:48]
                    for key in ("output_tokens", "reasoning_tokens", "prompt_tokens", "total_tokens"):
                        value = result.get(key)
                        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                            event[f"reported_{key}"] = value
                return result
            except BaseException as exc:
                event["status"] = "failed"
                event["error_type"] = type(exc).__name__
                raise
            finally:
                event["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
                _write_event(event)
        wrapped.__name__ = original.__name__
        wrapped.__doc__ = original.__doc__
        setattr(wrapped, _PATCHED, True)
    setattr(cls, method, wrapped)


def _install_provider_instrumentation() -> None:
    from managers.llm_manager import PROVIDER_MAP
    seen: set[type] = set()
    for cls in PROVIDER_MAP.values():
        if cls in seen:
            continue
        seen.add(cls)
        for method in (
            "_generate_messages_stream", "_generate_messages",
            "generate_background_result", "generate_with_vision",
        ):
            _patch_provider_method(cls, method)


def _run_with_module_profiler(target: Path) -> None:
    profiler_path = ROOT / "scripts" / "audit_runtime_python_execution.py"
    spec = importlib.util.spec_from_file_location("lumina_module_execution_audit", profiler_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load module execution profiler")
    profiler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profiler)
    sys.path.insert(0, str(ROOT))
    sys.argv = [str(target)]
    sys.setprofile(profiler._profile)
    threading.setprofile(profiler._profile)
    try:
        runpy.run_path(str(target), run_name="__main__")
    finally:
        sys.setprofile(None)
        threading.setprofile(None)
        profiler._write_report()


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "app.py").resolve()
    if not target.is_file() or target.suffix.lower() != ".py":
        print("Usage: audit_llm_calls.py [app.py]", file=sys.stderr)
        return 2
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("LUMINA_MODULE_EXECUTION_AUDIT", "1")
    sys.path.insert(0, str(ROOT))
    _install_executor_provenance()
    _install_provider_instrumentation()
    print(f"[audit] provider call log: {LOG_PATH}")
    _run_with_module_profiler(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
