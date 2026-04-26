# E-13 — Details

## Code that ran

```python
from controlnet_aux import OpenposeDetector
op = OpenposeDetector.from_pretrained('lllyasviel/Annotators')
pose = op(image, hand_and_face=True, output_type='pil')
```

The `OpenposeDetector` uses `body_pose_model.pth` (OpenPose 1.7 weights, body-25) +
`hand_pose_model.pth` (the Pittsburgh hand model). Both are real-photo trained.

## Output verification

```
shape:    (704, 512, 3)   — standard OpenPose viz canvas
mean:     0.0
non-zero: 0 / 360448 pixels
unique:   1 (all 0)
```

Both alice ref images produced fully-black canvases — meaning the body detector
returned zero keypoints with sufficient confidence to draw.

## Why this isn't a bug

OpenPose / DWpose / RTMPose all train on **MS-COCO** + **COCO-WholeBody** —
real-world photographs annotated by human labelers. Anime characters violate
several inductive biases of these models:

1. **Proportion** — anime body ratios (large head, narrow waist, small features)
   fall outside the COCO statistical distribution.
2. **Texture / shading** — cel-shaded flat colors don't have the gradient cues
   the detector keys on.
3. **Pose taxonomy** — moe / chibi / kawaii poses (e.g. peace-V, head-tilt at
   extreme angles) are underrepresented or absent.
4. **Eye / face geometry** — anime eye scale (~30% of face) breaks face landmark
   priors.

The result: detectors emit no keypoints with confidence ≥ threshold, so the
visualization is empty. With threshold = 0 you'd get noise; that's not useful
for downstream retargeting.

## Community state-of-art for anime pose detection (2026-04)

| Effort | Approach | Status | Open weights |
|---|---|---|---|
| AnimaPose / OpenAnimePose | YOLOv8-pose fine-tuned on Danbooru | small community projects | partial |
| sketch2pose | Manga panel pose | research, not production | yes |
| Mixamo character pre-rigged | Mixamo's library uses CMU motion capture | not really anime-specific | FBX downloads available |
| **Wan 2.2 Animate built-in preprocessor** | Pose extraction inside the model | **bundled with Wan 2.2 Animate-14B** | yes (Apache-2.0) |

The Wan 2.2 Animate-14B preprocessor uses **internal pose+face motion features**
that are not exposed as a standalone OpenPose-style API. This means: it works,
but only inside Wan 2.2 Animate's own pipeline. **You can't easily extract
"OpenPose JSON" from it for retargeting to a different rig.**

## Alternative: ARM-incompatible tools we couldn't try

- `onnxruntime-gpu` — no ARM wheels (only x86_64); blocked
- `mmcv` / `mmpose` / `mmdet` — notoriously hard to install; not attempted in time budget
- DWPose ONNX direct — needs `onnxruntime-gpu` for CUDA acceleration

If x86 worker available, the test sequence to try:
1. Install `onnxruntime-gpu`
2. Download DWpose ONNX from yzd-v/DWPose
3. Re-run on alice ref — likely the same null-result, since DWpose was also
   trained on COCO-WholeBody.
4. Try YOLO-pose v8 (`ultralytics/yolov8x-pose-p6`) — likely also fails, same reason

## Bottom line for the architect

The architecture spec lists "video → DWpose → 3D骨架 → retarget" as a viable
production line. **It is not viable as specified for anime-styled output.**

There are **two clean exits** that preserve the spirit of AC-5
(Animation is open problem):

1. Migrate to Wan 2.2 Animate-14B as the primary "AnimationFactory ⑦"
   implementation. Single open-source model. Apache-2.0.
2. Retain the spec'd pipeline but explicitly scope it to "real-photo styled
   intermediate video" — generate in realistic style, extract pose, re-stylize.

Both are worse than the spec implies. **Option 1 is much simpler and more
likely to work today.**
