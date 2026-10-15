# PandoraBOX Indoor/Outdoor Semantic Segmentation

SegFormer-B0 fine-tuned from `nvidia/segformer-b0-finetuned-ade-512-512` on
public ADE20K SceneParse150 and COCO-Stuff 10K data. The shared output taxonomy
contains 247 classes, merging equivalent labels across datasets.

## Ventuno Q artifact

- `segformer-ade-coco-247.dlc`: Qualcomm QNN DLC, INT8, compiled for Arduino
  VENTUNO Q / IQ-8275.
- `taxonomy.json`: class ID to label mapping used to report and visualize masks.
- Fine-tuning ran on the AMD Radeon RX 9070 XT via PyTorch ROCm, using 9,000
  training examples from each public dataset. On held-out validation data,
  ADE20K mIoU is 0.3268 vs. 0.3001 baseline (1,024 images); COCO-Stuff mIoU
  is 0.1814 vs. 0.1118 baseline (1,000 images).
- Runtime default: HTP first, CPU fallback on HTP load/inference failure.
- HTP inference validation: AI Hub job `jp4e14j2g`; output shape
  `(1, 247, 128, 128)`, 327/327 profiled layers assigned to NPU, estimated
  warm inference about 6.5 ms. This is the AI Hub benchmark, not the full
  on-device service latency.

On the physical Ventuno Q, the AppBuilder service was verified on a live camera
frame: HTP reported `ready` and predicted scene labels including wall, person,
ceiling, screen and table. A separate explicit CPU-runtime check also reported
`ready`; the service was then restored to HTP-first and verified on HTP again.
Observed service latency was about 59-103 ms on HTP and 459 ms on CPU during
these checks; timings vary with system load. The CPU check verifies the CPU
runtime path, while unit tests exercise automatic HTP-inference-failure to CPU
fallback. AI Hub's generated-tensor smoke test verifies target output/runtime,
not semantic accuracy; dataset mIoU is the semantic quality evidence.

## Training and export

Training, ONNX export, and AI Hub compile scripts are in
`scripts/indoor_segmentation/`. Their datasets, checkpoints, credentials, and
temporary exports stay outside Git in `.training-runtime/`. The DLC and taxonomy
are versioned here so a Ventuno checkout can recover them with Git.

For a clean Body/vision deployment, including the separate QNN environment and
external YOLOX/MiDaS artifacts, see [`docs/BODY_VISION_DEPLOYMENT.md`](../../docs/BODY_VISION_DEPLOYMENT.md).
