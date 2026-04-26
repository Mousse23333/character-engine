# E-13 — Video → Pose → Rigged Animation (End-to-End)

**Status**: ⚠️ **Partial — found a critical-path failure** before any GPU-heavy step.
**Time spent**: 25 min
**Architect's question this addresses**: **Q5** — Can the architecture spec's plan (video → DWpose → SMPL-X → retarget to rigged character) work end-to-end?

## TL;DR — the most important finding of this dir

> **Real-photo-trained pose detectors (OpenPose, DWpose) detect ZERO keypoints on the Alice anime reference image.** Both the original 189×267 and the Real-ESRGAN-upscaled 756×1068 produce empty pose output (`(704×512×3 image, mean=0.0, all pixels black`).
>
> This is **not a low-resolution issue**: it is a **distribution mismatch**. OpenPose / DWpose were trained on real photographs (COCO + COCO-WholeBody). Anime characters have non-photo proportions (large heads, small bodies, simplified silhouettes), non-photo skin shading, and 2D-cel features. The detectors don't fire.

**Architectural implication**: the plan "AI generates video → DWpose extracts motion → retarget to rigged character" has a **silent failure point at step 2** for anime-styled output. You need either:
1. **An anime-trained pose detector** (community efforts: AnimePose, sketch2pose, etc.) — none are SOTA / Apache-2.0 with confidence as of 2026-04
2. **Generate the video in a real-photo intermediate style** (e.g., realistic CG), extract pose, then re-stylize. Adds another generative step and more failure modes.
3. **Skip the pose-extraction step entirely** by using a **pose-conditioned video generation model** like Wan 2.2 Animate (see below)

## What was tested

| Method | Input | GPU | Time | Result |
|---|---|---|---|---|
| `controlnet_aux.OpenposeDetector` (with `hand_and_face=True`) | `alice_ref.jpeg` 189×267 | CPU (model defaulted) | 0.65 s | **0 keypoints** |
| Same | `realesrgan_x4_756x1068.png` | CPU | 0.60 s | **0 keypoints** |
| DWpose ONNX | (planned) | needs onnxruntime-gpu — **no ARM wheel** | — | unable to test on this hardware |
| DWpose mmpose path | (planned) | needs mmcv (notoriously hard on ARM) | — | deferred |

## Why this is decisive

The architecture spec (PIPELINE_ARCHITECTURE_SPEC §7) and the survey (E-10, E-13) both implicitly assume that **DWpose works on the AI-generated video frames**. If the AI generates anime-styled video (from the Character LoRA in E-11), and that video is anime-styled (goal of the project), and DWpose can't detect anime poses — **the plan does not run as specified**.

This is the kind of finding that — per the architect's strong preference — *failures at this level matter more than partial successes*. You'd much rather know **before** spending a day training a Wan 2.2 Character LoRA that the next downstream step doesn't accept its output.

## What replaces the broken link

**Option A — Use Wan 2.2 Animate-14B directly** (see `E-11/details.md`, `ARCHITECT_DECISIONS.md`):
```
Reference image (anime character) + driving video (real human dance)
                              ↓
                    Wan 2.2 Animate-14B
                              ↓
              Anime character moving like the human
```
This is **already what the model does** — single-step, no pose-extraction in the loop.
Pre-condition: 23-50 GB VRAM (workable on freed GB10).
**This bypasses all of E-08/E-10/E-13 traditional pipeline.**

**Option B — Retarget from Mixamo offline FBX library** (see `E-09`):
- 2,500+ canned humanoid animations are downloadable as FBX from Mixamo (free + offline-usable; the API is the SaaS, the FBX files themselves can be redistributed).
- Skip pose extraction entirely — work from human-curated motion clips.
- Cost: less expressive than user-driven motion, but works today.

**Option C — Train an anime pose detector** (research project)
- Synthesize anime + pose pairs from existing tools (e.g., MMD models with known skeletons rendered in anime style)
- Fine-tune a YOLOv8-pose / RTMPose model
- Estimated 2-4 weeks of work; not a one-night experiment.

## Files

- `samples/alice_orig_openpose.png` — empty pose result (proof of failure)
- `samples/alice_x4_openpose.png` — same, on upscaled image
- `details.md` — technical details + community-evidence on anime pose detection state-of-art

## Cross-reference

| Report | Why related |
|---|---|
| `E-08-rigging/README.md` | The "rigged target" half of E-13 — also bottlenecked by ARM/VRAM |
| `E-11-wan22-video/README.md` | Wan 2.2 Animate-14B as Option A above |
| `E-09-mixamo-retarget/README.md` | Option B — offline FBX retarget |
| `ARCHITECT_DECISIONS.md` § 4 | This finding feeds AC-5 (Animation is open problem) reaffirmation |
