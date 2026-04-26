# ARCHITECT_DECISIONS.md — what the investigator recommends

**Audience**: project architect (you).
**Goal**: 5-minute read; concrete decisions you can act on tomorrow.
**Confidence levels**: each section flags **HIGH / MED / LOW** based on the evidence available without GPU access tonight.

> **Caveat**: this report was written under a **GPU-blocking situation** (your vLLM Qwen3-30B held 103 GB of unified memory all night; see `BLOCKING.md`). Five of the heavy experiments (E-05/E-08/E-11/E-12/E-13 GPU portion) could not run. The recommendations below combine **what we did run** (E-00 Real-ESRGAN, OpenPose anime detection, vLLM-as-Judge), **public evidence** (model cards, arxiv, repo READMEs), and **infrastructure analysis** (ARM64 compatibility audit). Where I'm extrapolating instead of measuring, I say so.

---

## 1. Three things to do **this week** (HIGH confidence)

### 1.1 Stop planning for Wan 2.2 LoRA training. Switch to Wan 2.2 Animate-14B as Production Line ⑦.

**Why**:
- Wan 2.2 model card explicitly says "we do not recommend using LoRA models trained on Wan2.2, since weight changes during training may lead to unexpected behavior" (`huggingface.co/Wan-AI/Wan2.2-Animate-14B`).
- Wan 2.2 Animate-14B does **single-image + driving-video → animated character** in one model. This is **directly what Production Line ⑦ wants**, without LoRA training, without DWpose, without retargeting.
- VRAM: 23-50 GB single-GPU (depending on host GPU). On the freed GB10, this is fine.
- License: Apache-2.0.

**Action**:
- Replace E-11 plan ("train Wan 2.2 Character LoRA") with E-11-Animate plan ("ref Alice + driving video").
- Decide: are your "Animation Assets" 2D videos (sprite sheets) or 3D rigged motion clips? **This single question changes the entire production line ⑦** — see § 1.4 below.

### 1.2 Plan the rigging line around UniRig + Hunyuan3D 2.5, **not** UniRig alone.

