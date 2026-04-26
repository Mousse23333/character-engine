# E-08 — Details

## Tools surveyed and disposition

| Tool | License | ARM64 | VRAM | Run tonight | Why/why not |
|---|---|---|---|---|---|
| UniRig (skeleton) | Apache-2.0 | unknown | small | ❌ | needs Python 3.11 + spconv (no ARM wheels likely) + freed GPU |
| UniRig (skinning) | Apache-2.0 | unknown | **60 GB** | ❌ | both above + ≥ 60 GB free |
| Hunyuan3D 2.5 (built-in rig) | Apache-2.0 | high risk | shape: 6 GB | ❌ | E-05 prereq blocked; custom CUDA op ARM untested |
| HumanRig | research | unknown | unknown | ❌ | low community traction; not pursued |
| ASMR | research | unknown | unknown | ❌ | same |
| Blender Rigify | GPL | n/a | CPU | ❌ | no Blender on ARM container (libX11 missing) |
| AccuRIG 2 | **closed** | n/a | n/a | ❌ | violates AC-6, excluded |

## Reading guide for the architect

If you skim only one resource: **the UniRig README's "Limitations" section** at <https://github.com/VAST-AI-Research/UniRig>.
The 60 GB skinning quote is in there. So is the "Rig-XL/VRoid checkpoint still in preparation" note.

## Environmental dependencies for UniRig (when running on x86 / freed ARM box)

```bash
# Python 3.11 (uv installed it, see ENVIRONMENT.md)
uv venv unirig-env --python 3.11
source unirig-env/bin/activate
uv pip install torch torchvision  # NGC torch is 2.10; UniRig needs 2.1.1+, OK
uv pip install -r UniRig/requirements.txt  # may include flash_attn — we have it from NGC

# These are the risky ones on ARM:
uv pip install spconv-cu120         # may fail; check spconv-cu130 or compile from source
uv pip install torch-scatter torch-cluster   # may need source build with TORCH_CUDA_ARCH_LIST=12.0
```

## On the Spec's "AccuRIG vs UniRig" framing

The architecture spec section 9 lists AccuRIG as "闭源" (closed-source) and the
PGX survey section E-08 puts it as a baseline alongside UniRig. **These two
positions are inconsistent.** AccuRIG is free, but it is not open-source and
not redistributable — it's a Reallusion product. Including it as a "baseline"
implies running it; doing so violates AC-6.

I excluded AccuRIG from this analysis. This is not a deficit in the analysis —
it's a deficit in the spec consistency, and the architect should **decide
explicitly** in `ARCHITECT_DECISIONS.md` § AC-feedback whether to:
- (a) drop AccuRIG mentions entirely (pure AC-6),
- (b) accept AccuRIG as a quality reference even though we never ship with it
  (loosened AC-6, "free-as-in-beer baseline"), or
- (c) reword AC-6 to "no closed-source in production pipeline" (allowing
  closed-source for benchmarking only).

I recommend **(a)**. The pipeline does not need AccuRIG comparisons — UniRig +
Blender Rigify span the open-source design space. AccuRIG would be a
distraction during architecture phase.

## A note on what "open-source rigging" actually means in 2026

Three things are commonly conflated:

1. **Open-weight model** (Apache-2.0 / MIT / etc.) — UniRig has this.
2. **Open-source training data** — Articulation-XL2.0 is mostly open; VRoid is
   licensed but redistributable.
3. **Open-source pipeline / workflow** — UniRig's inference code is open. The
   integration with Blender for skinning paint, rig editing, animation export
   — that's mostly community / individual-team code, not first-party.

The architecture's AC-6 is satisfied at level 1 (model). Whether you also need
2 and 3 is a separate decision. For "we can build on top of this without
permission", level 1 is enough. For "we want to retrain on our own data", you
need level 2.

## What I would write a thin Python wrapper around (after vLLM frees up)

A clean abstraction over the three tracks:

```python
class Rigger:
    def __init__(self, backend: str):  # 'unirig' | 'hunyuan3d_25' | 'rigify'
        ...
    def rig(self, mesh_path: Path) -> RiggedAsset:
        ...
```

About 400 LoC for the dispatcher + per-backend adapters. Not a research
project. **The architectural design** (4-tuple of (skeleton, skinning_weights,
bind_pose, blendshapes) as RiggedAsset schema) **is** the architecture work
that needs human design — see ARCHITECT_DECISIONS.md § Asset Contract advice.
