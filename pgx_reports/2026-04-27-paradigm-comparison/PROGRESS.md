# PROGRESS — Paradigm Comparison Day (2026-04-27) — FINAL

**Started**: 2026-04-27 ~08:00 UTC (after vLLM kill)
**Finished today's session**: 2026-04-27 ~09:40 UTC (final report committed)
**Investigator**: Claude Opus 4.7 (1M context)
**Hardware**: NVIDIA GB10, aarch64, 119.6 GB unified memory

---

## 1-paragraph status (read first)

> **Both paths ran end-to-end on this hardware** (within their respective scopes):
> - **Path A**: Hunyuan3D 2.0 mesh + texture (263s) + trimesh retop (<1s) ✅. UniRig auto-rigging blocked on aarch64 (`bpy`/`open3d`/`spconv` ARM-deps); recoverable on x86 worker.
> - **Path B**: Both Wan 2.2 I2V (23 min, CLIP-I 0.954, low motion) and **Animate-14B (25 min, CLIP-I 0.893, real motion)** ran end-to-end on this aarch64 box, after a 30-line `decord` shim + onnxruntime-CPU patch.
> - **Equipment test**: prompt-only outfit swap drops CLIP-I to 0.61-0.75 — **pure Path B fails AC-3**.
>
> **Recommendation**: AC-0 collapses to **Path C** (3D for identity, 2D video for animation). See `ARCHITECT_DECISIONS.md`.

---

## Detailed timeline

| Time | Event |
|---|---|
| 08:00 | Session start; killed vLLM (PID 11072/11230) → 114 GB freed |
| 08:05 | Read PGX_TASK_ADDENDUM_001.md; new report dir created |
| 08:08 | Wan 2.2 Animate-14B download started in background |
| 08:10-08:25 | Decord shim written; pymeshlab patched; basic test of imports |
| 08:25 | E-05 Hunyuan3D 2.0 inference started |
| 08:32 | E-05 textured.glb saved (263s total: 65s shape + 198s texture, 10.5GB peak) |
| 08:34 | E-07 retop done (<1s × 4 variants) |
| 08:36 | Initial Wan 2.2 I2V started (alice + prompt) |
| 08:38 | I2V model load done; sampling started |
| 08:55 | E-11-equipment SDXL outfit variants completed in parallel |
| 08:59 | I2V finished — 23.2 min total, 1.4 MB MP4 |
| 09:03 | I2V CLIP-I scoring done: mean 0.954 to ref, cross-frame 0.976 |
| 09:08 | E-11-Animate launched with CPU-ONNX patches |
| 09:09 | Animate preprocess succeeded (62s for 106 frames) |
| 09:13 | Animate generation started (after model load) |
| 09:18 | Animate pass 1 (high-noise window 1) finished |
| 09:23 | Pass 2 finished |
| 09:28 | Pass 3 finished |
| 09:33 | **Animate pass 4 finished + MP4 saved (2.4 MB)** |
| 09:35 | Animate CLIP-I scoring: mean 0.893 to ref, cross-frame 0.917 |
| 09:35-09:40 | Final EXECUTIVE_SUMMARY + ARCHITECT_DECISIONS + this PROGRESS |

---

## Commits pushed today

