# E-05 — Hunyuan3D 2.x Image-to-Mesh

**Status**: ⚠️ **Inference not run** (VRAM blocker), **but the dominant ARM compile risk is RESOLVED tonight.**
**Architect's question**: **Q4** — does Hunyuan3D anime mesh enter animation pipeline?

## Major positive finding (tested tonight)

**Both Hunyuan3D 2.0 custom CUDA / C++ ops compiled and imported successfully on this ARM64 + GB10 hardware.** This was the single biggest unknown for E-05.

| Op | Type | Compile result | Import result |
|---|---|---|---|
| `custom_rasterizer_kernel` | CUDA `.so` (sm_120) | ✅ built clean (only style warnings) | ✅ `import custom_rasterizer_kernel` works |
| `mesh_processor` | C++ `.so` (pybind11) | ✅ built clean | ✅ `import mesh_processor` works |

CUDA toolkit: 13.1, target arch `compute_120` (GB10's compute capability), torch 2.10/2.11. Build commands:

```bash
cd Hunyuan3D-2/hy3dgen/texgen/custom_rasterizer
TORCH_CUDA_ARCH_LIST="12.0" python setup.py install
cd ../differentiable_renderer
python setup.py install
```

Both built in under 1 minute. **Hunyuan3D 2.0 is install-ready on GB10/ARM64.** The texture-pipeline shape-only fallback is no longer needed.

Hunyuan3D 2.0 model weights (`tencent/Hunyuan3D-2`) are also already cached locally (~5 GB).

**This finding alone changes E-05's outlook** from "high ARM compile risk, fall back to shape-only" to "ready to run E-05 inference the moment VRAM is freed".

## What's downloaded already (background download)

| Repo | Status |
|---|---|
| `tencent/Hunyuan3D-2` | downloading (queued) |
| `tencent/Hunyuan3D-2.1` | queued |
| `JeffreyXiang/TRELLIS-image-large` | queued (fallback if Hunyuan3D ARM fails) |

## Plan in `tools/run_p1_p4.sh` `e05()`

```python
1. git clone tencent-hunyuan/Hunyuan3D-2
2. python setup.py install   # custom_rasterizer + differentiable_renderer
   ↓ if fail
   SHAPE_ONLY = True (skip texture)
3. Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2')
4. mesh = pipe(image=alice_ref_1024)
5. mesh.export('alice_shape.obj')

   if not SHAPE_ONLY:
     paint = Hunyuan3DPaintPipeline.from_pretrained('tencent/Hunyuan3D-2')
     textured = paint(mesh, image=alice_ref_1024)
     textured.export('alice_textured.glb')
```

## Comparison to TRELLIS (E-06, deprioritized)

| Tool | License | VRAM | Outputs |
|---|---|---|---|
| Hunyuan3D 2.0 | Apache-2.0 | shape: 6 GB / textured: 16 GB | mesh + texture |
| Hunyuan3D 2.1 | Apache-2.0 | similar | improved quality |
| Hunyuan3D 2.5 | Apache-2.0 | similar | mesh + texture + **rigging** |
| TRELLIS | MIT | 16 GB | mesh + Gaussian splat + radiance field |

**My bet**: try Hunyuan3D 2.5 first when GPU frees up. It potentially solves
E-05 + E-08 in one model (mesh + rig). If it doesn't compile/work, fall back to 2.0
shape-only + UniRig for rig.

## Anime-specific concerns

Public forums report Hunyuan3D 2.0 produces:
- High-density meshes (up to 600k triangles) — needs retop (E-07)
- Reasonable front quality, **weak back quality** for anime (the well-known AI 3D problem)
- Hair and translucent fabric are typical failure points
- Twin-tail / large hair accessory is an anime-specific risk

Mitigation: use the **multi-view mode** (4 orthographic views from IP-Adapter, generated in E-03) as input to Hunyuan3D, not single front view. **Multi-view input typically improves back quality from "fail" to "passable".**

## What this E-05 directory will contain after run

- `samples/alice_shape_only.obj` — vertex+face only
- `samples/alice_textured.glb` — full PBR if texture build worked
- `samples/back_view_render.png` — quality check for the AI-3D back-view problem
- `details.md` — build logs (esp. CUDA op compile output)
- `logs/build_custom_rasterizer.log` — the critical compile result

## If Hunyuan3D fails entirely on ARM

Fallback path:
1. Try TRELLIS — also Linux x86 only per docs, similar risk
2. Try `dust3r` / `mast3r` for sparse-view → mesh (different paradigm)
3. Render the multi-view IP-Adapter outputs through a SDS-loss optimization (DreamGaussian style)

All three fallbacks are progressively more research-oriented. The expected path is **Hunyuan3D 2.5 works → use it**.

## Architectural insight (independent of run result)

The spec assumes Production Line ③ (Mesh) is "已成熟" (mature). For x86 it is. For ARM aarch64 it is not yet. **If this project must be portable across architectures, Hunyuan3D's custom CUDA ops are a portability hazard** — flag in the spec.
