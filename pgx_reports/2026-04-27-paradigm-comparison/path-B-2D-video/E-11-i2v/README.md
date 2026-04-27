# E-11-I2V — Wan 2.2 I2V-A14B on Alice (path B substitute for Animate)

**Status**: 🟡 **Inference in progress at writing — partial metrics below**
**Date**: 2026-04-27

## Why I2V (and not Animate-14B as the architect prioritized)

The architect's #1 priority is end-to-end Path B confirmation. Animate-14B has additional ARM-compat blockers in the preprocess (`onnxruntime-gpu` no wheel, ViTPose stored as 443 layer files instead of `end2end.onnx`). I2V uses the **same 14B MoE base** but takes only an image + text prompt — no preprocess pipeline needed.

**If I2V works on this hardware, the 14B inference path is proven**, and Animate's only remaining gap is the preprocess. So I2V is a faithful proxy for "Path B inference works on GB10/aarch64".

## Run config

| Parameter | Value |
|---|---|
| Model | `Wan-AI/Wan2.2-I2V-A14B` (high-noise + low-noise MoE) |
| Resolution | 832×480 |
| Frames | 33 (~2 sec @ 16fps) |
| Sampler | UniPC, 40 steps |
| Sample shift | 5.0 |
| Guide scale | (3.5, 3.5) |
| Offload | True (model swap between high/low noise) |
| T5 device | CPU (saves GPU) |
| Convert dtype | True |
| Backbone params | 14B per expert; bf16 |

## Live metrics (filling in real-time)

| Stage | Time | GPU peak | Notes |
|---|---|---|---|
| Pipeline create | 54 s | — | Pre-loading |
| T5 load | ~10 s | — | onto CPU |
| VAE load | ~1 s | — | |
| WanModel build (incl. high+low noise weights) | ~55 s | (loading) | |
| **Total load** | **~120 s** | (memory peaks during load) | |
| Step 1 | 54 s | — | first step always slowest |
| Steps 2-N | ~30 s/step | — | settled |
| Inference (40 steps) | ~25 min ETA | — | _filling_ |
| Save MP4 | _pending_ | | |

**Live progress** (last sampled): step 5 / 40 at +2:44, est total ~17:28 remaining at 30 s/step.

## Architecturally relevant findings (already)

1. **Wan 2.2 14B I2V loads and runs on aarch64 + CUDA 13.1** — every dependency that was a question yesterday (flash_attn, triton, decord shim) actually held up.
2. **Memory headroom is workable**: 119 GB unified, model + cache + intermediates fit.
3. **Per-step inference cost ~30 s at 832×480** is the real number you need for "how long does 1 second of generated video cost on this hardware?". For 33 frames: 30 × 40 ≈ 20 min wall. That's roughly **10 minutes per second of generated video** at this resolution — informs the AC-3 cost analysis.

## Files

```
samples/
  alice_i2v.mp4            — 832×480, 33 frames, ~2 sec  (filling in)
logs/
  run.log                  — full inference log
```

## Cross-reference

- `E-11-animate/README.md` — what Animate-14B would have done if preprocess weren't ARM-blocked
- Top-level `EXECUTIVE_SUMMARY.md` § 2 for Path B verdict
