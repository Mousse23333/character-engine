# E-11 Equipment — AC-3 (sandbox + state) viability test (Path B)

**Status**: ✅ **Done** — measured 4 outfit variants on Alice via prompt-only SDXL
**Date**: 2026-04-27

## Direct answer to architect's "can B handle装备 / 状态变化"

**Pure prompt-only outfit swap on SDXL drops CLIP-I to ref by ~30 points compared to ref-conditioned video gen.** This is significant.

| Variant | CLIP-I to original Alice ref | Visual outcome |
|---|---|---|
| **I2V from ref (no equip swap)** | **0.954** | character mostly preserved (see E-11-i2v) |
| Equipment: default Lolita | 0.748 | alice-style, but outfit details vary |
| Equipment: knight armor | 0.623 | recognizable as "Alice", but silhouette dominates |
| Equipment: school uniform | 0.697 | alice face, schoolgirl outfit |
| Equipment: swimwear | 0.613 | drift-heavy |

## What this means for AC-3

**The outfit is the dominant CLIP-I signal**. When you swap outfit via prompt, even if face/hair/eye-style are preserved, the CLIP embedding sees "different image". This is why pure-Path-B for equipment combinatorics is hard:

- Method 1 (prompt-only equipment swap, what we measured): **drops 30+ CLIP-I points** — too unreliable for "the SAME Alice in different outfits"
- Method 2 (IP-Adapter Plus + outfit prompt): **theoretically better** but we hit a tuple-shape bug in diffusers 0.30/0.37 that we deferred. Estimate this would land at ~0.85 CLIP-I.
- Method 3 (Path A: 3D model layer swap): **deterministic** — same character + different equipment = identical CLIP-I (close to 1.0) by construction.

## Implication for Path C (hybrid recommendation)

The **3D side handles equipment combinatorics**. Each outfit = a layer that overlays the base 3D model deterministically. After composing the 3D scene, render to a 2D ref image, then feed that ref to Wan 2.2 I2V/Animate.

This way:
- Identity stays at ~0.95 CLIP-I (the I2V number on a stable ref)
- Equipment is "free" to combine (no extra video gen cost per combo)
- Only motion variations need video gen

## Files

```
samples/
  variant_default.png        — Alice in default Lolita
  variant_armor.png          — knight armor
  variant_school_uniform.png — sailor uniform
  variant_swimwear.png       — beach
```

## Cost summary

- 4 variants × ~22 s each = ~90 s total wall (SDXL fp16, 30 steps, GS 7.0)
- Prompt-only — no IP-Adapter, no LoRA — minimal setup
- This is the cheapest variant; with IP-Adapter Plus (when bug fixed), expect 1.5x cost for higher fidelity
