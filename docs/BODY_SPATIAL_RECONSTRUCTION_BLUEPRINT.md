# Body Spatial Reconstruction Blueprint

Status: in progress (software groundwork; no physical sensors available yet)
Owner: Body Runtime
Related contracts: `body_perception_frame.v2`, Body world model, Body sensor plugins
Primary visualization target: Body UI and Meta Quest 3S

Implementation note: `MetricVoxelMap` provides a sparse metric endpoint
accumulator with deterministic tests. Runtime integrates only LiDAR frames
whose adapter explicitly marks them `native: true`; the persisted map is
inspectable at `/worldmodel/spatial-map`, remains outside the planner, and does
not infer free space. Real-sensor calibration and hardware validation remain
outstanding.

The VLM semantic path now emits normalized image regions, open-vocabulary
scalar attributes and observed-object relations into `body_semantic_splats.v1`
at `/worldmodel/semantic-splats`. Quest renders these only for accepted
semantics aligned to the current observation, as a deterministic soft-point
preview. With the simulator this is explicitly a preview, not camera-derived
Gaussian Splatting or real-world reconstruction. A real Gaussian backend
still needs camera keyframes, calibrated poses and captured appearance
primitives.

## 1. Objective

Replace the hand-authored/simulated 3D scene progressively with a persistent,
spatially grounded representation built from the robot's camera, LiDAR/depth,
pose and other available sensors. The representation must support both:

- reliable metric reasoning for navigation, clearance and object coordinates;
- a useful visual reconstruction for inspection and VR.

The result is a VLM-conditioned hybrid reconstruction. Camera images and poses
provide the appearance and multi-view evidence for Gaussian Splatting (3DGS);
the VLM output is an explicit input to semantic grouping and rendering. Metric
geometry and tracked entities remain the source of truth for Body reasoning.
The splat scene is a visual reconstruction, not a collision map, localization
authority or substitute for missing sensor evidence.

## 2. Architectural decision

Maintain four related but distinct products:

1. **Metric safety map**: free/occupied/unknown space, distances, geometry,
   confidence and freshness. Built from calibrated range/depth data and pose.
2. **Semantic scene**: open-vocabulary entities and descriptions from the VLM,
   grounded to image regions and metric sensor evidence. Preserve unmatched and
   uncertain observations instead of forcing a label.
3. **Dynamic tracks**: moving entities with timestamped position, velocity,
   uncertainty and track age. Do not bake moving objects into a static map.
4. **VLM-conditioned splat scene**: camera-derived Gaussian appearance with
   VLM-grounded object identities, open-vocabulary labels, descriptions,
   relations and confidence attached to the relevant splats/groups. These
   semantics drive selectable render layers, highlights and annotations.

The VLM output is not merely shown beside the scene: it feeds the splat
association/metadata layer and controls semantic rendering (entity grouping,
labels, category filters, confidence/uncertainty overlays and relations).
Camera pixels and calibrated multi-view poses supply observed appearance; the
VLM does not repaint pixels from its prose. It cannot invent metric coordinates,
declare space free, erase a LiDAR obstacle, or authorize motion. When modalities
disagree, retain the conflict and uncertainty; the conservative metric safety
layer wins for actuation.

## 3. System flow

```text
Camera ───────────────┐
LiDAR / depth ────────┤
IMU + odometry + pose ├─> body_perception_frame.v2
Calibration ──────────┘          │
                                 ├─> synchronization and quality gate
                                 ├─> metric geometry + localization
                                 ├─> VLM image interpretation
                                 ├─> vision/range association + tracks
                                 ├─> Body metric/semantic spatial map
                                 │       └─> safety planner (metric only)
                                 └─> camera + pose -> Gaussian reconstruction
                                          + grounded VLM labels/groups/relations
                                          -> semantic splat renderer -> VR
```

Keep the pipeline Body-owned and usable without Brain connectivity. The frame
contract in `body_runtime_host/worldmodel/perception.py` is the integration
boundary; evolve it compatibly rather than creating a parallel sensor packet.
Every derived map item must retain source frame IDs and provenance back to the
observations that produced it.

## 4. Staged implementation

### Stage 0 - Inventory and evidence baseline

Record what is real, simulated, replayed or unavailable for each modality.
Inventory camera intrinsics, LiDAR/depth format and frame, IMU/odometry source,
timestamp behavior, current calibration UI, and existing map/rendering paths.
Use explicit provenance labels; replay-derived or synthetic range data must
never be reported as a physical LiDAR measurement.

**Exit gate:** a repeatable capture/replay fixture yields a `v2` frame, and a
report clearly distinguishes real, derived, simulated and missing inputs.

### Stage 1 - Synchronization and calibration quality

Define and validate camera intrinsics, camera-to-body transform, range-sensor-
to-body transform, units, handedness, axis convention, frame IDs and timestamps.
Measure synchronization skew and calibration residuals. Reject or downgrade
frames that exceed configured quality limits; preserve their raw data for
diagnosis. Do not silently replace missing timestamps with evidence of perfect
synchronization.

