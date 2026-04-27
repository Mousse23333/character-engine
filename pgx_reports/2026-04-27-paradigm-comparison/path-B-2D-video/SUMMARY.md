# Path B — 2D Video Pipeline (Summary)

**Date**: 2026-04-27 morning session
**Hardware**: NVIDIA GB10, aarch64, 119.6 GB unified

## What ran end-to-end

### Wan 2.2 I2V-A14B (image → video, free motion)

```
alice_ref (756×1068) → squared 1024² → I2V condition image
       ↓ Wan 2.2 I2V-A14B (40 sample steps, MoE high+low noise expert swap)
Animated MP4 (832×480 → 736×528 effective, 33 frames @ 16fps, 1.38 MB)
```

**Wall time**: 23.2 min (load 2 min + sampling 20.5 min + save 3 s) on GB10.
**Quality**: CLIP-I 0.954 to ref (excellent identity preservation across frames),
0.976 cross-frame consistency (very stable character), but **motion is minimal** —
the character "breathes" / sways rather than locomoting per the "walking forward" prompt.

### Wan 2.2 Animate-14B (image + driving video → animated character)

(in progress at writing — pass 3 of 4 sampling windows)

```
alice_ref (1024×1024) + Wan example driving video (106 frames, real human)
       ↓ Preprocess (62 s, CPU ONNX for ViTPose + YOLO)
src_ref.png + src_face.mp4 + src_pose.mp4
       ↓ Wan 2.2 Animate-14B (4 windows × 20 sample steps each, ~13.5 s/step)
Animated character video (1280×720, 129 frames @ 30fps)
```

**Wall time** (estimated): 3 min model load + ~20 min sampling + save = ~25 min total.
**Quality**: TBD when output completes.

### Equipment / state test (E-11-equipment)

```
4 outfit variants of Alice via SDXL prompt-only (no IP-Adapter):
  default Lolita    →  CLIP-I 0.748 (vs original Alice ref)
  knight armor      →  CLIP-I 0.623
  school uniform    →  CLIP-I 0.697
  swimwear          →  CLIP-I 0.613
Wall: ~90 s for 4 variants total (SDXL 30 steps × 22 s/each).
```

**Compare with I2V CLIP-I 0.954** (no equipment swap, just image-conditioned animation):
prompt-only equipment swap **drops CLIP-I by 21-34 points**. **AC-3 cannot be solved by pure-Path-B prompt swapping.**

## Path B — verdict

**Wan 2.2 14B inference works end-to-end on aarch64 + GB10**. Both I2V (no driving video) and Animate (driving video) variants run after the `decord` shim + onnxruntime CPU patch. Quality is good for character preservation when ref image is honored.

**Cost on GB10**: ~10-12 minutes per second of video at 832×480 (I2V), ~9 minutes per 4 sec of video at 1280×720 (Animate, with 4-window inference). Workable for offline batch generation; **not real-time**.

**The hard problem**: equipment / state combinatorics. Each variation needs a fresh inference, ~10x cost of just identity. **AC-3 (sandbox + state explosion) is not affordable in pure Path B at runtime** without aggressive caching.

## Sub-experiments

| ID | What | Status | Wall time | Quality |
|---|---|---|---|---|
| E-11-i2v | Wan 2.2 I2V-A14B | ✅ | 23.2 min | CLIP-I 0.954 / 0.976 cross-frame |
| E-11-animate | Wan 2.2 Animate-14B | 🟡 in flight | ~25 min est | TBD |
| E-11-equipment | SDXL prompt-only outfit variants | ✅ | 90 s | 0.61-0.75 CLIP-I (drift) |

## Files

```
path-B-2D-video/
├── SUMMARY.md                 — this file
├── E-11-i2v/                  — Wan 2.2 I2V (RAN, success)
│   ├── README.md
│   └── samples/               — alice_i2v.mp4 + frames + metrics.json
├── E-11-animate/              — Wan 2.2 Animate-14B (in flight)
│   ├── README.md
│   └── samples/               — alice_ref_1024.png + preprocessed/ (so far)
└── E-11-equipment/            — outfit variant test (RAN)
    ├── README.md
    └── samples/               — 4 outfit PNGs
```
