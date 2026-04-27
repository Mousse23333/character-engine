# Path A — 3D Pipeline (Summary)

**Date**: 2026-04-27 morning session
**Hardware**: NVIDIA GB10, aarch64, 119.6 GB unified

## What ran end-to-end

```
Image (alice_ref 189×267)
   ↓ Real-ESRGAN x4 (yesterday)
Image (756×1068) → squared 1024×1024
   ↓ Hunyuan3D 2.0 shape (65 s, 5.99 GB peak)
Mesh (V=209k F=418k, non-manifold)
   ↓ Hunyuan3D 2.0 paint (198 s, 10.45 GB peak)
Textured GLB (V=327k F=418k, 2048² PBR texture, 16 MB)
   ↓ trimesh quadric decimation (CPU, <1 s)
Retopped tris (5k–50k variants; floor at 19.6k)
   ↓ ❌ UniRig auto-rigging (ARM-blocked)
   ↓ ❌ Blender Rigify (ARM-blocked)
   ↓ ❌ Mixamo retarget (depends on rigging)
Rigged FBX (NOT PRODUCED on this hardware tonight)
```

## Path A — verdict

**The 3D AI side works on ARM64 GB10**. Hunyuan3D 2.0 custom CUDA ops compile and run cleanly. Texturing produces real PBR. Retop is fast. **The traditional rigging side is blocked on ARM** — `bpy`, `open3d`, `spconv` all lack Linux/ARM wheels.

**The bottleneck is open-source rigging tooling, NOT the AI mesh generator.** A single x86 dev box closes this gap.

**Quality** (visual inspection of `E-05/samples/03_alice_textured.glb`): full body Alice mesh, recognizable as anime character with the right outfit, **non-manifold geometry typical of AI mesh generators** — needs retop before rigging. Back-view quality is the typical AI-3D weak spot but acceptable.

**Cost on GB10**: ~5 minutes from input image to retopped mesh. Predictable. Cacheable.

## Sub-experiments

| ID | What | Status | Time | Output |
|---|---|---|---|---|
| E-05 | Hunyuan3D 2.0 mesh + texture | ✅ | 263 s | `samples/03_alice_textured.glb` |
| E-07 | trimesh quadric retop | ✅ | <1 s × 4 targets | 4 OBJ variants |
| E-08 | UniRig auto-rig | ❌ blocked | — | docs only — see `E-08/README.md` |
| E-09 | Mixamo / FBX retarget | ⏸ pending E-08 | — | not run |
| E-14 | NPR shader render | ⏸ Blender ARM-blocked | — | not run |

## What an x86 worker would deliver in 1 day

If an x86 box with Blender 4.x + UniRig + freed GPU is added to the project's infra:

1. UniRig skeleton inference on E-07 retopped mesh (~5 min)
2. UniRig skinning (~10-30 min, 60 GB GPU)
3. Mixamo offline FBX retarget (3 standard animations: idle, walk, wave) (~30 min)
4. Render + export to GLB with armature

End-to-end: ~1 hour (sequential) for first character. Subsequent characters: same cost (no setup amortization needed).

## Files

```
path-A-3D/
├── SUMMARY.md                 — this file
├── E-05-hunyuan3d/            — mesh generation (RAN)
│   ├── README.md
│   ├── details.md
│   └── samples/               — 4 PNGs + obj + glb
├── E-07-retop/                — retopology (RAN)
│   ├── README.md
│   └── samples/               — 3 OBJ variants
└── E-08-rigging/              — auto-rigging (BLOCKED)
    └── README.md              — what would have run + ARM blocker analysis
```
