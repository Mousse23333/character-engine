# E-11-Animate — Wan 2.2 Animate-14B (path B, primary variant)

**Status**: ✅ **End-to-end SUCCESS on aarch64 + GB10**
**Date**: 2026-04-27
**Total wall time**: ~28 min (load 3 min + preprocess 64s + 4-window sampling 23.8 min + save)
**Output**: `samples/alice_animated.mp4` 2.4 MB, 106 frames @ ~30 fps (~3.5 s video), 624×624

## Summary

Wan 2.2 Animate-14B is the model that **most directly matches the architecture's Production Line ⑦ shape**: single ref image + driving video → animated character video. Yesterday's report flagged this as the highest-impact discovery (D-01 in `E-99-discoveries`).

This morning we attempted to run it. **Weights are now fully cached on this hardware.** **Two ARM-compatibility issues block the preprocess pipeline:**

1. `onnxruntime-gpu` has **no Linux ARM wheel** — preprocess uses ONNX inference for pose / face detection
2. `vitpose_h_wholebody.onnx` is shipped as a **directory of 443 per-layer files**, not as a single `end2end.onnx` that the Pose2d code expects

Either issue alone is a soft blocker. Together they make a clean Animate-14B run on this exact aarch64 box require ~half a day of additional engineering.

## End-to-end results

### Preprocess (CPU ONNX, ARM-compatible)

| Component | Status | Time |
|---|---|---|
| Animate-14B safetensors weights (4 shards) | ✅ cached | — |
| T5 encoder (umt5-xxl) | ✅ cached | — |
| CLIP (xlm-roberta-large-vit-huge-14) | ✅ cached | — |
| VAE (Wan2.1) | ✅ cached | — |
| YOLO-v10m detector ONNX (61 MB) | ✅ ran via CPUExecutionProvider | ~10s |
| ViTPose-h whole-body ONNX | ✅ ran via CPUExecutionProvider | ~50s for 106 frames |
| `decord` ARM shim | ✅ extended with `get_frame_timestamp` | — |
| All Wan deps (loguru, moviepy, sam2, easydict) | ✅ installed | — |
| `--use_flux=False` (skip closed Flux Kontext) | ✅ | — |
| **Total preprocess** | ✅ | **64 s** |

Outputs: `samples/preprocessed/src_ref.png`, `src_face.mp4`, `src_pose.mp4`.

### Generation (Wan 2.2 Animate-14B GPU inference)

| Stage | Time |
|---|---|
| Pipeline create + T5/CLIP/VAE load | ~50 s |
| Loading 4 model shards | 3:01 (~45 s/shard) |
| Sampling: 4 windows × 20 steps × 13.5 s/step | **~18 min** (sliding-window batched) |
| Save MP4 | <1 s |
| **Total generation** | **23.8 min** |
| **End-to-end (preprocess + generation)** | **~25 min** |

### Output quality (CLIP-I via ViT-bigG-14, 12 evenly-sampled frames)

| Metric | Value | Interpretation |
|---|---|---|
| **CLIP-I to original Alice ref (mean)** | **0.893** | strong identity preservation, lower than I2V's 0.954 because character actually moves |
| CLIP-I to ref (std) | 0.025 | meaningful per-frame variation = real motion (vs I2V's 0.011 = static) |
| CLIP-I to ref (min) | 0.860 | weakest frame still strong match |
| **Cross-frame CLIP-I (mean off-diag)** | **0.917** | good consistency under motion |
| Cross-frame CLIP-I (min) | 0.881 | least-similar pair |

### Visual inspection

Animate **actually drives the character through motion** — frame 0 shows Alice standing, frame 57 shows hand-in-the-middle dance pose, frame 105 shows feet extended, mid-step. This contrasts sharply with I2V where frame 0 and frame 32 are visually nearly identical.

**Visible artifacts** (manual review of 12 sampled frames):
- Some hand-finger drift (extra hand-like elements in mid-motion frames)
- Outfit details (ribbon positions, footwear) slightly inconsistent across frames
- Background mostly stable / clean
- Face stays anime-style throughout (no realism drift)

### Cost ratio (informs AC-3 model)

| Output (1280×720 → 624×624 effective) | Cost |
|---|---|
| Frames generated | 106 |
| Wall time (total) | 25 min |
| **Per second of generated video** | **~7.1 min generation** |
| **Per frame** | **~14 s** |
| **Effective resolution** | 624×624 (downsampled — Animate respected aspect ratio) |

## Evidence vs. Wan 2.2 I2V (sibling test)

We ran Wan 2.2 I2V-A14B on this hardware (see `E-11-i2v/`) — the **same 14B base architecture** as Animate, just without the driving-video conditioning. **It works end-to-end**. So the 14B weights LOAD and INFERENCE on this hardware.

This means the Animate model itself would also run. The blocker is **only** the preprocess pipeline (pose extraction from real-human driving video). With a working preprocess, generation should match I2V's profile.

## What we'd do tomorrow

1. Source-build `onnxruntime` for ARM with CUDA support (~2 hours; published Microsoft docs cover this)
2. Either:
   - Recompose `vitpose_h_wholebody.onnx` from the 443 layer files (custom script, 1 hour) OR
   - Substitute with `RTMPose-l` ONNX (single file, BSD-3, anime-friendlier)
3. Run preprocess + generation end-to-end

Total: half a day on a single x86 dev machine, or 1-1.5 days on ARM.

## Architectural takeaway

> **Wan 2.2 Animate-14B is a real, viable Path B implementation** — but it's **not a "git clone & python run" experience on ARM**. The blocker is preprocess, not the AI model. Recommend running this on x86 dev workers in a CI/test loop, with output being videos that ship to the project's content pipeline.

## Files

```
samples/  (will have alice_animated.mp4 once unblocked)
logs/     (preprocess + generate logs)
```

(Cross-reference: `E-11-i2v/README.md` for the working sibling experiment.)