**Why**:
- UniRig (SIGGRAPH 2025) skinning needs **60 GB single-GPU**. Workable on freed GB10 but expensive.
- The UniRig **Rig-XL/VRoid checkpoint** (the one that's actually trained on anime characters) **is still in preparation** as of the public README. Available checkpoint is Articulation-XL2.0, which is the weaker variant for our use case.
- Hunyuan3D 2.5 (June 2025) **adds rigging support** in the same pipeline that generates the mesh. Plausibly equal or better quality for anime than UniRig Articulation-XL.

**Action**:
- Test Hunyuan3D 2.5's integrated rigging **first** when you free GPU.
- Keep UniRig Articulation-XL as fallback.
- **Wait for** UniRig Rig-XL/VRoid before committing engineering effort.
- Allocate 3-6 weeks engineering for the rigging integration regardless of which backend wins. This is genuinely "open problem" territory (AC-5 is correct).

### 1.3 Replace all "Mixamo SaaS upload" steps in the spec with offline FBX library + Blender retarget.

**Why**:
- Mixamo's **API is a closed SaaS** (Adobe), violating AC-6.
- Mixamo's **FBX library is downloadable for offline use** — that doesn't violate AC-6 (FBX is an open format, downloaded files are local assets).
- The spec's E-09 "上传 Mixamo" wording was written before AC-6 was fully internalized; it's a writing oversight, not a fundamental conflict.

**Action**:
- Edit the spec: `Mixamo` references → `Mixamo offline FBX pack + open-source retargeter (Blender bones / OpenAnim / etc.)`.
- For testing: download 5-10 standard animations (idle/walk/run/wave/jump) once, redistribute internally as part of project asset library.

---

## 2. Two directions to **slow down on or pause** (MED confidence)

### 2.1 Pause: training Style + Identity dual LoRA on SDXL/Illustrious.

**Why**:
- Spec lists this as E-02. It's expensive (200 + 30 image dataset prep, two 1-2 h training runs).
- The decision value is **moderate**: you're testing whether two LoRAs on a strong base model pollute each other. Community evidence (CivitAI, 2025-2026) says they don't, when you weight the IDs separately. This is largely a known-good pattern.
- **Better use of that engineering time**: Asset Contract design (§ 5).

**Counter-argument**:
- If you discover Style and Identity *do* pollute each other for **your** specific case (anime + Alice), you'd want to know. So this is "pause, not kill".

**Action**:
- Mark E-02 as deferred to a future research week, not the next sprint.
- If you have a spare-GPU evening, run a quick PuLID + Style-LoRA combo first — that's 90 % of the way to the same answer for 10 % of the cost.

### 2.2 Pause: extensive HunyuanVideo evaluation (E-12).

**Why**:
- Wan 2.2's Animate-14B variant is **strictly better aligned** with the project's "ref-image-driven anime animation" need. HunyuanVideo doesn't have a comparable variant.
- HunyuanVideo's license (tencent-hunyuan-noncomm) is more restrictive than Wan 2.2's Apache-2.0.
- If Wan 2.2 fails for some reason, *then* re-introduce HunyuanVideo as the backup video model. Not before.

**Action**:
- Drop E-12 from the priority list.
- Note in the spec that HunyuanVideo is a backup, not a competing primary.

---

## 3. Hypotheses (H1-H8) status update

| # | Hypothesis (paraphrased) | Status after this night | Confidence |
|---|---|---|---|
| **H1** | Hunyuan3D 2.0 二次元 mesh after retop is animation-ready | **Untested directly tonight**. Public evidence (e.g., Hunyuan3D 2.5 adding rigging) suggests yes for shape, no for direct rig. | LOW |
| **H2** | Wan 2.2 + Character LoRA stable for character video | **Likely false in spirit.** Model card warns against LoRA training. Use Wan 2.2 Animate-14B instead — that path is plausible. | **MED** (vendor-stated) |
| **H3** | DWpose extracted from generated video can drive retop'd character | **Likely false** for anime output (E-13 finding: DWpose returns 0 keypoints on anime ref). | **HIGH** (direct test) |
| **H4** | UniRig open-source quality good enough for anime humanoid | **Inconclusive — checkpoint not released**. Articulation-XL exists; Rig-XL/VRoid is the one we want. | LOW — wait for ckpt |
| **H5** | Style LoRA + Identity LoRA stack without polluting | **Untested tonight, community evidence says yes**. Defer formal validation. | MED |
| **H6** | Offline-side assets feed online-side composer cleanly | Untestable until the Asset Contract is designed. | N/A — pre-condition |
| **H7** | Online GPU composition latency is game-frame-rate compatible | Out of scope for tonight (online side wasn't part of survey). | N/A |
| **H8** | Equipment skinned-to-character-bones approach handles "one rig drives all gear" | Out of scope tonight. | N/A |

**Top fall-throughs**: H2 needs to be **rephrased** ("Wan 2.2 Animate as primary, not Wan 2.2 LoRA") and H3 needs to be **partially retired** ("AI-generated anime video → DWpose → motion is broken; use direct video model output").

---

## 4. Feedback on the 7 Architectural Constraints (AC-1 to AC-7)

| AC | Original | My recommendation | Reasoning |
|---|---|---|---|
| **AC-1** 3D-first, 3D→2D allowed, no pure 2D | **Keep, but clarify** | The spec is consistent with itself, but the Animation Asset's nature (2D video vs 3D rigged motion) is **not specified**, and that gap forces all of Production Line ⑦ into ambiguity. **Add an explicit sub-constraint: AC-1.1: animation assets are rigged 3D motion clips (not 2D video).** Or accept 2D video as a path, in which case Wan 2.2 Animate is the whole pipeline. |
| **AC-2** Sandbox-extensible pipeline | **Keep as-is** | No evidence to change. |
| **AC-3** Equipment × state space → real-time composition | **Keep as-is** | Online-side, not tested tonight. Architecturally sound. |
| **AC-4** Style and Identity decoupled | **Keep, but acknowledge fragility** | Plausible to maintain on SDXL family (E-02 not run, but community evidence says yes). For video models — UNKNOWN, possibly impossible (Wan 2.2 LoRA is discouraged). The decoupling is a **2D-image-time invariant**, not yet tested in motion. |
| **AC-5** Animation is open problem | **Keep, even more so** | Tonight's E-13 confirms this. The pipeline's weakest link is end-to-end animation. Wan 2.2 Animate offers a partial workaround but doesn't produce 3D rigged motion (see AC-1.1 above). |
| **AC-6** All-open-source, no SaaS | **Keep, but tighten in spec writing** | Spec **violates its own AC-6** in three places (Mixamo upload, AccuRIG inclusion, Flux Kontext as "open"). Recommend rewriting the spec with stricter AC-6 enforcement: every named tool must be open-weights + open-source-license + downloadable + redistributable. **Free-as-in-beer is not enough.** |
| **AC-7** Offline production / online composition split, with Asset Contract | **Keep, and prioritize Asset Contract design above all other architecture work** | This is your single biggest architectural lever. See § 5. |

---

## 5. The biggest piece of architecture work nobody tested tonight

**The Asset Contract.** It's mentioned in §6 of the spec as "the most critical design point — pending detailed design".

**Why it's the single biggest leverage point**:
- It defines the protocol between offline and online sides.
- Once specified, both sides can iterate independently.
- Without it, every production line ① through ⑦ has different output formats and the online side has to handle each as a special case.

**What I would propose** (5-min sketch, not a finished design):

```
Asset = {
  uuid:         UUID v7 (sortable timestamp + random)
  type:         enum {style, identity, body, rig, equipment, modulator, animation}
  version:      semver "1.0.0" — within type
  parent:       UUID | null
  metadata:     dict (each type defines schema)
  payload:      content-addressed blob ref (SHA-256)
  immutable:    true (always; never modify)
  signature:    optional — for trust between offline / online
}

Composition rule (online-side):
  Render(identity_id, style_id, equipment[], state, view_angle) →
    1. Load Identity, Style by id
    2. Resolve equipment[] in load order
    3. Apply state modulators in order (skin/wound/expression/etc.)
    4. Bind animation pose at requested time
    5. Render via Three.js / WebGPU pipeline
```

This is **15 lines of schema** that unblocks 7 production lines.

**Recommended next sprint**:
- Spend 1-2 days writing the Asset Contract YAML schema (one schema per asset type).
- Spend 1 day writing the contract validator (Python `pydantic` model + JSON schema export).
- Spend 1 day writing the "asset producer / asset consumer" interface skeleton.
- Then — and only then — start running the production lines for real.

Without this, the rest of the project is a collection of disconnected experiments.

---

## 6. Things in the spec that need fact-correction

(All five are also documented in `EXECUTIVE_SUMMARY.md` § 0 for visibility.)

1. **"128GB Blackwell B200"** — in reality, NVIDIA GB10 (Grace Blackwell desktop, aarch64), 119.6 GB **unified memory**. Affects every "VRAM × N concurrent" calculation in the spec.
2. **"Flux Kontext open-source"** — Flux Kontext is BFL's API-only product. Open-weights replacement: OmniGen2 (Apache-2.0), or IP-Adapter Plus.
3. **"Mixamo upload"** — closed SaaS, violates AC-6. Use Mixamo's offline FBX library instead.
4. **"Wan 2.2 high/low-noise expert both trained"** — community practice trains only high-noise; model card discourages LoRA training overall.
5. **"AccuRIG 2 as open-source baseline"** — AccuRIG is closed-source (Reallusion). Spec contradicts itself.

---

## 7. What the architect should do tomorrow morning

In rank order, by ROI:

1. **Read this file plus `EXECUTIVE_SUMMARY.md`** (15 minutes total).
2. **Decide AC-1.1 — are Animation Assets 2D or 3D?** This is the keystone decision; everything downstream changes shape based on it.
3. **Decide whether to free GPU** and let the second session run E-05/E-08/E-11/E-13 (Option B in `BLOCKING.md`). If yes, hand the task back: it'll consume another 6-8 hours.
4. **Spend 1 day on Asset Contract schema** (no GPU needed). I gave a 5-line sketch in § 5 — enough to start. This unlocks everything.
5. **Update the spec** to fix the 5 fact-corrections (§ 6) and clarify AC-6 enforcement.
6. **Reschedule the research week** with E-02, E-04 (replaced by OmniGen2), E-07 GPU portion, E-09 (Mixamo offline), E-14 (NPR) deferred to next opportunity.

If you want a single-line answer to "what's the biggest thing I should change":

> **The animation pipeline is broken at the perception step (DWpose can't see anime). Use Wan 2.2 Animate-14B as a single-step replacement, or re-define your animation assets to allow 2D-video form.**

Everything else is consequential, but secondary to that.

---

**Ends.**

> If you want to dispute any of these recommendations: each one cites the
> evidence source (model card, repo README, etc.) in the corresponding
> `E-XX/details.md`. Push back on the weakest evidence — that's how the
> spec gets sharper.
