from cognition.body_runtime.runtime import BodyCommand, BodyObservation, BodyRuntime, get_body_runtime

# Embodied world model — OWNED by the Body (body_runtime_host), read by the
# Brain over the Body host's HTTP API (cognition.body_runtime.remote).
# Imported defensively: a problem in the world model must never take the
# brain down with it.
try:
    from body_runtime_host.worldmodel import (
        EmbodiedWorldModel,
        PhysicalMemory,
        ArtificialCortex,
        LatentWorldDynamics,
        Policy,
        ConsolidationEngine,
        SimulatedRoom,
        get_embodied_worldmodel,
    )
    _WORLDMODEL_OK = True
except Exception:  # pragma: no cover - defensive
    import logging
    logging.getLogger(__name__).warning(
        "body world model unavailable (import failed)", exc_info=True
    )
    _WORLDMODEL_OK = False

try:
    from .remote import RemoteWorldModel
except Exception:  # pragma: no cover - defensive
    RemoteWorldModel = None  # type: ignore
    _WORLDMODEL_OK = False

__all__ = [
    "BodyCommand", "BodyObservation", "BodyRuntime", "get_body_runtime",
    "RemoteWorldModel",
]
if _WORLDMODEL_OK:
    __all__ += [
        "EmbodiedWorldModel", "PhysicalMemory", "ArtificialCortex",
        "LatentWorldDynamics", "Policy", "ConsolidationEngine", "SimulatedRoom",
        "get_embodied_worldmodel",
    ]