**Exit gate:** repeatable calibration capture; documented coordinate frames;
measured time skew and projection residuals within declared tolerances.

### Stage 2 - Metric local geometry

Build a local metric representation from actual range/depth observations and
Body pose. Start with the simplest inspectable representation already suitable
for the planner (point cloud plus local occupancy/voxel or equivalent); choose
TSDF/surfel details only after measured needs justify them. Encode three states:
free, occupied and unknown. Expand occupied geometry by the robot footprint,
pose uncertainty and a configurable safety margin before route validation.

**Exit gate:** known obstacle distances agree with measured range within the
sensor's declared uncertainty; unknown space is never treated as free; the
planner rejects routes that violate clearance.

### Stage 3 - VLM semantics grounded to geometry

Run the VLM on selected camera frames, preferably keyframes or regions of
interest when this reduces latency without losing relevant context. Request
open-vocabulary descriptions, visible evidence, image region/bounds, entity
attributes/relations and uncertainty. Project image regions into range data
using calibration, then associate by spatial overlap, distance, category
compatibility and temporal consistency. Keep VLM-only candidates as ungrounded
hypotheses, not map facts.

The normalized VLM result becomes a versioned semantic annotation input to the
renderer: stable entity ID, label/description, 2D region, grounded 3D extent or
anchor when available, relation links, confidence, source frame IDs and
validity interval. The association stage maps those image regions through
calibrated camera poses to the Gaussian primitives/groups visible in those
views. Across keyframes, merge labels onto a stable semantic entity/group only
when geometric and temporal evidence agree. Keep the original VLM response
alongside the normalized annotation for audit.

Do not use a fixed object dictionary as the ontology. Normalize categories for
matching while preserving the model's original label and description. Log
accepted, rejected and ambiguous associations with reasons.

**Exit gate:** a blind, labeled set measures object precision/recall,
association precision, invented-object rate and stability across viewpoints;
all accepted metric positions cite range/depth evidence.

#### Runtime attention and timing

Keep two loops independent. The fast loop consumes current range, pose and
velocity for collision checks, route validation and safe stops. The slower
Body VLM adds open-vocabulary labels to tracked sensor entities; its prose
cannot authorize motion or create free space. A camera frame and radar scan
may be combined only when calibration and timestamps agree. Radar projects an
attention region into the camera image, but never supplies an object identity.

The current attention input is one 640x240 image: a scene overview and one
radar-selected detail. A rejected grounding triggers one full-frame retry.
Without synchronized radar evidence, the Body uses the full frame directly.
The Body VLM setting can disable radar focus. Background calls are paced by
measured provider latency to avoid saturating the Ventuno NPU while the fast
sensor loop continues.

On 2026-10-05, a three-scene simulated A/B test on Ventuno Q with
Qwen3-VL-4B-Instruct W4A16 measured 12.44 s per attention call versus 41.20 s
per full-frame call. Attention grounded the task target in 3/3 scenes and
completed 3/3 simulated routes with zero collisions or near misses. This is
evidence for the input format, not a real-sensor or physical autonomy result.
Before relying on it for a mounted robot, repeat with calibrated camera/radar
timestamps, moving objects, occlusion, varied goals and viewpoints, and report
both worst-case latency and safe-stop behavior. A 4x4 or 8x8 image grid is not
part of the runtime path because every additional region costs vision tokens.

### Stage 4 - Persistent map and dynamics

Accumulate geometry and static semantic entities across robot motion using the
localization estimate. Give map anchors and entities stable IDs, coordinate
frame, first/last-seen timestamps, uncertainty, confidence, provenance and
update history. Keep moving objects in a tracking layer with relative velocity;
expire or mark stale evidence rather than leaving ghost obstacles indefinitely.
Support map reset, export/import and replay without mixing sessions silently.

**Exit gate:** repeatable revisits align within a measured drift budget;
moving objects do not become persistent static geometry; stale or conflicting
observations remain visible as such.

### Stage 5 - Visual reconstruction and Gaussian Splatting evaluation

First produce a calibrated keyframe/depth replay and compare it with the metric
map. Then evaluate offline 3DGS on a short, static, calibrated sequence with
known camera poses. Feed the grounded VLM annotations from those keyframes into
the reconstruction pipeline to create semantic splat groups, not just a
separate text panel. The renderer must support per-entity labels/highlights,
category visibility, relationship/context overlays, confidence visualization
and selection that resolves back to the Body entity ID. Compare novel views
against held-out camera frames and range data. Track reconstruction quality,
scale/alignment drift, semantic-to-splat assignment precision, holes/floaters,
processing time, memory, storage and thermal/compute cost.

Photometric splat attributes (observed color/appearance) come from camera
captures. VLM descriptions may label or guide grouping and may drive a clearly
marked semantic overlay; they must not silently synthesize unseen surfaces or
replace calibrated depth/pose. If a VLM hypothesis has no geometric support,
show it as a non-occluding uncertain annotation rather than adding fabricated
Gaussians to the reconstructed scene.

