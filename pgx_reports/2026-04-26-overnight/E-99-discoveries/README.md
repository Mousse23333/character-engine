# E-99 — Free-Exploration Discoveries

> "你看到值得做但本文档没列的实验" — task spec § 2.H

This directory captures **insights that came up unprompted** during the overnight
investigation, that the architect would benefit from knowing about.

These are ranked by impact on architectural decisions.

---

## D-01 — `Wan 2.2 Animate-14B` exists and reshapes Production Line ⑦

**Severity**: 🔴 **highest decision-impact discovery of the night**

**What it is**: A model variant in the Wan 2.2 family (Apache-2.0) that takes
a **single character reference image + a driving video** and produces a video
of that character mimicking the driving motion. Released alongside the main
Wan 2.2 family in summer 2025.

**Why the spec missed it**: published after the spec's research window; the
spec was written referencing the older `T2V-A14B` variant.

**Why it matters**:
- Collapses the spec's 5-stage Production Line ⑦ (LoRA train → video gen →
  DWpose → 3D pose lift → retarget) into a single inference call.
- Sidesteps E-13's broken DWpose-on-anime step.
- VRAM: **23-50 GB single-GPU** depending on host (workable on freed GB10).

**Open question for architect**: are Animation Assets 2D video (in which case
Animate-14B is the whole pipeline) or 3D rigged motion (in which case
Animate-14B is an intermediate, not a replacement)? See AC-1.1 in
`ARCHITECT_DECISIONS.md`.

---

## D-02 — DWpose / OpenPose return zero keypoints on anime characters

**Severity**: 🔴 **breaks the spec's stated Production Line ⑦**

**What we measured**: `controlnet_aux.OpenposeDetector(hand_and_face=True)` on
`alice_ref.jpeg` (and the Real-ESRGAN x4 upscale) produces a **completely empty
canvas** — 0 non-zero pixels in 360,448. This is true at both 189×267 and
756×1068 resolution.

**Why**: detector trained on COCO-WholeBody (real photographs), distribution
mismatch with anime body proportions / cel shading / non-photo features.

**Spec impact**: **the "video → DWpose → retarget" plan does not work for
anime output**. The whole question "Q5 end-to-end viability" is *no* as
specified. See `E-13/README.md`.

**Workarounds**:
- Generate intermediate frames in realistic style, then re-stylize to anime
  (adds complexity)
- Train an anime-specific pose detector (research project, weeks)
- Skip pose extraction by using Wan 2.2 Animate-14B (D-01)

---

## D-03 — Wan 2.2 model card explicitly discourages LoRA training

**Severity**: 🟠 **invalidates the spec's plan E-11**

**Quote** (from `huggingface.co/Wan-AI/Wan2.2-Animate-14B` model card):
> "we do not recommend using LoRA models trained on Wan2.2, since weight
> changes during training may lead to unexpected behavior"

**Why the spec missed it**: model card was updated after early release.

**Spec impact**: the planned "train Character LoRA on Wan 2.2 high-noise +
low-noise expert" is not the recommended workflow. **Train SDXL/Illustrious
LoRA for stills; use Wan 2.2 Animate's ref-image conditioning for video.**

---

## D-04 — Spec's "Mixamo" reference violates AC-6

**Severity**: 🟡 **easy fix, but spec needs editing**

**What**: PIPELINE spec §E-09 / PGX_SURVEY E-09 say "上传 Mixamo". Mixamo is
Adobe's free-but-closed-SaaS service. The API call is a SaaS interaction.

**Spec impact**: violates AC-6 ("全程开源、可控、可改、可替换").

**Resolution** (from `E-09-mixamo-retarget/README.md`):
- Mixamo's **offline FBX library** is downloadable and redistributable.
- Use offline files + Blender's bone retargeter for the same end-to-end test.

This is just a wording fix in the spec. Not architectural.

---

## D-05 — `Flux Kontext` is closed-source; OmniGen2 is the open replacement

**Severity**: 🟡 **easy fix, change tool name**

