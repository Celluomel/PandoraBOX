# Body Vision Deployment

This covers the Python dependencies and model files needed to reproduce the
Body camera stack on a clean VENTUNO Q checkout. The root `requirements.txt` is
for the main PandoraBOX application and optional dataset/training tools; it is
not the sole Body or Qualcomm runtime installer.

## Python environments

- `start_body.sh` creates `body_venv` and installs `body_requirements.txt`.
  This includes the Body camera, MiDaS support dependencies such as `timm`,
  NumPy, and the CPU PyTorch world-model dependency.
- YOLOX, MiDaS DLC inference, and SegFormer HTP inference share the isolated
  `~/.venvs/yolox-infer` AppBuilder environment. Provision it once from the
  repository root with `bash ./install_body_yolox.sh`. This installs the
  platform-specific `qai-appbuilder==2.48.40`, OpenCV and NumPy, verifies the
  system QAIRT/DSP packages, and fetches the published IQ-8275 YOLOX DLC if it
  is not already present. It may require sudo and network access.
- `requirements.txt` includes `datasets` for the optional ADE20K/COCO-Stuff
  training and evaluation scripts. PyTorch is deliberately installed separately
  using the hardware-specific instructions in that file; on the AMD training
  PC, use the ROCm environment rather than a CPU/NVIDIA wheel.

## Model artifacts

- **SegFormer:** `models/indoor-segmentation/segformer-ade-coco-247.dlc` and
  `taxonomy.json` are versioned in Git. The QNN runtime may create the adjacent
  `.dlc.bin` cache on first use; it is intentionally ignored by Git.
- **YOLOX:** the installer fetches the public precompiled model into
  `~/models/yolox-qairt245/yolox-qnn_dlc-w8a8/yolox.dlc`.
- **MiDaS:** the compiled `midas-float.dlc` is currently an external artifact,
  not in this repository, and there is no automatic fetch step. Obtain the
  compiled DLC from its Qualcomm AI Hub job/export and place it at
  `~/models/midas-qualcomm/midas-float.dlc`, or configure the actual path in
  Body Camera settings. Do not put an AI Hub token in Git or a deployment file.

After provisioning, start the Body with `./start_body.sh` (or the installed
systemd unit), then configure the desired camera models and keep their runtime
set to **HTP preferred, fall back to CPU**. Segmentation is optional and disabled
by default; enable it in Camera settings. A fresh deployment is not complete
until each selected DLC path exists and the camera settings report the model as
`ready` on the intended device.
