# E-05 — Hunyuan3D 2.0 mesh + texture on Alice ref (Path A, step 1)

**Status**: ✅ **End-to-end success on GB10 / aarch64**
**Time**: 263s total (4.4 min)
**Date**: 2026-04-27

## Numbers

| Stage | Time | GPU peak | Output |
|---|---|---|---|
| Background removal (rembg / u2net) | 56s | <1 GB | `00_alice_rembg.png` |
| Square + resize 1024² | <1s | — | `01_alice_input_1024.png` |
| Shape generation (Hunyuan3D-DiT) | **65 s** | **5.99 GB** | `02_alice_shape.obj` (V=209k, F=418k) |
| Texture generation (Hunyuan3D-Paint) | **198 s** | **10.45 GB** | `03_alice_textured.glb` (V=327k after UV seams, F=418k, texture 2048²) |
| **Total** | **~263 s** | **10.45 GB** | textured GLB ready for retop |

## Findings

### Hunyuan3D 2.0 install on ARM/GB10 — answers from this run

| Item | Result |
|---|---|
| `custom_rasterizer` CUDA op | ✅ compiled clean (sm_120, CUDA 13.1) |
| `mesh_processor` C++ op | ✅ compiled clean |
| `pymeshlab` | ❌ blocked by `libharfbuzz.so.0` (no sudo) — **mocked out** as the `MeshSimplifier` postprocessor is optional |
| `pygltflib` | ✅ pip install OK |
| Background remover (rembg/u2net.onnx) | ✅ auto-downloads on first use, runs on CPU (no ARM GPU issue) |
| Mesa libGL via Blender bundle | ✅ workaround for missing system libGL |
| Inference end-to-end | ✅ both shape and texture |

### Mesh quality (subjective + raw stats)

- **Vertex count 209k → 327k after UV seams**: typical "AI mesh" density. Way too dense for animation use; needs retop.
- **Watertight: NO**, **manifold: NO**: typical AI-mesh issue. Most retoppers (Instant Meshes, QuadriFlow) handle non-manifold input fine.
- **Bounds**: ~[0.81, 1.99, 0.67] — character is upright, ~2 units tall, ~33% wider than thick.
- **Texture**: 2048×2048 PBR via Hunyuan3D-Paint. Visual quality TBD pending render.

### Architectural takeaways

1. **Hunyuan3D 2.0 is install-clean on GB10 once you patch around `pymeshlab`** (blocked by libharfbuzz on this container; mocked the symbol). That's a reproducible recipe.
2. **End-to-end inference cost is low-end of practical (4.4 min)** at the default settings. Plenty of headroom on 119 GB unified memory for batching multiple subjects.
3. **The mesh out is NOT animation-ready** (non-manifold, 400k tris). E-07 retop is mandatory before anything else in path A.
4. **Path A step 1 is "live"** — does not block path A. Moves the bottleneck downstream to retop and especially rigging (E-07 / E-08).

## Files

```
samples/
  00_alice_rembg.png         — input after bg removal
  01_alice_input_1024.png    — squared / resized 1024² input
  02_alice_shape.obj         — shape only, 16 MB, V=209k F=418k
  03_alice_textured.glb      — full PBR, 16 MB, V=327k F=418k, tex 2048²
logs/
  run.log                    — full inference log
```

Open `03_alice_textured.glb` in any GLTF viewer (Blender, online viewers, etc.) to inspect quality.

## Next: E-07 retop

The mesh is too dense for skinning. PyMeshLab quadric collapse OR Instant Meshes (if I can build it) will reduce to ~5-8k quads.
