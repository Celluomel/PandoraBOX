# Body YOLOX

YOLOX is an optional, advisory camera detector in the Body Runtime. It never sends motor commands. The Body sends candidate detections to its existing scene interpreter only when YOLOX reports a low-confidence or ambiguous frame; the VLM still verifies candidate labels against the image.

## Install on the VENTUNO Q

The installer is intentionally separate from normal Body startup. On the Ventuno, enable it for one startup:

```bash
BODY_INSTALL_YOLOX=1 ./start_body.sh
```

This creates an isolated Python environment at `~/.venvs/yolox-infer`, installs Qualcomm AppBuilder, OpenCV and NumPy, then fetches the IQ-8275 QNN W8A8 model into `~/models/yolox-qairt245/yolox-qnn_dlc-w8a8/yolox.dlc`. The CLI fetch uses Qualcomm AI Hub's published model asset filters; it may require network access. Subsequent Body starts do not reinstall the packages.

## Configure

Open Body GUI → Sensing & vision → Camera settings → YOLOX object detection. Enable it, keep `HTP, fall back to CPU` initially, check the Python and DLC paths, then save. YOLOX values are stored in `data/body/config.json` and survive service restarts. Camera inference runs on a separate worker process so QNN dependencies do not contaminate the main Body Python environment.

The Quest camera tile and anchored camera arc use the same annotated frame, with normalized boxes, label and confidence. If there is no fresh YOLOX result, the frame is shown without boxes. The VLM fallback has a configurable cooldown and remains advisory.

## Runtime caveat

The VENTUNO Q has an AI Hub-published YOLOX QNN target, but runtime initialization depends on the installed QAIRT/HTP stack. The service reports the runtime actually selected; `HTP, fall back to CPU` keeps detections available when HTP cannot initialize. The CPU fallback is functional but much slower and should not be presented as NPU performance.
