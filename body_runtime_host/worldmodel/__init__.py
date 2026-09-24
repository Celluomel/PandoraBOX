"""The Body's embodied world model.

Principles implemented (see the architecture spec):

    * World model = representation + dynamics + imagination + counterfactual
      + causality + long-horizon stability + planning.
    * Vision is an *affordance encoder* conditioned on the body's
      capabilities — not a passive image decoder.
    * The world model is *dynamic* and in *continuous learning*.
    * Knowledge is *revised, optimized and reinforced* against new
      experience vs. the past (stability/plasticity).
    * Physical world memory: anchors of *places, objects, trajectories*.
    * The Body owns this model; the Brain only consumes its context.

Public surface:
    EmbodiedWorldModel, get_embodied_worldmodel, PhysicalMemory,
    ArtificialCortex, LatentWorldDynamics, Policy, ConsolidationEngine,
    SimulatedRoom, and the data types.
"""
from .types import (
    Action, AnchorLieu, AnchorObjet, AnchorTrajectoire, BodyState,
    Episode, GlobalState, Observation, Outcome, SceneObject,
)
from .contracts import ActionResult, BodyPlan, BodySnapshot, PlanStep
from .anchors import PhysicalMemory, atomic_write_json
from .cortex import ArtificialCortex, HashEmbedder, action_space_for_body
from .dynamics import LatentWorldDynamics, encode_action, ACTION_TYPES
from .policy import Policy
from .consolidation import ConsolidationEngine
from .sim_world import SimulatedRoom
from .sources import (
    HAFallbackSource,
    NullSource,
    RobotHttpSource,
    SimRobotSource,
    resolve_source,
)
from .core import EmbodiedWorldModel, get_embodied_worldmodel

__all__ = [
    "Action", "AnchorLieu", "AnchorObjet", "AnchorTrajectoire", "BodyState",
    "Episode", "GlobalState", "Observation", "Outcome", "SceneObject",
    "ActionResult", "BodyPlan", "BodySnapshot", "PlanStep",
    "PhysicalMemory", "atomic_write_json",
    "ArtificialCortex", "HashEmbedder", "action_space_for_body",
    "LatentWorldDynamics", "encode_action", "ACTION_TYPES",
    "Policy", "ConsolidationEngine",
    "SimulatedRoom",
    "RobotHttpSource", "SimRobotSource", "HAFallbackSource", "NullSource",
    "resolve_source",
    "EmbodiedWorldModel", "get_embodied_worldmodel",
]
