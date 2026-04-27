# E-11-Animate — Wan 2.2 Animate-14B (path B, primary variant)

**Status**: ⏸ **Partial — Animate-14B weights downloaded but preprocess pipeline has ARM friction**
**Date**: 2026-04-27

## Summary

Wan 2.2 Animate-14B is the model that **most directly matches the architecture's Production Line ⑦ shape**: single ref image + driving video → animated character video. Yesterday's report flagged this as the highest-impact discovery (D-01 in `E-99-discoveries`).

This morning we attempted to run it. **Weights are now fully cached on this hardware.** **Two ARM-compatibility issues block the preprocess pipeline:**

1. `onnxruntime-gpu` has **no Linux ARM wheel** — preprocess uses ONNX inference for pose / face detection
2. `vitpose_h_wholebody.onnx` is shipped as a **directory of 443 per-layer files**, not as a single `end2end.onnx` that the Pose2d code expects

Either issue alone is a soft blocker. Together they make a clean Animate-14B run on this exact aarch64 box require ~half a day of additional engineering.

## What's clean

| Component | Status |
|---|---|
| Animate-14B safetensors weights (4 shards) | ✅ cached |
| T5 encoder (umt5-xxl) | ✅ cached |
| VAE (Wan2.1) | ✅ cached |
| YOLO-v10m detector ONNX (61 MB) | ✅ cached |
| `decord` ARM shim | ✅ written + tested |
| Wan repo install (excl. decord, included via shim) | ✅ |

## What's blocking

| Component | Blocker | Work to unblock |
|---|---|---|
| `onnxruntime-gpu` | no ARM wheel for any cp version | source-build from `microsoft/onnxruntime` (~2 hours) OR fall back to CPU `onnxruntime` (slow) |
| `vitpose_h_wholebody.onnx` directory format | repo ships 443 layer files instead of single ONNX | recompose from layer files OR find alternate ViTPose ONNX |
| `FluxKontextPipeline` (when `--use_flux`) | Flux Kontext closed-source weights | always pass `--use_flux=False` (preprocess accepts this) |

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
