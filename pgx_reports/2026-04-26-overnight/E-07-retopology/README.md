# E-07 — Retopology Open-Source Methods

**Status**: ⛔ **Not run tonight** — both Blender (libX11 missing) and Instant Meshes binary (no ARM build) blocked on this container; pre-condition E-05 also not run.
**Architect's question**: part of **Q4**.

## The headline finding from the audit

| Tool | ARM64 status (in container) | License | Quality on AI mesh |
|---|---|---|---|
| Instant Meshes (wjakob) | ❌ no ARM binary; source build untested | GPL | gold-standard quad remesh |
| Blender QuadriFlow | ❌ Blender unloadable on ARM container (libX11 missing, no sudo) | GPL | good |
| PyMeshLab | ✅ likely (pip wheels for aarch64 exist for many versions) | GPL | adequate |
| trimesh + meshio | ✅ pure python | MIT | no remesh, just IO |
| `nvdiffrast` | ✅ ARM CUDA build expected | NVIDIA SLA | for differentiable rendering, not retop |

**The retopology problem on this hardware is mostly about getting Blender / Instant Meshes to run, not about which algorithm wins.**

## What we know without measuring

For AI-generated meshes (Hunyuan3D / TRELLIS class):
- **Instant Meshes** with `Vertex count = 5000-8000` produces clean quads suitable for skinning. Algorithm has been gold-standard since 2015.
- **QuadriFlow** is comparable for organic shapes; weaker for hard surface; bundled with Blender.
- **PyMeshLab** (`Quadric Edge Collapse Decimation`) is a reasonable Python-callable alternative when Blender isn't available; it produces tris not quads but tris are still skinnable.

## Recommendation for the next session

When you run experiments on the freed GPU:

1. Run E-05 first to get a Hunyuan3D mesh.
2. **Don't fight the ARM-Blender issue** — instead, run retop via PyMeshLab in this Python env (5 minutes). It's good enough.
3. If you need Blender QuadriFlow for higher quality, do that on **a different host** (any x86 dev box) and round-trip the mesh.
4. Production-grade retop will need a Blender x86 worker in any case (because Rigify, NPR shaders, and many DCC tools live in Blender). **This is an architectural constraint of the project, not a failure of E-07.**

## What this directory will contain after run

- `samples/alice_hunyuan3d_raw.obj` — copy of E-05 output
- `samples/alice_pymeshlab_remesh.obj` — PyMeshLab quadric collapse
- `samples/alice_instantmeshes_quad.obj` — if Instant Meshes built (low confidence)
- `details.md` — per-tool params and runtime
- `samples/topology_comparison.png` — wireframe overlay of three retops

## Architectural note (independent of run result)

Retopology is **deterministic, well-understood, and not the project's bottleneck**. Treat E-07 as a routine pipeline step, not as a research question. AC-5 (Animation is open problem) doesn't extend to retop — that's solved.

The genuine open problem is **anime-aware retopology** (place edge loops along eye-lid and mouth flow lines for blendshape friendliness). No 2026 open-source tool does this automatically. Manual work + a Blender add-on like RetopoFlow handles it. Budget: 2-4 hours of human work per character if you want film-quality retop.
