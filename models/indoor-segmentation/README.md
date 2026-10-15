# PandoraBOX Indoor/Outdoor Semantic Segmentation

SegFormer-B0 fine-tuned from `nvidia/segformer-b0-finetuned-ade-512-512` on
public ADE20K SceneParse150 and COCO-Stuff 10K data. The shared output taxonomy
contains 247 classes, merging equivalent labels across datasets.

## Ventuno Q artifact

- `segformer-ade-coco-247.dlc`: Qualcomm QNN DLC, INT8, compiled for Arduino
  VENTUNO Q / IQ-8275.
- `taxonomy.json`: class ID to label mapping used to report and visualize masks.
- Validation (1,024 images/dataset): ADE20K mIoU 0.3268 (baseline 0.3001),
  COCO-Stuff mIoU 0.1814 (baseline 0.1118).
- Runtime default: HTP first, CPU fallback on HTP load/inference failure.
- HTP inference validation: AI Hub job `jp4e14j2g`; output shape
  `(1, 247, 128, 128)`, 327/327 profiled layers assigned to NPU, estimated
  warm inference about 6.5 ms.

The AI Hub smoke test used a generated input tensor. It verifies target runtime
execution and output schema, not semantic accuracy on camera scenes. The actual
Ventuno AppBuilder service still requires on-device verification before enabling
segmentation in production.

## Training and export

Training, ONNX export, and AI Hub compile scripts are in
`scripts/indoor_segmentation/`. Their datasets, checkpoints, credentials, and
temporary exports stay outside Git in `.training-runtime/`. The DLC and taxonomy
are versioned here so a Ventuno checkout can recover them with Git.
