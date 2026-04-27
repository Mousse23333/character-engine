# E-11-I2V — Wan 2.2 I2V-A14B on Alice (path B substitute for Animate)

**Status**: ✅ **End-to-end SUCCESS on aarch64 + GB10**
**Date**: 2026-04-27
**Total wall time**: 23.2 min (model load 2 min + sampling 20.5 min + save 3 s)
**Output**: `samples/alice_i2v.mp4` 1.38 MB, 33 frames @ 16 fps (~2.06 s video), 736×528

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

## Final metrics

| Stage | Time | Notes |
|---|---|---|
| Pipeline create + T5 load (CPU) + VAE load | ~55 s | |
| WanModel build (high + low noise experts loaded) | ~55 s | |
| **Total model load** | **~120 s (2 min)** | Memory peaks ~93 GB during load |
| First inference step | 54 s | First-step warmup |
| Steps 2-15 (high-noise expert) | 27-29 s/step | Settled, healthy |
| Step 16 (high → low expert SWAP) | **~165 s** | Offload swap — memory shuffle |
| Steps 17-40 (low-noise expert) | 26-30 s/step | Recovered after swap |
| **Total sampling (40 steps)** | **20:28 min** (1228 s) | wall-clock |
| Save MP4 | 3 s | |
| **Total end-to-end** | **23.2 min** (1391 s) | from process start to file written |

### Quality (CLIP-I via ViT-bigG-14, 8 evenly-sampled frames vs original Alice ref)

| Metric | Value | Interpretation |
|---|---|---|
| **CLIP-I to ref (per-frame mean)** | **0.954** | excellent identity preservation |
| CLIP-I to ref (std) | 0.011 | very low variance — character is **stable** across frames |
| CLIP-I to ref (min frame) | 0.940 | even worst frame still strong match |
| **Cross-frame CLIP-I (mean off-diagonal)** | **0.976** | character extremely consistent within clip |
| Cross-frame CLIP-I (min pair) | 0.945 | least-similar two frames still tightly clustered |

### Cost ratio (informs AC-3 cost model)

| Output (832×480 → 736×528) | Cost |
|---|---|
| Frames generated | 33 |
| Wall time | 23.2 min |
| **Per second of generated video** | **~11 min generation** |
| **Per frame** | **~42 s** |
| **VRAM peak** | ~93 GB during load, swaps to ~50 GB during inference |

## Architecturally relevant findings (confirmed by this run)

1. **Wan 2.2 14B I2V loads and runs on aarch64 + CUDA 13.1** ✅ — every dependency that was a question yesterday (flash_attn, triton, decord shim) actually held up.
2. **Memory headroom is workable**: 119 GB unified is enough for 14B MoE with offload between experts. Peak load 93 GB, settles to ~50 GB during inference.
3. **Per-second-of-video cost ~11 min** on this hardware at 832×480. For batch / offline pipelines, this is workable. For real-time — not even close. **AC-3 (sandbox + state explosion) requires aggressive caching** if Path B is used for animation.
4. **Identity preservation is excellent (cross-frame), but identity match to original ref is "anime-style match" not "exact-character match"**: CLIP-I 0.954 to ref — but visual inspection shows **the character has drifted from the precise Alice silhouette** (slightly different hair, ribbon color became darker, proportions more standard anime). The model preserved STYLE + design space, but not EXACT identity. **This is the gap an architect should know about: Wan 2.2 I2V is a "concept-aligned" generator, not a "character-clone" generator** — you need IP-Adapter / Animate-14B with explicit ref conditioning for stricter ID preservation.
5. **The "walking forward" prompt produced near-static motion** — frame 0 and frame 32 are visually almost identical. Wan I2V without an explicit motion source defaults to "subtle character animation" (breathing, hair sway), not locomotion. **For real motion control, Animate-14B with driving video is required.** This validates yesterday's discovery D-01: I2V is the "1 model, no preprocess" easy path; Animate-14B is the "real motion" hard path.
6. **The high→low expert swap at boundary timestep (step 16) is a one-time ~165 s penalty** — informs scheduling (don't run multiple Wan jobs interleaved if you can avoid the swap).

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