| Hash | What |
|---|---|
| `78658ac` | (architect's commit before session) Add AC-0 + Task Addendum 001 |
| `ae4e4e7` | Path A: E-05 + E-07 end-to-end |
| `3920ff3` | Path A docs (E-07/E-08 READMEs) |
| `2ab8099` | Path B docs (I2V/Animate placeholder READMEs) |
| `d66f9cf` | EXECUTIVE_SUMMARY draft |
| `f8f3ca4` | Path C hybrid sketch |
| `cdfc745` | ARCHITECT_DECISIONS — Path C recommendation |
| `b22ae54` | PROGRESS update |
| `80e3126` | Animate run script (CPU ONNX patch) + I2V output scorer |
| `c2095cf` | EXECUTIVE_SUMMARY: lead with Path C diagram |
| `6a110c1` | Equipment test script |
| `abfb804` | I2V SUCCESS: 23.2 min, CLIP-I 0.954 / 0.976 |
| `297ee1a` | decord shim: get_frame_timestamp |
| `83dcb17` | EXECUTIVE_SUMMARY refined with measured data |
| `8465849` | Equipment test results: 0.61-0.75 CLIP-I prompt-only |
| `2d4c50f` | Animate-14B preprocess SUCCESS (62s) |
| `1f6f74a` | Cleanup stale failure marker |
| `ecc6801` | Path A and Path B summaries |
| `1bf8c20` | Animate-14B END-TO-END SUCCESS 25min, real motion |
| `002e8b1` | Final EXECUTIVE_SUMMARY (both paths measured) |
| `06b9a03` | Final ARCHITECT_DECISIONS (AC-0 → Path C) |

---

## Final task status

| Task | Status | Result |
|---|---|---|
| Setup (kill vLLM, new dir, WORKPLAN) | ✅ | clean start |
| Path A E-05 Hunyuan3D mesh+texture | ✅ | 263s, 10.5GB peak |
| Path A E-07 retop (trimesh) | ✅ | <1s × 4 variants |
| Path A E-08 UniRig | ❌ ARM-blocked | precise blocker list documented |
| Path A E-09 retarget | ⏸ depends on E-08 | n/a |
| Path A E-14 NPR | ⏸ Blender ARM-blocked | n/a |
| Path B E-11 I2V end-to-end | ✅ | 23.2 min, CLIP-I 0.954, low motion |
| Path B E-11-Animate end-to-end | ✅ | 25 min, CLIP-I 0.893, **real motion** |
| Path B E-11-equipment AC-3 test | ✅ | CLIP-I drops to 0.61-0.75 — pure-B fails AC-3 |
| Path C hybrid sketch | ✅ | architectural design committed |
| 9-dim scoring table | ✅ | all 3 paths scored, evidence cited |
| EXECUTIVE_SUMMARY | ✅ | final version with Path C recommendation |
| ARCHITECT_DECISIONS | ✅ | concrete actions + AC feedback |
| RAW_NUMBERS.csv | ✅ | every metric persisted |
| Final commit + push | ✅ | 21 commits today |

---

## Key measurements (the numbers that matter)

```
Path A (3D):
  Hunyuan3D 2.0 mesh+texture:    263 s, 10.45 GB peak GPU
  trimesh quadric retop:         <1 s (CPU), 50k/20k/19.6k variants
  UniRig auto-rig:               BLOCKED on aarch64 (bpy/open3d/spconv)

Path B (2D video):
  Wan 2.2 I2V-A14B:              23.2 min, 33 frames @ 832×480→736×528
    - CLIP-I to ref:             0.954 mean, 0.011 std (very static)
    - cross-frame:               0.976 mean
  Wan 2.2 Animate-14B:           25 min, 106 frames @ 1280×720→624×624
    - CLIP-I to ref:             0.893 mean, 0.025 std (real motion ✓)
    - cross-frame:               0.917 mean
    - preprocess (CPU ONNX):     62 s on aarch64
  SDXL prompt-only equipment:    ~22 s/variant @ 1024², 30 steps
    - CLIP-I to original alice:  0.748 (default), 0.623 (armor),
                                 0.697 (school uniform), 0.613 (swimwear)

Cross-path (the AC-3 question):
  I2V on stable ref (no eq swap):       CLIP-I 0.954
  SDXL with eq swap (no ref):           CLIP-I 0.61-0.75
  → 30-point drop ≈ pure-B fails AC-3
  → Path C answer: do equipment in 3D, then feed rendered ref to video
```

---

## What I won't do this session (and why)

| Item | Why deferred |
|---|---|
| UniRig on x86 worker | not on this hardware tonight |
| NPR shader on 3D mesh | Blender ARM-blocked |
| IP-Adapter Plus equipment swap | tuple-shape bug consumed too much time, deprioritized in favor of Path C |
| Anime driving video for Animate-14B | Wan example was real-human; anime drive is open question for next session |
| 3D→2D ref bridge implementation | architectural sketch in path-C-hybrid; engineering is next-sprint task |

---

## Resource snapshot at session end

```
GPU/unified: ~10 GB used (idle)
Disk:        ~440 GB HF cache / 695 GB total free at start (now ~250 GB free)
HF cache (notable):
  Wan 2.2 Animate-14B:     68 GB (downloaded today)
  Wan 2.2 I2V-A14B / T2V:  118 GB each (yesterday)
  Hunyuan3D 2 + 2.1:       69 GB
  SDXL base:               72 GB (with all variants)
  IP-Adapter family:       24 GB
  Illustrious-XL v1.0:     7 GB (downloaded today)
  Annotators / TRELLIS / etc: ~25 GB
```

All artifacts and reports are at:
`/workspace/character-engine/pgx_reports/2026-04-27-paradigm-comparison/`
and pushed to GitHub `Mousse23333/character-engine` main branch.
