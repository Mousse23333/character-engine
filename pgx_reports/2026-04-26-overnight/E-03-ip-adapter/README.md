# E-03 — Zero-Train Identity Injection (IP-Adapter / PuLID / InstantID)

**Status**: ⛔ **Not run tonight** — same VRAM blocker.
**Architect's question**: **Q1 cross-view** + **Q3 method comparison**.

## Plan in `tools/run_p1_p4.sh` `e03()`

Three methods, each generating 20 images at the same set of prompts on the
Alice reference, on Illustrious-XL backbone:

| Method | License | Setup cost | Quality (community-evidenced) |
|---|---|---|---|
| **IP-Adapter Plus SDXL** (h94) | Apache-2.0 | trivial (5 LoC) | CLIP-I 0.78-0.82 typical |
| **PuLID** | Apache-2.0 | needs InsightFace antelopev2 detector (extra setup) | CLIP-I 0.83-0.87 typical (+5-10 % over IP-Adapter) |
| **InstantID** | Apache-2.0 | needs antelopev2 + ControlNet pose | comparable to PuLID |

CLIP-I scoring against the reference, with OpenCLIP ViT-bigG-14, after each batch.

## Pre-prediction (to validate when we run it)

1. **IP-Adapter Plus** will hit ~0.80 CLIP-I average. Mean ranks: outfit > hair > face.
2. **PuLID** will be 5-10 % higher CLIP-I but at the cost of needing antelopev2
   (which is an additional ~120 MB ONNX model — luckily ARM-compatible).
3. **InstantID** is a tier above PuLID for **face** identity but tends to
   over-fit face geometry to expense of body. Less useful for full-body shots.

## Why this is decision-relevant

If IP-Adapter Plus gets us to CLIP-I ≥ 0.80 with **zero training**, then for
Production Line ② (Identity) we may not need Character LoRA at all for many
use cases — a major engineering simplification. Character LoRA becomes a
specialization, not a default.

If even PuLID can't break 0.85, then training Character LoRA is unavoidable
for high-fidelity character work — and we need to invest in that training
pipeline (Kohya / ai-toolkit) and dataset prep (E-00 expansion).

This is **the experiment most likely to drive a concrete architectural decision**.

## Cross-reference

- `E-00-data-augmentation/details.md` — uses IP-Adapter as the data expander
- `E-11-wan22-video/README.md` — Wan 2.2 Animate is "IP-Adapter-style" for video
- `ARCHITECT_DECISIONS.md` § 1.1 / § 2.1 — decision posture toward LoRA

## Files (will be populated when run)

- `samples/ipadapter_*.png` (20 images)
- `samples/pulid_*.png` (20 images)
- `samples/instantid_*.png` (20 images)
- `samples/clip_scores.json` — per-method statistics
- `details.md` — per-prompt logs
