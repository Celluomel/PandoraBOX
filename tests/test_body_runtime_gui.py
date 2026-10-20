import unittest
import json
import gzip
import tempfile
import threading
from pathlib import Path


class BodyRuntimeGuiTests(unittest.TestCase):
    def test_sensor_camera_refresh_initializes_empty_element_before_access(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "world_map_3d.js").read_text(encoding="utf-8")
        refresh = source.split("async function refreshSensors() {", 1)[1].split("\nasync function sensorJson", 1)[0]

        self.assertLess(refresh.index("const cameraEmpty = byId('world-map-camera-empty')"),
                        refresh.index("if (cameraEmpty &&"))

    def test_sensor_summary_counts_only_connected_physical_sources(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "world_map_3d.js").read_text(encoding="utf-8")

        self.assertIn("const physicalSources = ['camera', 'radar', 'gps', 'imu', 'tof', 'ultrasonic']", source)

    def test_battery_level_input_changes_action_button_label(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "world_map_3d.js").read_text(encoding="utf-8")

        self.assertIn("batteryLevelInput.value.trim() ? 'Set battery level' : 'Battery full'", source)

    def test_calibration_midas_snapshots_are_sparse_but_keep_per_frame_metadata(self):
        from body_runtime_host.runtime import _calibration_midas_record

        frame = {"frame_id": "depth-1", "captured_at": 10.0, "depth_width": 640,
                 "depth_raw_png_base64": "YWJjZA=="}
        first, last_snapshot = _calibration_midas_record(frame, 10.0, 0.0)
        later, _ = _calibration_midas_record({**frame, "frame_id": "depth-2"}, 12.0, last_snapshot)

        self.assertEqual(first["depth_raw_png_base64"], "YWJjZA==")
        self.assertTrue(first["depth_snapshot"])
        self.assertEqual(later["depth_raw_png_bytes_omitted"], 6)
        self.assertNotIn("depth_raw_png_base64", later)
        self.assertEqual(later["frame_id"], "depth-2")

    def test_new_calibration_session_archives_previous_plain_log_and_starts_fresh(self):
        from body_runtime_host.runtime import BodyHost

        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            host = object.__new__(BodyHost)
            host._midas_calibration_log_path = Path(directory) / "midas_calibration_trace.log"
            host._midas_calibration_log_lock = threading.Lock()
            host._midas_calibration_active_session_id = None
            host.append_midas_calibration_trace({"records": [
                {"type": "session_start", "session_id": "first"},
                {"type": "session_end", "session_id": "first"},
            ]})
            host.append_midas_calibration_trace({"records": [
                {"type": "session_start", "session_id": "second"},
            ]})

            current = [json.loads(line) for line in host._midas_calibration_log_path.read_text().splitlines()]
            archives = list((Path(directory) / "midas_calibration_archives").glob("*.log.gz"))
            with gzip.open(archives[0], "rt", encoding="utf-8") as stream:
                archived = [json.loads(line) for line in stream]
            self.assertEqual([row["session_id"] for row in current], ["second"])
            self.assertEqual([row["session_id"] for row in archived], ["first", "first"])

    def test_midas_calibration_trace_appends_structured_log_records(self):
        from body_runtime_host.runtime import BodyHost

        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            host = object.__new__(BodyHost)
            host._midas_calibration_log_path = Path(directory) / "midas_calibration_trace.log"
            host._midas_calibration_log_lock = threading.Lock()
            result = host.append_midas_calibration_trace({"records": [
                {"type": "session_start", "session_id": "test"},
                {"type": "session_end", "accepted_anchors": 0},
            ]})

            lines = host._midas_calibration_log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(result["records_written"], 2)
            self.assertEqual([json.loads(line)["type"] for line in lines], ["session_start", "session_end"])
            self.assertEqual(
                host.read_midas_calibration_trace(),
                host._midas_calibration_log_path.read_bytes(),
            )

    def test_midas_calibration_trace_rejects_unbounded_record_count(self):
        from body_runtime_host.runtime import BodyHost

        host = object.__new__(BodyHost)
        with self.assertRaisesRegex(ValueError, "5000 records"):
            host.append_midas_calibration_trace({"records": [{}] * 5001})

    def test_depth_frame_camera_pixels_fall_back_to_midas_source_frame(self):
        from types import SimpleNamespace
        from body_runtime_host.runtime import BodyHost

        host = object.__new__(BodyHost)
        host._yolox_service = SimpleNamespace(analyzed_frame=lambda frame_id: None)
        source_frame = {"frame_id": "depth-1", "image_base64": "paired-image"}
        host._midas_service = SimpleNamespace(analyzed_frame=lambda frame_id: source_frame)

        self.assertEqual(
            host.camera_yolo_frame("depth-1"),
            {"available": True, "camera": {**source_frame, "camera_height_m": 0.18}},
        )

    def test_depth_response_avoids_retransmitting_unchanged_frame_and_optional_blobs(self):
        from types import SimpleNamespace
        from body_runtime_host.runtime import BodyHost

        payload = {
            "frame_id": "depth-1", "state": "ready", "depth_jpeg_base64": "color",
            "depth_gray_jpeg_base64": "gray", "depth_raw_png_base64": "raw",
        }
        host = object.__new__(BodyHost)
        host._midas_service = SimpleNamespace(status=lambda: dict(payload), request_raw_output=lambda: None)
        host._power_mode = SimpleNamespace(status=lambda: {"mode": "DEV"})
        host._camera_height_m = lambda: 0.18
        host.value = lambda _key, default=None: default

        unchanged = host.camera_depth(since_frame_id="depth-1")
        shape_only = host.camera_depth(include_raw=False, include_color=False)

        self.assertTrue(unchanged["unchanged"])
        self.assertNotIn("depth_raw_png_base64", unchanged)
        self.assertNotIn("depth_jpeg_base64", unchanged)
        self.assertEqual(shape_only["depth_gray_jpeg_base64"], "gray")
        self.assertNotIn("depth_raw_png_base64", shape_only)
        self.assertNotIn("depth_jpeg_base64", shape_only)

        calibration = host.camera_depth(include_raw=True)
        self.assertIn("depth_raw_png_base64", calibration)

    def test_world_map_switches_between_simulation_and_sensor_only_renderings(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        source = (root / "body_runtime_host" / "world_map_3d.js").read_text(encoding="utf-8")
        self.assertIn('src="/world-map-3d.js"', BODY_GUI_HTML)
        self.assertIn("['simulation','Simulation']", (root / "body_runtime_host" / "body_gui.py").read_text(encoding="utf-8"))
        self.assertIn("['sensors','Live sensors']", (root / "body_runtime_host" / "body_gui.py").read_text(encoding="utf-8"))
        self.assertIn("window.bodyWorldModelView=active", (root / "body_runtime_host" / "body_gui.py").read_text(encoding="utf-8"))
        self.assertIn("body-worldmodel-viewchange", source)
        self.assertIn('data-render="2d"', source)
        self.assertIn('data-render="3d"', source)
        self.assertIn(".map-layout>.map-wrap[hidden]", source)
        self.assertIn("sim?.resize(); buildSimulation(latestWorld); sim?.render()", source)
        self.assertIn("depth_gray_jpeg_base64", source)
        self.assertIn("no simulation object positions", source)
        self.assertIn("performance.now() - lastSensorDepthAt < 100", source)
        self.assertIn("since_frame_id", source)
        self.assertIn("age > 2.5", source)
        self.assertIn("yolo.paired === false", source)
        self.assertIn("const yoloOverlayCoastSeconds = 5", source)
        self.assertIn("const yoloOverlayStaleLabelSeconds = 1.5", source)
        self.assertIn("now - track.lastSeenAt <= yoloOverlayCoastSeconds", source)
        self.assertIn("LAST SEEN", source)
        self.assertIn("nearest_detection_result(camera_at, max_delta_s=0.35)", (root / "body_runtime_host/runtime.py").read_text(encoding="utf-8"))
        self.assertNotIn("boxIou(previous.bbox", source)
        self.assertIn("currentCamera.image_base64", source)
        self.assertIn("/plugins/mmwave_radar/status", source)
        self.assertIn("/plugins/gps/status", source)
        self.assertIn("/plugins/imu/status", source)
        self.assertIn("/plugins/imu/status?history=0", source)
        self.assertIn("void refreshLiveImu();\n}, 250)", source)
        self.assertIn("activePowerMode === 'ATTENTIVE' ? 1000 : 400", source)
        self.assertIn("void refreshLiveUltrasonic();", source)
        self.assertIn("/plugins/tof/status", source)
        self.assertIn("world-map-gps-signals", source)
        self.assertIn("world-map-gps-map-card", source)
        self.assertIn("data-gps-map-mode=\"satellite\"", source)
        self.assertIn("tile.openstreetmap.org/{z}/{x}/{y}.png", source)
        self.assertIn("World_Imagery/MapServer/tile/{z}/{y}/{x}", source)
        self.assertIn("function updateGpsMap()", source)
        self.assertIn("Center GPS", source)
        self.assertIn("No physical LiDAR stream is connected", source)
        self.assertIn("/plugins/ultrasonic/status", source)
        self.assertIn("refreshLiveUltrasonic", source)
        self.assertIn("void refreshLiveRadar()", source)
        self.assertIn("async function refreshSensorDepth()", source)
        self.assertIn("sensorDepthBusy", source)
        self.assertIn("depthStatus.device", source)
        self.assertIn("s old", source)
        self.assertIn("activeRender === '3d'", source)
        self.assertIn("function drawDepthDetections(image, yolo, calibration = metricDepthCalibration)", source)
        self.assertIn("setCloudLayerLabels('detections', htmlLabels)", source)
        self.assertIn("data-cloud-layer=\"detections\" checked", source)
        self.assertIn("function cameraPoint(u, v, z, intrinsics)", source)
        self.assertIn("low_body_front: { heightM: 0.12 }", source)
        self.assertIn("const elevationDeg = Number.isFinite(reportedPitch) ? reportedPitch : 0", source)
        self.assertIn("new THREE.ArrowHelper(direction, new THREE.Vector3(), 0.2, color, 0.045, 0.028)", source)
        self.assertIn("world-map-cloud-radar-dot", source)
        self.assertIn("labels.push({ position: point, marker: true", source)
        self.assertIn("BODY SENSOR ORIGIN · ${mount.heightM.toFixed(2)} m above floor", source)
        self.assertIn("CAMERA MOUNT · ${mount.profile.replace(/_/g, ' ')}", source)
        self.assertLess(source.index("const cameraMountProfiles ="), source.index("updateCloudOrigin();"))
        self.assertIn("cloud.camera.up.set(0, 1, 0).applyQuaternion(cameraRotation)", source)
        self.assertIn("cameraPointInBodyFrame(cameraPoint(x, y, distance, intrinsics)", source)
        self.assertIn("Number(depth.captured_at) || latestDepthCapturedAt", source)
        self.assertIn("positions.push(index, 0, 1, index, 0, -15", source)
        self.assertIn("cameraPoint(x, y, distance, intrinsics)", source)
        self.assertIn("function applyCameraProjection()", source)
        self.assertIn("data-cloud-view=\"camera\"", source)
        self.assertIn("async function cameraFrameForDepth(depth)", source)
        self.assertNotIn("yoloForDepthFrame", source)
        depth_cloud = source.split("async function rebuildDepthCloud(", 1)[1].split("async function refreshSensorDepth(", 1)[0]
        self.assertNotIn("/body/camera/yolo/status", depth_cloud)
        self.assertIn("cloudPoints.geometry = geometry", depth_cloud)
        self.assertIn("previousGeometry.dispose()", depth_cloud)
        self.assertIn("requestAnimationFrame(animateSensorCloud)", source)
        self.assertIn("if (activeRender === '3d' && cloudDepthImage) drawDepthDetections(cloudDepthImage, cloudDepthYolo)", source)
        self.assertNotIn("cloudFrameId = String(depth.frame_id || '')", depth_cloud.split("const image = await loadDepthFrame(depth)", 1)[1].split("const intrinsics = cameraIntrinsicsForImage(image)", 1)[0])
        self.assertIn("cloud.render();\n  cloudFrameId = String(depth.frame_id || '')", depth_cloud)
        self.assertNotIn("await yoloResultForDepth(depth)", depth_cloud)
        self.assertIn("void yoloResultForDepth(depth).then(frameYolo =>", depth_cloud)
        self.assertIn("cloudDepthYolo = alignedYolo", depth_cloud)
        self.assertIn("async function yoloResultForDepth(depth)", source)
        self.assertIn("const frameMatches = Boolean(image.frameId && yolo?.frame_id === image.frameId)", source)
        self.assertIn("yoloFrameDelta <= maxSceneDetectionPairDeltaSeconds", source)
        self.assertIn("const maxSceneDetectionPairDeltaSeconds = 0.5", source)
        self.assertIn("'depth unpaired · relative shape only'", source)
        self.assertIn("MiDaS stale ${depthAge.toFixed(1)} s", source)
        self.assertIn("YOLOX Δ${yoloFrameDelta.toFixed(1)} s", source)
        self.assertIn("async function decodeGray16Png(base64)", source)
        self.assertIn("image.normalizedDepth?.[index]", source)
        self.assertIn("if (cloudViewport?.classList.contains('is-camera-view'))", depth_cloud)
        self.assertIn("cameraFrameForDepth(depth).then(frame =>", depth_cloud)
        self.assertNotIn("cameraFrameForDepth(depth)", depth_cloud.split("if (cloudViewport?.classList.contains('is-camera-view'))", 1)[0])
        self.assertIn("function pairedYoloDetections(yolo)", source)
        self.assertIn("yolo?.paired !== false ? pairedYoloDetections(yolo) : []", source)
        self.assertIn("const medianRange = frameMatches && metricFrame", source)
        self.assertNotIn("relativeDepthPercentiles(image)", source)
        self.assertIn("attitudeQuaternion(timestamp)", source)
        self.assertIn("function bodyPointToScene(point, timestamp = latestDepthCapturedAt)", source)
        self.assertIn("cloudOriginGroup.quaternion.copy(attitude || new THREE.Quaternion())", source)
        self.assertIn("bodyPointToScene(new THREE.Vector3(lateral, 0, -forward), sample.timestamp)", source)
        self.assertIn("replaceChildren('Z− · forward')", source)
        self.assertIn("if (scale) scale.hidden = true", source)
        self.assertIn("Pseudo-metres · uncalibrated; shape only, not range · ${fovText}", source)
        self.assertIn("function detectionDepthStats(image, bbox, calibration, identity)", source)
        self.assertIn("return { near: quantile(0.1), median: quantile(0.5), far: quantile(0.9), screen: true }", source)
        self.assertIn("stats.screen ? Math.min(observedSpan, metricFrame ? 0.04 : 0.02)", source)
        self.assertIn("world-map-cloud-hud-sync", source)
        self.assertNotIn("distance * 1.28", source)
        self.assertNotIn("distance * 0.96", source)
        self.assertIn("function updateCloudRadar(sample = latestRadarSample, force = false)", source)
        self.assertIn("depthTest: false, depthWrite: false", source)
        self.assertIn("marker.renderOrder = 21", source)
        self.assertIn("new THREE.SphereGeometry(0.055, 16, 12)", source)
        self.assertIn("function updateCloudLabelPositions()", source)
        self.assertIn("ResizeObserver(resize)", source)
        self.assertIn("data-cloud-layer=\"radar\"", source)
        self.assertIn("data-cloud-layer=\"radar\" checked", source)
        self.assertIn("let cloudRadarRenderKey = ''", source)
        radar_refresh = source.split("async function refreshLiveRadar()", 1)[1].split("async function refreshLiveGps()", 1)[0]
        self.assertNotIn("drawDepthDetections", radar_refresh)
        self.assertIn("3D ${Math.round(cloudFpsFrames * 1000 / elapsed)} FPS", source)
        self.assertIn("void refreshLiveRadar();\n}, 400);", source)
        self.assertIn("cloudGuides.visible = !cloudViewport?.classList.contains('is-camera-view')", source)
        self.assertIn("data-cloud-view=\"follow\"", source)
        self.assertIn("world-map-cloud-hud-fps", source)
        self.assertIn("world-map-cloud-depth-caption", source)
        self.assertIn("clamp(420px,60vh,720px)", source)
        self.assertIn("grid-template-columns:minmax(0,1fr) 320px", source)
        self.assertIn("#426078", source)
        self.assertNotIn("colorsArray", depth_cloud)
        self.assertNotIn("setAttribute('color'", depth_cloud)
        self.assertNotIn("loadGrayDepth", depth_cloud)
        self.assertNotIn("loadClassMask", depth_cloud)
        self.assertIn("function createMidasPointMaterial(pointSize)", source)
        self.assertIn("geometry.setAttribute('depthValue'", depth_cloud)
        self.assertIn("vec3 color = turbo(clamp(vDepth, 0.0, 1.0))", source)
        self.assertNotIn("uniform float uStale", source)
        self.assertIn("drawDepthDetections(cloudDepthImage, cloudDepthYolo)", source)
        self.assertIn("uPointSize * uViewportHeight", source)
        self.assertIn("#f05a28,#f9c932,#72d055,#1fa4b2,#4663d8,#30123b", source)
        self.assertNotIn("pairedFramePromise.then(async frame =>", depth_cloud)
        self.assertIn("function semanticColor(classId)", source)
        self.assertIn("[0, '#ef8354']", source)
        self.assertIn("[89, '#3a86ff']", source)
        self.assertIn("[130, '#c77dff']", source)
        self.assertIn("[22, '#e76f51']", source)
        self.assertIn("const classId = sourcePixels[index]", source)
        self.assertIn("color:#40574a;font:11px ui-monospace,monospace", source)
        self.assertIn("color:#b4c9bc;font:10px ui-monospace,monospace", source)
        self.assertIn("function segmentationMatchesDepth(segmentation, depth)", source)
        self.assertIn("Math.abs(segmentationTime - depthTime) <= 0.25", source)
        self.assertIn("Enable SegFormer semantic mask", BODY_GUI_HTML)
        self.assertIn("camera-setting-segmentation-runtime", BODY_GUI_HTML)
        self.assertIn("/body/camera/segmentation", BODY_GUI_HTML)
        self.assertIn("world-map-segmentation-state", source)
        self.assertIn("async function renderSemanticMask(segmentation)", source)
        self.assertIn("displayedYoloOverlayKey", source)
        self.assertIn("yoloOverlayKey !== displayedYoloOverlayKey", source)
        self.assertIn("maskAge <= 2.5", source)
        self.assertIn("s old", source)
        self.assertIn("world-map-segmentation-overlay", source)
        self.assertIn("CAMERA · YOLOX", source)
        self.assertIn("SEGFORMER · SEMANTIC MASK", source)
        self.assertIn("visionGrid?.append(trajectory)", source)
        self.assertIn("visionGrid?.append(segmentation)", source)
        self.assertIn("new ResizeObserver(() => drawVisualOdometryMap())", source)
        self.assertIn("window.devicePixelRatio", source)
        self.assertIn("function drawVisualOdometryMap()", source)
        self.assertIn("aspect-ratio:4/3", source)
        self.assertIn("world-map-status-bar", source)
        self.assertIn("world-map-offline-strip", source)
        self.assertIn("classifyAge('imu'", source)
        self.assertIn("world-map-imu-gyro", source)
        self.assertIn("world-map-imu-attitude", source)
        self.assertIn("attitude.style.setProperty('--imu-roll'", source)
        self.assertIn("attitude.style.setProperty('--imu-pitch'", source)
        self.assertIn("Roll / pitch · no magnetic heading", source)
        self.assertIn("repeat(auto-fit,minmax(min(100%,300px),1fr))", source)
        self.assertIn("sensorPanel.append(liveReadouts, positionMap, computeCard)", source)
        self.assertNotIn("liveReadouts.append(computeCard)", source)
        self.assertIn(".system-gauge{position:relative;width:88px", source)
        self.assertIn(".system-gauge-center strong{font-size:16px}", source)
        self.assertIn("object-fit:cover;background:#02060a", source)
        self.assertIn("sensor-heading-copy", source)
        self.assertIn("sensor-gps-more", source)
        self.assertIn("targets.length === 1 ? '' : 's'", source)
        self.assertIn(".odom-edge-label", source)
        self.assertIn("world-map-vision-footer", source)
        self.assertIn("visionFooter.append(sensorPanel.querySelector('#world-map-sensor-note'))", source)
        self.assertIn("statusBar.append(sensorPanel.querySelector('#world-map-cloud-fetch')", source)
        self.assertIn('id="world-map-cloud-fetch" class="world-map-cloud-fetch"', source)
        self.assertIn("depthRenderKey !== renderedKey && depthRenderKey !== cloudBuildingKey", source)
        self.assertIn("data-source=\"tof\"", source)
        self.assertIn("staleAfterSeconds = { camera: 5", source)
        self.assertIn("The INA232 monitors the onboard input rail; external motor loads may be excluded", source)
        self.assertIn("#world-map-radar-state')?.closest('.sensor-readout-card')", source)
        self.assertIn("@container (max-width:760px)", source)
        self.assertIn("justify-items:stretch;align-items:stretch", source)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", source)
        self.assertIn("geometry.computeBoundingBox()", source)
        self.assertIn("cloud.camera.position.copy(target)", source)
        self.assertIn("camera.userData.userAdjusted = true", source)
        self.assertIn("Standalone SegFormer semantic class mask", source)
        self.assertNotIn("Segmentation overlay", source)
        self.assertNotIn("world-map-segmentation-toggle", source)
        self.assertNotIn("image-rendering:pixelated", source)
        self.assertIn("fetch('/body/camera/segmentation'", source)
        camera_refresh = source.split("async function refreshSensors()", 1)[1].split("async function refreshSensorSegmentation()", 1)[0]
        segmentation_refresh = source.split("async function refreshSensorSegmentation()", 1)[1].split("async function refreshSensorDepth()", 1)[0]
        self.assertNotIn("/body/camera/segmentation", camera_refresh)
        self.assertNotIn("renderSemanticMask", camera_refresh)
        self.assertIn("renderSemanticMask(segmentation)", segmentation_refresh)
        self.assertIn("}, 500);", source)
        quest = (root / "body_runtime_host" / "quest_vr.js").read_text(encoding="utf-8")
        self.assertNotIn("pollSensorSegmentation", quest)
        self.assertNotIn("sensorSemanticColor", quest)
        self.assertNotIn("fetch('/body/camera/segmentation'", quest)
        self.assertNotIn("latestSensorYolo?.frame_id === depthFrameId", source)
        self.assertIn("maskAge <= 2.5", source)
        self.assertIn("requestAnimationFrame(animateSensorCloud)", source)
        self.assertIn("}, 100);", source)
        self.assertIn("}, 500);", source)
        self.assertIn("Compute & power", source)
        self.assertIn("refreshSystemMetrics", source)
        self.assertIn("/system/metrics", source)
        self.assertIn("system-instrument-grid", source)
        self.assertIn("world-map-cpu-temp-gauge", source)
        self.assertIn("world-map-gpu-temp-gauge", source)
        self.assertIn("world-map-power-gauge", source)
        self.assertIn("Not exposed by kernel", source)
        self.assertIn("temperature_c", (root / "body_runtime_host" / "runtime.py").read_text(encoding="utf-8"))

    def test_modulino_movement_controls_expose_persistent_body_setting_and_live_sample(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("VENTUNO Q · Modulino Movement", BODY_GUI_HTML)
        self.assertIn("Use physical IMU in Body and Quest HUD", BODY_GUI_HTML)
        self.assertIn("/plugins/imu/status", BODY_GUI_HTML)
        self.assertIn("Save IMU setting", BODY_GUI_HTML)

    def test_quest_hud_exposes_live_sensor_health_without_simulation_fallback(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        dashboard = (root / "body_runtime_host" / "quest_vr_dashboard.js").read_text(encoding="utf-8")
        renderer = (root / "body_runtime_host" / "quest_vr.js").read_text(encoding="utf-8")
        self.assertIn("drawSensorStatusStrip", dashboard)
        self.assertIn("GPS", dashboard)
        self.assertIn("C/N₀ dB-Hz", dashboard)
        self.assertIn("updateSensorStatus({", renderer)
        self.assertIn("midas:", renderer)
        self.assertIn("yolo:", renderer)

    def test_ld2450_settings_expose_ventuno_bridge_and_live_frame_state(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("Ventuno STM32 UART · local Bridge", BODY_GUI_HTML)
        self.assertIn("Ventuno UART7 online", BODY_GUI_HTML)
        self.assertIn("bridge_status", BODY_GUI_HTML)
        self.assertIn("void refreshSensorDevices()", BODY_GUI_HTML)

    def test_brain_bridge_settings_are_mounted_in_runtime_view(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("const page=document.getElementById('view-runtime')", BODY_GUI_HTML)
        self.assertIn("Persistent Body → Brain bridge settings.", BODY_GUI_HTML)
        self.assertIn("void refreshBrainBridgeSettings()", BODY_GUI_HTML)
        self.assertIn("document.getElementById('brain-bridge-save')", BODY_GUI_HTML)

    def test_world_model_exposes_grounded_vlm_scene_visually(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("VLM-grounded spatial scene", BODY_GUI_HTML)
        self.assertIn("semantic-scene-view", BODY_GUI_HTML)
        self.assertIn("semantic-scene-vlm-status", BODY_GUI_HTML)
        self.assertIn("Interpret current scene", BODY_GUI_HTML)
        self.assertIn("renderSemanticScene(w?.perception,w?.sim)", BODY_GUI_HTML)
        self.assertIn("not photogrammetric reconstruction", BODY_GUI_HTML)

    def test_sensorimotor_benchmark_exposes_blind_scene_count_and_paired_metrics(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("sensorimotor-scene-count", BODY_GUI_HTML)
        self.assertIn("new Option(`${count} scene${count===1?'':'s'}`,String(count))", BODY_GUI_HTML)
        self.assertIn("camera_only", BODY_GUI_HTML)
        self.assertIn("camera_plus_sensors", BODY_GUI_HTML)
        self.assertIn("paired_scene_count", BODY_GUI_HTML)

    def test_hardware_inventory_updates_without_replacing_unchanged_rows(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML

        self.assertIn("function setStableHtml(node,html)", BODY_GUI_HTML)
        self.assertIn("fnk-serial-devices", BODY_GUI_HTML)
        self.assertIn("No USB serial adapters detected by this Body host.", BODY_GUI_HTML)
        self.assertIn("(data.modules||[]).filter(m=>m.detected||m.enabled)", BODY_GUI_HTML)


if __name__ == "__main__":
    unittest.main()