Only pursue online/incremental splat updates after offline results demonstrate
value. Dynamic objects should be masked, independently represented or rebuilt
with an explicitly dynamic method; a static splat must not accumulate trails.
Keep the splat renderer isolated from safety-critical map generation and
planning. Test rendering/inference support on the intended device rather than
assuming that an available AI NPU accelerates 3DGS training or rendering.

**Exit gate:** reproducible offline reconstruction, metric alignment against
range data, acceptable held-out-view quality, and a measured resource budget.
If these do not beat a simpler textured mesh/point-cloud view for the intended
VR use, retain the simpler renderer.

### Stage 6 - Live visualization and VR integration

Expose distinct controls/layers for camera, metric geometry, semantic splats,
uncertainty, dynamic tracks and the photometric splat view. Selecting a splat
group must resolve to its grounded Body entity and evidence; selecting a VLM
entity should highlight its associated splats and show unmatched/uncertain
status where grounding is incomplete. Show map frame, age, source and quality
status. Make the VR reconstruction inspectable while keeping metric sensor
views available; visual quality must not conceal stale or missing evidence.
Provide an explicit fallback to 2D/point-cloud views.

**Exit gate:** stable rendering while Body updates; no loss of UI controls;
users can distinguish measured geometry, VLM-grounded semantic splats,
unmatched hypotheses and camera-derived appearance at a glance; semantic
selection/visibility controls act on the correct stable entity groups.

### Stage 7 - Physical acceptance

After the robot is assembled and sensors are mounted, repeat calibration and
mapping tests at low speed in a controlled environment. Start with mapping and
visualization only. Enable planner consumption only after clearance, drift,
latency and stale-data behavior pass their gates. Actuation remains subject to
the Body's existing authorization, stop and safety constraints.

**Exit gate:** signed-off sensor calibration, localization/map quality report,
zero safety-map false-free cases in the acceptance set, functioning emergency
stop, and a documented rollback to the existing planner/view.

## 5. Measurements and evidence

Every experiment records hardware/software versions, map/session ID, sensor
provenance, calibration ID, frame count and test conditions. Report at least:

- camera/range/pose timestamp skew and dropped-frame rate;
- calibration reprojection and range-alignment residuals;
- localization drift (position and heading) over distance and loop closure;
- obstacle-distance error, unknown-space rate and false-free rate;
- VLM object precision/recall, hallucination rate and vision/range association
  precision, including per-scene minimum and viewpoint stability;
- dynamic track position/velocity error and stale-track/ghost rate;
- end-to-end capture-to-map latency, update rate, CPU/GPU/NPU use, memory,
  storage and temperature;
- 3DGS held-out-view quality and alignment, reported separately from mapping
  and safety metrics;
- planner clearance violations and near misses, using metric geometry only.

Do not summarize success using a single image-quality score or a single
benchmark success rate. Keep per-scene failures and raw replay artifacts.

## 6. Safety and degraded modes

- No valid pose or calibration: do not merge into the persistent map.
- Excess synchronization skew: mark frame unsynchronized and do not fuse it as
  simultaneous evidence.
- Range sensor unavailable: mark geometry degraded; do not infer free space
  from the VLM or a Gaussian Splat.
- VLM unavailable or malformed: retain metric geometry and continue only with
  capabilities allowed by the existing planner.
- Sensor disagreement: preserve both observations and uncertainty; safety uses
  the more conservative obstacle interpretation.
- Stale map or track: expire/downgrade it and require fresh local sensing before
  motion through the affected region.
- Reconstruction/rendering overload: drop visual updates before sensor
  acquisition, mapping or stop handling.

## 7. Immediate next step

Complete **Stage 0 with a read-only audit and deterministic replay report**:
list each current camera, LiDAR/depth, pose and calibration input with its real
provenance; serialize representative `body_perception_frame.v2` samples; and
identify schema gaps without changing the planner. This establishes whether the
next engineering task is calibration, timestamp quality, real range capture or
map accumulation, based on evidence rather than the simulated scene.

## 8. References

- Kerbl et al., [3D Gaussian Splatting for Real-Time Radiance Field
  Rendering](https://doi.org/10.1145/3592433), ACM TOG 2023.
- Keetha et al., [SplaTAM: Splat, Track & Map 3D Gaussians for Dense RGB-D
  SLAM](https://openaccess.thecvf.com/content/CVPR2024/papers/Keetha_SplaTAM_Splat_Track__Map_3D_Gaussians_for_Dense_RGB-D_SLAM_CVPR_2024_paper.pdf), CVPR 2024.
- [Gaussian-LIC2: Precise LiDAR-Inertial-Camera Odometry and Mapping Using
  3D Gaussian Splatting](https://doi.org/10.48550/arXiv.2507.04004), 2025.
- Li et al., [4D Gaussian Splatting SLAM](https://openaccess.thecvf.com/content/ICCV2025/html/Li_4D_Gaussian_Splatting_SLAM_ICCV_2025_paper.html), ICCV 2025.
