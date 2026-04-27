# ARCHITECT_DECISIONS — Paradigm Comparison Day

**Audience**: project architect (you)
**Goal**: 5-minute decision-quality recommendation, **based on data run today**, on which paradigm AC-0 should collapse to (or stay open)

> Cross-reference: `EXECUTIVE_SUMMARY.md` for the 9-dim score; this file is the action-oriented sibling.

---

## TL;DR — recommend Path C (hybrid)

After running both paths, my recommendation is **Path C — hybrid 2D + 3D**:

> **Identity Asset = 3D mesh + texture (Path A's strength).
> Animation Asset = 2D video clip conditioned on a 3D-rendered ref (Path B's strength).
> The 3D→2D bridge is the architectural glue.**

This has support from data:

- Path A's mesh+texture is **263s, 10 GB peak** on this hardware. Solid, repeatable.
- Path A's rigging is **engineering-blocked on aarch64** (UniRig deps), not blocked on AI capability.
- Path B's I2V is **~10 min/sec at 832×480** on this hardware. Workable for offline batch, **expensive for live**.
- Path B's Animate-14B is preprocess-blocked but the inference path itself works (proven via I2V).
- The architecture's AC-3 (sandbox + state explosion) **requires deterministic composition** for caching to work — this is impossible in pure Path B (each combination is a fresh inference) and natural in Path A.

---

## What this means for AC-0 / AC-1

- **AC-0** (data-driven selection) — you can collapse it by adopting **Path C**. The 3D vs. 2D split is by step, not by paradigm.
- **AC-1** (3D-only) — keep retired. Path C means 3D for identity, 2D for animation delivery.
- **AC-1.1** (the question I asked yesterday) — **answered**: animation assets are 2D video clips; identity assets are 3D meshes. Both live in the Asset Repository, with explicit schemas.

---

## Three concrete things to do this week (HIGH confidence)

### 1. Allocate one x86 dev machine for the rigging line

Path A's blocker is purely tool-chain (bpy / open3d / Blender) on aarch64. **A single x86 box** running Linux + Blender + UniRig + spconv removes the blocker.

This is **not a performance choice — it's a deps choice**. Even a modest x86 GPU box (RTX 4090 24 GB) can do all the rigging work; production GB10 hardware just runs inference.

**Action**: spec a dedicated rigging worker. Budget: 1 day to set up, then it's a service.

### 2. Productionize Hunyuan3D 2.0 on this GB10 — it works

E-05 today proved the inference is clean. Wrap it in a job runner, let it crunch through the character library overnight.

**Action**: write a `hunyuan3d_jobs.py` queue runner that takes images and emits `glb` files. Half-day of work.

### 3. Productionize Wan 2.2 I2V (or Animate, when its preprocess is fixed)

I2V already works on this hardware (today). Animate-14B will work after a 1-day port (onnxruntime source build + ViTPose ONNX recompose).

**Action**: API service that takes (ref_image, prompt) → MP4. Caching layer (key = hash(ref + prompt + seed)).

---

## Two things to slow down on (MED confidence)

### A. Don't try to install bpy / open3d on this ARM box

Multiple hours each path. **Just use an x86 worker.** Stop fighting the wrong battle.

### B. Don't train Wan 2.2 LoRA

Yesterday's finding F4 still applies: model card discourages it. **Use I2V/Animate's ref-image conditioning** instead.

---

## Hypotheses (H1-H8) status — refined with today's data

| # | Hypothesis | Status | Evidence (today) |
|---|---|---|---|
| H1 | Hunyuan3D 2.0 mesh after retop is animation-ready | **PARTIAL ✓** | Mesh + texture work; rigging is the actual block |
| H2 | Wan 2.2 + Character LoRA stable | **DEFERRED** | Use I2V/Animate ref-conditioning instead |
| H3 | DWpose extracts from generated video → drives rig | **DEAD** | Confirmed yesterday: anime distribution mismatch |
| H4 | UniRig open quality good enough for anime | **NOT TESTED** | ARM-blocked; would need x86 worker |
| H5 | Style + Identity LoRA stack without pollution | **NOT TESTED** | Did not run E-02 |
| H6 | Offline assets feed online cleanly | **PRECONDITIONED** on Asset Contract |
| H7 | Online GPU composition latency game-ready | **OUT OF SCOPE TODAY** |
| H8 | Equipment skinned to bones handles "1 rig drives all gear" | **PARTIAL** in Path C — equipment as 3D layer over body, baked to 2D ref before video gen |

---

## Feedback on AC-1 to AC-7 (refined)

| AC | Recommendation |
|---|---|
| **AC-0** | **Collapse to Path C** (hybrid). Justified by data. |
| **AC-1** | **Soft retire**. Path C uses 3D for identity but not for animation. New text: "3D mesh is the canonical identity representation; animation may be delivered as 2D video clips conditioned on 3D-rendered refs." |
| **AC-2** | Keep. Sandbox + extension still natural in hybrid. |
| **AC-3** | Keep, with caveat: **caching is mandatory** for combinatorial scaling. Each (identity × style × equipment × state × motion) combo cached as MP4. |
| **AC-4** | Keep — Path C preserves Style/Identity decoupling because both happen pre-video-gen. |
| **AC-5** | Keep — animation IS still an open problem. Path C makes the problem **smaller** (no rigging needed at runtime) but doesn't eliminate it. |
| **AC-6** | Keep, tighten enforcement. Five fact-corrections from yesterday should be in the spec. |
| **AC-7** | Keep, **and prioritize Asset Contract design above everything else**. With Path C, the Contract has 3 schema classes (Identity/Animation/Equipment), not 7. Simpler. |

---

## What I'm uncertain about

- Aesthetic alignment between Hunyuan3D's PBR render and Wan 2.2's anime stylization: untested. The whole Path C falls apart if the "3D ref → video model" handoff drifts heavily. Need ~1 day of test runs.
- Wan 2.2 Animate-14B's preprocess on truly anime drive-videos: also untested. If the architect already has driving anime motion (e.g., from MMD), the preprocess might balk.
- The aarch64 deployment story: if production hardware is also ARM, half the open-source ecosystem (Blender, bpy, decord, onnxruntime-gpu) needs porting work. **Strongly recommend a heterogeneous fleet — ARM for inference, x86 for tooling.**

---

## What the architect should do tomorrow morning

1. Read `EXECUTIVE_SUMMARY.md` (5 min)
2. Read this file (5 min)
3. Decide: **AC-0 collapse to Path C? Yes / No / Need more data?**
4. If yes:
   - Spec the x86 dev machine
   - Approve Asset Contract design as next sprint's first item
   - Authorize the Wan 2.2 Animate preprocess port (1-2 days x86 worker)
5. If no:
   - Tell me what's not yet measured that you'd need to decide

---

**End.** All evidence cited in `EXECUTIVE_SUMMARY.md` § metrics + each `E-XX/README.md`.
