"""Build a sanitized, reproducible Body Runtime deployment bundle."""
from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable

SECRET_KEYS = ("TOKEN", "SECRET", "PASSWORD", "API_KEY")
EXCLUDED_PARTS = {".git", ".venv", "venv", "body_venv", "__pycache__", ".pytest_cache"}


def _safe_config(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        return {key: value for key, value in payload.items() if not any(secret in str(key).upper() for secret in SECRET_KEYS)}
    except Exception:
        return {}


def _files(root: Path) -> Iterable[tuple[Path, str]]:
    roots = [
        (root / "body_runtime_host", "body_runtime_host"),
        (root / "body_requirements.txt", "body_requirements.txt"),
        (root / "start_body.sh", "start_body.sh"),
        (root / "start_body.bat", "start_body.bat"),
        (root / "start_ventuno_gateway.sh", "start_ventuno_gateway.sh"),
        (root / "start_ventuno_gateway.bat", "start_ventuno_gateway.bat"),
        (root / "docs" / "FNK0050_PLUGIN.md", "docs/FNK0050_PLUGIN.md"),
    ]
    for path, archive_name in roots:
        if path.is_file():
            yield path, archive_name
        elif path.is_dir():
            for item in path.rglob("*"):
                if not item.is_file() or any(part in EXCLUDED_PARTS for part in item.parts):
                    continue
                yield item, str(Path(archive_name) / item.relative_to(path))


def build_bundle(root: str | Path, include_learned_model: bool = False) -> tuple[bytes, Dict[str, Any]]:
    root = Path(root).resolve()
    manifest: Dict[str, Any] = {
        "contract": "pandorabox.body_bundle.v1",
        "created_at": time.time(),
        "secrets_included": False,
        "learned_model_included": bool(include_learned_model),
        "files": [],
        "config": _safe_config(root / "data" / "body" / "config.json"),
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, archive_name in _files(root):
            archive.write(path, archive_name)
            manifest["files"].append(archive_name)
        # The target receives a portable configuration, never the source
        # machine's credentials. Secret-bearing values are represented by the
        # existing @env references or omitted by _safe_config().
        archive.writestr(
            "data/body/config.json",
            json.dumps(manifest["config"], indent=2, ensure_ascii=False),
        )
        manifest["files"].append("data/body/config.json")
        if include_learned_model:
            model_root = root / "data" / "body" / "worldmodel"
            if model_root.exists():
                for item in model_root.rglob("*"):
                    if item.is_file() and item.suffix in {".pt", ".npz", ".json"}:
                        name = str(Path("data/body/worldmodel") / item.relative_to(model_root))
                        archive.write(item, name)
                        manifest["files"].append(name)
        archive.writestr("BODY_BUNDLE_MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    return output.getvalue(), manifest