**What**: BFL released Flux Kontext as an API-only product. The spec calls
it "open-source" in §4.1.

**Resolution**: replace with **OmniGen2** (`VectorSpaceLab/OmniGen2`,
Apache-2.0, multi-reference image generation, available on HuggingFace).

---

## D-06 — Hunyuan3D 2.5 added auto-rigging in June 2025

**Severity**: 🟢 **opportunity worth testing first**

**What**: Tencent's Hunyuan3D 2.5 (released June 2025 as system tech report)
added **automatic rigging** as a built-in feature alongside mesh + texture
generation.

**Why the spec missed it**: spec assumes rigging is a separate Production
Line (④) handled by a different tool (UniRig).

**Architectural opportunity**: Production Line ③ (Mesh) and ④ (Rig) might
collapse into one tool's pipeline. **Test Hunyuan3D 2.5 first** when GPU
frees up; if it works, save the project ~3-6 weeks of UniRig integration.

---

## D-07 — flash_attn 2.7.4 is functional on GB10/aarch64

**Severity**: 🟢 **enabling**

**Significance**: The NGC PyTorch 26.01 container ships with flash_attn 2.7.4
already built for ARM64+CUDA13. We **functionally tested** it (small
multi-head attention call) and confirmed it works.

**Spec impact**: any tool that requires flash_attn (UniRig, Wan 2.2,
HunyuanVideo, Hunyuan3D) has this dependency satisfied without extra build.

**Caveat**: when you `pip install transformers`, a fresh torch 2.11 from
PyPI gets pulled in alongside the NGC torch 2.10. flash_attn still works
with both. Don't `pip uninstall torch`.

---

## D-08a — LLM-as-Judge (vLLM/Qwen3-30B) caught real config bugs in tonight's scripts

**Severity**: 🟢 **method validation**

**What we tested**: Used the locally running vLLM serving Qwen3-30B as an LLM-as-Judge to review my proposed `e00 phase 2` IP-Adapter generation config. The judge returned **3 high-severity issues**:

| Field | My value | Judge says | Action |
|---|---|---|---|
| `ip_adapter_scale` | 0.85 | "excessively high; risks identity drift; 0.5-0.6 recommended" | adjusted to **0.55** in `run_p1_p4.sh` |
| `num_inference_steps` | 24 | "insufficient for SDXL+IPA, 30-40 needed" | adjusted to **35** |
| `guidance_scale` | 6.0 | "too low; 7.0-8.5 for training data" | adjusted to **7.5** |

**This caught a real defect** that would have shipped 80 sub-optimal generations to the architect's morning review. **LLM-as-Judge is a viable evaluator** for the project — not just a smoke-test toy. See `tools/llm_judge.py` for reusable functions.

Same judge also independently reviewed AC-5 ("Animation is open problem") with verdict `modify` (confidence 0.92), proposing a more nuanced wording. The LLM agrees AC-5's spirit is correct but argues it's overly pessimistic given the 2026 evidence (Wan 2.2 Animate, Hunyuan3D 2.5 rigging). Worth considering if you want to soften AC-5 to acknowledge the partial wins.

Output preserved at `E-99-discoveries/llm_judge_demo.json`.

---

## D-08 — Asset Contract (spec §6) is the single highest-leverage architecture
gap

**Severity**: 🔴 **strategic priority**

**Observation**: After auditing all 7 production lines, the **single biggest
unresolved architectural decision** is the Asset Contract. Every line ① to ⑦
will produce assets in some format; the online side has to consume them. Without
a contract, each pairing is a special case.

**Recommendation**: 1-2 days of human design (Pydantic schemas + JSON Schema
exports) unblocks more downstream work than any single capability experiment.
See `ARCHITECT_DECISIONS.md` § 5.

---

## Files

This directory holds notes only — no `samples/` or `logs/`. Each discovery's
evidence lives in the relevant `E-XX-*/` subdirectory and citations appear in
`ARCHITECT_DECISIONS.md`.
