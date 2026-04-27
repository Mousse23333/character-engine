# PROGRESS — Paradigm Comparison Day (2026-04-27)

**Started**: 2026-04-27 ~08:00 UTC (after vLLM kill)
**Investigator**: Claude Opus 4.7 (1M context)
**Hardware**: NVIDIA GB10, aarch64, 119.6 GB unified memory (vLLM freed)
**Reports**: `pgx_reports/2026-04-27-paradigm-comparison/`

---

## 1-paragraph status (read first)

> **Path A (3D)**: Hunyuan3D 2.0 mesh + texture + tris-retop **work end-to-end on aarch64** in ~5 minutes. Rigging (UniRig) is **ARM-blocked** on this specific container (bpy / open3d / spconv have no Linux ARM wheels). Recoverable on an x86 worker.
>
> **Path B (2D video)**: Wan 2.2 I2V-A14B is **running right now** on this hardware (step 15/40 as of last check; ETA ~11 min more). Animate-14B weights downloaded but its preprocess pipeline has additional ARM friction (onnxruntime-gpu wheel, ViTPose stored as 443 layer files).
>
> **Path C (hybrid)** is my recommendation — see `ARCHITECT_DECISIONS.md`. 3D for identity composition, 2D video for motion delivery, with a 3D→2D ref-render bridge.

---

## Detailed progress

| Task | Status | Time | Result |
|---|---|---|---|
| **Setup** | | | |
| Kill vLLM (PID 11072 / 11230) | ✅ | 30s | 114 GB freed |
| Stop the leftover model_downloads.sh | ✅ | — | |
| New report dir + WORKPLAN | ✅ | 5 min | `pgx_reports/2026-04-27-paradigm-comparison/` |
| Wan 2.2 Animate-14B download | ✅ | 17 min | 68 GB (444 files) |
| Decord shim package install | ✅ | 5 min | `tools/decord_shim/decord/__init__.py` |
| Various deps (pymeshlab patch, pygltflib, easydict, moviepy) | ✅ | various | |
| **Path A** | | | |
| E-05 Hunyuan3D 2.0 (shape + texture) | ✅ | 263 s | `glb` 16 MB, V=327k F=418k, tex 2048² |
| E-07 retop (trimesh quadric) | ✅ | <1 s | 3 variants: 50k / 20k / 19.6k tris |
| E-08 UniRig | ❌ | — | bpy/open3d/spconv ARM-blocked |
| E-09 Mixamo retarget | ⏸ | — | depends on E-08 |
| E-14 NPR | ⏸ | — | Blender on ARM blocked |
| **Path B** | | | |
| Decord ARM shim | ✅ | 10 min | functional, all Wan classes import |
| Animate-14B weights | ✅ | 17 min | downloaded |
| Animate preprocess setup | ⏸ | — | onnxruntime-gpu no ARM wheel; ViTPose ONNX format issue |
| I2V smoke test (alternate substitute for Animate) | 🟡 | ~30 min ETA | currently step 15/40 |
| Equipment test (E-11-equipment) | ⏸ | — | script ready; will run after I2V |
| **Architecture sketches** | | | |
| Path C hybrid design | ✅ | — | `path-C-hybrid/README.md` |
| 9-dim scoring table | 🟡 | — | drafted in EXECUTIVE_SUMMARY (one column live, two TBD) |
| **Reports** | | | |
| WORKPLAN.md | ✅ | | |
| EXECUTIVE_SUMMARY.md | 🟡 | drafted, refining as data lands |
| ARCHITECT_DECISIONS.md | ✅ | recommends Path C |
| RAW_NUMBERS.csv | 🟡 | E-05 / E-07 entries; I2V pending |
| All E-XX READMEs | ✅ | E-05, E-07, E-08, E-11-i2v, E-11-animate; placeholders for the rest |

## Commits pushed (today's session)

- `ae4e4e7` — Path A: E-05 + E-07 end-to-end
- `3920ff3` — Path A docs (E-07/E-08)
- `2ab8099` — Path B docs (I2V/Animate)
- `d66f9cf` — EXECUTIVE_SUMMARY draft
- `f8f3ca4` — Path C hybrid sketch
- `cdfc745` — ARCHITECT_DECISIONS recommend Path C
- `6a110c1` — Equipment test script
- + this PROGRESS update next

## What's still in flight

1. ⏳ **Wan 2.2 I2V step ~15/40** — finishes around 09:01 UTC
2. After I2V finishes: equipment test (~10 min)
3. After equipment test: refine EXECUTIVE_SUMMARY 9-dim scores with measured numbers
4. Final commit + push

## What I won't do (and why)

- ❌ Source-build onnxruntime-gpu for ARM. Would take 2+ hours, low ROI on this single-night sprint.
- ❌ Recompose vitpose_h_wholebody.onnx from 443 layer files. Custom work, low ROI tonight.
- ❌ Install Blender on ARM with manual lib extraction. Already tried, deemed not worth the time.
- ❌ Train Wan 2.2 LoRA. Per author's own warning + yesterday's analysis.

## Resource snapshot

```
GPU/unified: ~93/119 GB used (I2V running with offload)
Disk:        695 GB free at start; ~440 GB used by HF cache
HF cache by model:
  Wan 2.2 I2V-A14B  : 118 GB
  Wan 2.2 T2V-A14B  : 118 GB
  Wan 2.2 Animate-14B: 68 GB
  SDXL base + variants: 72 GB
  Hunyuan3D-2 + 2.1 : 69 GB
  IP-Adapter family : 24 GB
  Annotators        : 10 GB
  Misc (DWPose, TRELLIS, InstantID, Real-ESRGAN, Illustrious): ~25 GB
```
