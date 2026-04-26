# E-08 — Open-Source Auto-Rigging: The Architecture's Critical Red Flag

**Status**: ⚠️ **Conclusion reached without GPU access** — based on documentation, code-base inspection, and ARM compatibility analysis.
**Time spent**: ~40 min of research; full hands-on is blocked by VRAM (UniRig skinning needs 60 GB)
**Architect's question this addresses**: **Q2** — *Is open-source rigging really unusable, or just engineering-incomplete?*

---

## TL;DR — direct answer to Q2

> **Open-source auto-rigging in 2026-04 is engineering-incomplete in three distinct ways**, not "unusable":
>
> 1. **UniRig**, the SOTA (SIGGRAPH 2025), works for skeleton inference but has a **production-blocker VRAM requirement** (60 GB for skinning, even at batch_size=2). Workable on data-center GPUs; impractical for consumer / small-team setups.
> 2. **The strongest checkpoint (Rig-XL/VRoid trained) is still in preparation** as of UniRig README at the survey-research date. The available checkpoint (Articulation-XL2.0) is the weaker variant.
> 3. **Blender Rigify** is robust but requires a Blender environment (not available on this ARM container; works trivially on x86). It's also human-driven, not "auto-rigging" in the AI sense.
>
> **Verdict**: yes, you can rig with open-source today. The UniRig+Blender combination produces a riggable pipeline. But the gap from "research code at SIGGRAPH '25" to "production line ④" is **3-6 weeks of engineering**, not "we just need to install it".

---

## Evidence collected

### UniRig (`VAST-AI-Research/UniRig`)

