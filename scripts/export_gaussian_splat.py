"""Run Nerfstudio's Gaussian-only exporter without requiring PyMeshLab on ARM."""
from __future__ import annotations

import sys
import types


try:
    import pymeshlab  # noqa: F401
except ModuleNotFoundError:
    # Nerfstudio imports mesh exporters eagerly, but Gaussian PLY export does
    # not call PyMeshLab. Keep those unrelated mesh operations unavailable.
    pymeshlab = types.ModuleType("pymeshlab")
    pymeshlab.Mesh = type("Mesh", (), {})
    pymeshlab.MeshSet = type("MeshSet", (), {})
    sys.modules["pymeshlab"] = pymeshlab

from nerfstudio.scripts.exporter import entrypoint


if __name__ == "__main__":
    entrypoint()
