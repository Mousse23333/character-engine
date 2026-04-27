# E-08 — Auto-rigging (Path A, step 3)

**Status**: ❌ **BLOCKED on this hardware** (specific Python deps unavailable on aarch64)
**Date**: 2026-04-27

## Direct answer to architect's Q2 (still: "Is open-source rigging really unusable, or just engineering-incomplete?")

**Engineering-incomplete, with a precise list of what's missing on aarch64**:

| Open-source rigger | Status on this GB10/aarch64 box | Estimated work to unblock |
|---|---|---|
| **UniRig** (SIGGRAPH 2025) | ❌ Hard-blocked: `bpy==4.2` no Linux ARM wheel; `open3d` no Linux ARM wheel; `spconv-cu120` no cp312 wheel | 1-2 days to write trimesh-based shim + spconv source build |
| **Hunyuan3D 2.5 integrated rigging** | ❓ — repo doesn't expose rigging in 2.0 install; need to wait for separate 2.5 release / verify which weights ship rigging | unknown until tested |
| **Blender Rigify** (manual) | ❌ no Blender on this container (libX11 missing, no sudo); bpy PyPI no Linux ARM wheel | needs x86 Blender worker |
| **AccuRIG** | ❌ closed-source, violates AC-6 | excluded |

## What we did try tonight

1. ✅ Cloned UniRig repo
2. ✅ Installed all UniRig deps **except** bpy + open3d + spconv (precisely identified blockers)
3. ✅ Confirmed `from src.model import *` loads (the deep net code itself is clean Python)
4. ✅ Built `torch_scatter` from source on ARM (succeeded, v2.1.2)
5. ✅ Patched Hunyuan3D `pymeshlab` (libharfbuzz blocker on related path) — proves the same pattern of patching UniRig is feasible
6. ❌ Did NOT run UniRig inference because of the 3 missing deps above

## What an x86 worker would do today

Given a 1-machine x86 setup with Blender + free GPU:

```bash
git clone https://github.com/VAST-AI-Research/UniRig
cd UniRig
pip install bpy==4.2 open3d  # works on x86
pip install spconv-cu120 torch_scatter torch_cluster
pip install -r requirements.txt

# Inference (assuming we have alice_retop_19600f.obj from E-07):
python launch/inference/skeleton.py \
    --input ../pgx_reports/2026-04-27-paradigm-comparison/path-A-3D/E-07-retop/samples/alice_retop_19600f.obj \
    --output alice_skeleton.npz

# Skinning (requires 60 GB GPU):
python launch/inference/skin.py \
    --input alice_retop_19600f.obj \
    --skeleton alice_skeleton.npz \
    --output alice_rigged.fbx
```

Total estimated time on a freed-GPU x86 box: ~10-15 minutes for skeleton + ~15-30 min for skinning (depending on Articulation-XL2.0 ckpt vs Rig-XL).

## Quality forecast (without a measured run)

Based on community evidence + UniRig README + the `Articulation-XL2.0` ckpt available (vs the unreleased `Rig-XL/VRoid`):

- **Skeleton placement**: likely **acceptable for biped humanoids**. Anime characters with standard proportions OK; wide skirts / asymmetric outfits will confuse it.
- **Skinning weights**: variable. The training set (Articulation-XL) is broad/general — anime-specific weights will be smoother once Rig-XL/VRoid drops.
- **Animation drive-ability**: Mixamo-class skeleton mapping should work; bone naming follows their convention.

## Path A status after E-08

Path A **stops here on this hardware**. We have:
- ✅ Mesh (E-05)
- ✅ Retop (E-07)
- ❌ Rigged character (E-08)

To complete path A end-to-end we need either:
1. An x86 worker to run UniRig + Blender retarget
2. Wait for Hunyuan3D 2.5 rigging weights to be testable on ARM (untested today)
3. Several days of engineering to port UniRig's runtime to ARM

**Architectural conclusion**: open-source rigging IS possible, but **not on a closed ARM-only setup**. This affects deployment strategy if the production hardware is ARM (e.g., Jetson edge boxes).

## Files

```
(no samples — ARM-blocked at this step)
```