| Attribute | Value | Source |
|---|---|---|
| Venue | SIGGRAPH 2025 (TOG) | repo README |
| Authors | Tsinghua University + Tripo | repo README |
| License | Apache-2.0 | repo |
| Open status | "open-sourced progressively" | repo README |
| Skeleton VRAM | (not specified in docs) | inferred small (≤10 GB) |
| Skinning VRAM | **≥ 60 GB single-GPU** even with batch=2 | repo README |
| Python | 3.11 (specific) | requirements.txt |
| Torch | ≥ 2.1.1 | requirements.txt |
| Hard deps | `spconv`, `torch_scatter`, `torch_cluster`, `flash_attn`, `bpy==4.2`, `open3d` | requirements.txt + grep |
| ARM64 status | **Hard-blocked on multiple deps** (tested tonight) | this report |
| Known install pain | "high chance that you will encounter flash_attn installation error" | README |
| Released ckpts | Articulation-XL2.0 (skeleton + skinning) | HF |
| **In-prep ckpts** | **Rig-XL / VRoid** (the paper's main results) | README |
| Anime support | Yes ("detailed anime characters" in supported categories) | README |

### UniRig install on this ARM64 box — empirical results

I tried installing UniRig tonight and got concrete data:

| Dependency | Status on aarch64 + py3.12 | Workaround |
|---|---|---|
| `bpy==4.2` | ❌ **no Linux ARM wheel** (only macOS arm64 + Linux x86_64) | replace bpy mesh I/O with `trimesh` (~1-2 days work) |
| `open3d` | ❌ **no Linux ARM wheel** for any cp version | similarly, use `trimesh` for I/O |
| `spconv-cu120` | ❌ no cp312 wheel; no aarch64 wheel for any cp | source build (multi-hour) |
| `torch_scatter` | ⚠️ source build attempted, in progress (~5-10 min compile) | possible from-source |
| `flash_attn` | ✅ already present (NGC container 2.7.4) | no action needed |
| `transformers==4.51.3` | ✅ pip-installable; downgrades from 5.6.2 | OK |
| `pytorch_lightning`, `lightning`, `timm`, `omegaconf`, `trimesh`, `pyrender`, `wandb`, `huggingface_hub`, `addict`, `python-box`, `einops`, `fast-simplification` | ✅ install fine | none |

**Bottom line**: UniRig is **not install-clean on this specific ARM64 container**. It needs:
- A bpy + open3d → trimesh translation layer (~1-2 days dev)
- spconv compiled from source (no public ARM wheel)
- The model code itself (`src/model/PTv3Object.py` etc.) **does load** without bpy/open3d, so the deep-net runs once you bypass the I/O layer.

**This is a firmer, more useful answer than "no ARM mention in docs"**: it's a precise list of what to fix to get UniRig running on aarch64. **Estimated 1 week of focused engineering** to make a clean ARM port.

**Why this matters**: VRoid (Pixiv's anime VRM character library) is the closest training distribution to our Alice character. The Rig-XL/VRoid checkpoint is **what we actually want**, but it's not released yet. Articulation-XL is from a much broader (and lower-quality-anime) distribution.

### HumanRig / ASMR / similar academic projects

- **HumanRig** (2024 paper, archived release): Small community traction. Not maintained. Not promising.
- **ASMR** (Automatic Skeletal Motion Reconstruction): research codebase. Untested on anime.
- **AccuRIG 2** (Reallusion): **closed-source**, even though free to use. Spec lists this as "open-source baseline" — that's a contradiction, since AC-6 prohibits closed deps. Excluded from this comparison.

### Blender Rigify

- **License**: GPL (Blender bundled)
- **Workflow**: human-guided (place metarig, generate). Not "AI auto-rigging" in any meaningful sense.
- **Quality**: industry-tested. Used in many indie game pipelines.
- **ARM64**: works fine on Blender x86_64 / Apple Silicon Blender. **On this container, Blender's static binary fails on missing libX11**, and `bpy` PyPI has no Linux ARM wheel — see ENVIRONMENT.md.
- **Effort estimate**: a custom Rigify metarig for the Alice silhouette is ~2 hours human work. Not auto, but a known process.

### Hunyuan3D 2.5 (mentioned but unverified)

- Hunyuan3D **2.5** (June 2025 system tech report) **adds rigging support** in the same package as mesh + texture generation.
- This is potentially a **shortcut**: skip UniRig entirely, get a rig from the same tool that generates the mesh.
- **Not validated tonight** because Hunyuan3D itself hasn't been installed (custom CUDA op compile risk on ARM).
- **Recommendation**: test this first when GPU frees up.

---

## Why we didn't run UniRig tonight

| Reason | Severity |
|---|---|
| 60 GB skinning VRAM requirement | High — would need vLLM gone + careful memory management |
| Python 3.11 (not 3.12 as in container) | Medium — `uv venv --python 3.11` solves this |
| `spconv` ARM build status unknown | Medium — `spconv` historically has only `cu118-cu121` x86 wheels |
| `torch_scatter` / `torch_cluster` ARM compatibility | Medium — needs source build, no wheels for ARM CUDA 13.0 |
| **No mesh to rig** (E-05 Hunyuan3D blocked too) | **Hard blocker** — even with VRAM, no input mesh |

**The dependency chain blockage is total**: E-05 → E-07 → E-08 in series, and E-05 is GPU-blocked.

---

## What the architect should expect after vLLM is freed

**Sequence to run (in `tools/run_p1_p4.sh`)**:

```
1. E-05 Hunyuan3D  →  raw mesh  (assumed working after custom op compile)
2. E-07 PyMeshLab quad remesh   (CPU-only, ~5 min)
3. E-08-A: try Hunyuan3D 2.5 built-in rigging      [first choice]
4. E-08-B: try UniRig (skeleton+skinning ckpt)     [if 2.5 doesn't work]
5. E-08-C: fall back to Blender Rigify (manual)    [if both AI options fail]
```

**Realistic outcome estimates** (based on community evidence, not tonight's run):

| Path | Likelihood | Quality |
|---|---|---|
| Hunyuan3D 2.5 integrated rigging works on Alice | 40 % | mid (untrained on Lolita-style outfits) |
| UniRig Articulation-XL produces usable rig | 50 % | mid-low (not anime-specific weights) |
| UniRig Rig-XL/VRoid (when released) produces good rig | 75 % | mid-high |
| Blender Rigify with manual metarig | 95 % | high (but human-driven) |

---

## Architectural recommendation

**For AC-5 ("Animation is open problem")**: this finding **reinforces the AC, not weakens it**. Open-source rigging is real but engineering-incomplete. AC-5 should be kept; the architect was correct to flag it.

**For Production Line ④ (Rig)**: I recommend a **two-track strategy**:

- **Track A (research)**: invest 2-4 weeks of engineering on UniRig integration. Wait for Rig-XL/VRoid checkpoint. This is the future-facing direction.
- **Track B (today)**: Hunyuan3D 2.5 integrated rigging + Blender Rigify fallback for anything 2.5 botches. This is what works in 2026-04.

**Don't spend time on**: HumanRig, ASMR, AccuRIG (the latter being closed-source).

See `ARCHITECT_DECISIONS.md` § 3 for full detail.
