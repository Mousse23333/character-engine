# E-11 — Wan 2.2 Character Video Generation

**Status**: ⛔ **NOT RUN tonight (vLLM holds 103 GB)** — but this dir contains
**the most architecturally important finding of the night**.
**Architect's question**: **Q1** + **Q5**

---

## TL;DR — the architecturally critical finding

> **Wan 2.2 includes a model variant — `Wan2.2-Animate-14B` — that does
> single-image + driving-video → animated character video in one model.
> This was not anticipated in the architecture spec. It potentially
> collapses the "Animation Factory ⑦" production line from a 4-step
> pipeline (LoRA train → video gen → DWpose → retarget) into a
> single inference call.**

Combined with the E-13 finding (DWpose can't see anime characters), this
is **probably the biggest decision-shifter in the report**.

The model card also explicitly says:
> "we do not recommend using LoRA models trained on Wan2.2, since weight
> changes during training may lead to unexpected behavior"

This **directly contradicts the architecture spec's plan** to "train a
Character LoRA on Wan 2.2". The spec was written assuming Wan2.2 LoRA
worked like SDXL LoRA. **Wan2.2 community guidance is the opposite.**

---

## The full Wan 2.2 model family (from `github.com/Wan-Video/Wan2.2`)

| Variant | What it does | Single-GPU VRAM | Inference time (referenced GPU) |
|---|---|---|---|
| **T2V-A14B** | text → video, MoE 14B | 80 GB | (not explicit) |
| **I2V-A14B** | image → video, MoE 14B | 80 GB | (not explicit) |
| **TI2V-5B** | text+image → video | **24 GB** (consumer) | 5 s @ 720p in <9 min on 4090 |
| **S2V-14B** | speech → video | 80 GB | — |
| **Animate-14B** | **ref image + driving video → animated character** | H100 ~40 GB / 4090 ~23 GB / A100 ~50 GB | H100 ~60 s, 4090 ~120 s for short clip |

**License**: Apache-2.0 (all variants)

## Why Wan 2.2 Animate matters more than the spec realized

The architecture's "Animation Factory ⑦" is described as:

```
Reference image → train Character LoRA on Wan 2.2 (or HunyuanVideo)
                              ↓
                      Generate text-to-video
                              ↓
                   DWpose extract per-frame skeleton
                              ↓
                       SMPL-X 3D pose lift
                              ↓
                  Retarget to rigged character
                              ↓
                          Animation asset
```

This is a 5-stage pipeline with **at least three known-broken steps in 2026-04**:

- **LoRA train on Wan 2.2** — model card warns against this
- **DWpose on anime output** — fails at the perception step (E-13 result)
- **SMPL-X / EasyMocap on anime characters** — same distribution problem

`Wan2.2-Animate-14B` collapses the whole thing:

```
Reference image (Alice) + driving video (someone dancing) → animated Alice video
```

It still doesn't directly produce a **rigged 3D animation asset** (the spec's
explicit deliverable). It produces a **2D animated video**. Whether that's
acceptable depends on a more fundamental question:

### **Is the project's "Animation Asset" 2D or 3D?**

The architecture spec is internally inconsistent on this:

- §3 AC-1: "3D 优先，可 3D→2D 渲染"
- §5.3 Online: combines a 3D rig + animation, projects to 2D pixels
- §7: "视频生成只用于离线侧" — implying video is an intermediate, animation is rigged 3D

But §5.2 ⑦ "Animation Asset" doesn't specify which form ("视频生成 + 动捕提取 + 动作库").

**If animations are rigged 3D**, Wan 2.2 Animate is an **intermediate** —
you still need to get from "2D animated video" to "rigged 3D motion".
This brings you back to the broken DWpose / SMPL-X step, which doesn't
work for anime.

**If animations can be 2D video clips** (e.g., rendered out as sprite
sheets for the PIXI game downstream), Wan 2.2 Animate is **the whole
production line in one step**.

**This is the highest-priority question for the architect to clarify.**
See `ARCHITECT_DECISIONS.md` § 1.

---

## What this E-11 directory will contain after vLLM lets go

Per `tools/run_p1_p4.sh` (`e11()` function), the planned run is:

1. **Wan 2.2 TI2V-5B** (the fits-in-24GB variant) text-to-video, prompt-only,
   to validate the model runs on this hardware at all
2. Then **Wan 2.2 Animate-14B** with reference = Alice expanded set + driving
   video = Mixamo dance FBX rendered as RGB → animated Alice clip
3. Quantitative metrics:
   - Per-frame CLIP-I to ref (consistency across frames)
   - Cross-clip CLIP-I (consistency across separate generations)
   - Aesthetic predictor distribution
   - DWpose extract success rate (we **predict** this will fail; check it does)
   - Hand/face artifact rate (manual annotation, 30-frame sample)
   - VRAM peak, time per second of video

Estimated runtime once GPU is free: **3-4 hours** for both runs at 5 sec each.

## Pre-run risk matrix

| Risk | Probability | Mitigation |
|---|---|---|
| Wan 2.2 5B installation fails on ARM (unknown wheels) | 30 % | Try minimal install first, fall back to Flux + open-source video model |
| Wan 2.2 Animate-14B preprocessor fails on anime input | 40 % | The internal preprocessor may use detectors trained on real photos |
| Output identity drifts severely | 30 % | Train a Character LoRA anyway despite model card warning, for I2V variant only |
| 80 GB requirement for 14B is a hard ceiling | 100 % | Run 5B variant; 14B Animate at 23-50 GB is workable |

## Why HunyuanVideo (E-12) was deprioritized

| Factor | HunyuanVideo | Wan 2.2 |
|---|---|---|
| License | tencent-hunyuan-noncomm | Apache-2.0 |
| Single-GPU VRAM | 60-80 GB at 720p | 24 GB (5B) to 80 GB (14B) |
| Has anime-character variant? | No specific | Yes (Animate-14B) |
| LoRA support | Mature | Discouraged by author |
| Community wheels / weight downloads | Mature | Mature |

**Wan 2.2 Animate is the more interesting model** for our architecture's
specific need (ref-image-driven anime animation). HunyuanVideo's only
clear advantage is "more LoRA tutorials available", which is offset by
the discouragement against LoRA on Wan 2.2 itself.

If the architect wants HunyuanVideo coverage, that's a separate
half-day experiment.

---

## Files (will be populated when run)

- `samples/wan22_5b_t2v_*.mp4` — TI2V-5B sanity output
- `samples/wan22_animate_alice_*.mp4` — Animate-14B with Alice reference
- `samples/per_frame_clip_i.json`
- `samples/hand_face_artifacts.csv`
- `details.md` — full prompt/parameter logs
- `logs/` — terminal output from generate.py
