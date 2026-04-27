# E-07 — Retopology (Path A, step 2)

**Status**: ✅ **Working via trimesh quadric decimation (CPU)**
**Time**: <1s per target
**Date**: 2026-04-27

## Numbers

Input: `E-05-hunyuan3d/samples/03_alice_textured.glb` — V=327k F=418k.

| Target faces | Actual faces | Vertices | Decimation ratio | Time |
|---|---|---|---|---|
| 50,000 | 49,999 | 57,847 | 11.96 % | 0.3 s |
| 20,000 | 20,000 | 15,205 | 4.78 % | 0.4 s |
| 8,000 | **19,600** (floor) | 14,049 | 4.69 % | 0.5 s |
| 5,000 | **19,600** (floor) | 14,049 | 4.69 % | 0.5 s |

**Floor at ~19,600 faces**: trimesh's quadric decimation refuses to go below this for the non-manifold input. Acceptable for skinning (anime characters typically ride 5-15k faces; 19.6k tris is in the same magnitude).

## Findings

- **trimesh `simplify_quadric_decimation` is fast and adequate** for this hardware.
- **No GPU needed**, no Blender needed, no pymeshlab GUI deps.
- The original AI mesh's **non-manifold geometry caps how aggressively we can decimate** — but 19.6k tris is workable.

### What we'd want next (deferred — not on critical path tonight)

- Quad-flow retopology (proper edge loops along anatomy) — needs Instant Meshes binary or Blender QuadriFlow. **Both ARM-blocked on this container** (no sudo / no ARM Blender).
- The current retopped mesh **has tris, not quads**. For Animation rigging this works; for film-quality skinning you'd want quads.

## Path-A status after E-07

| Step | Status | Time |
|---|---|---|
| E-05 mesh + texture | ✅ | 263 s |
| E-07 retop (tris) | ✅ | 0.5 s |
| E-08 rigging | ⏳ next |
| E-09 animation retarget | ⏳ |

Total path-A through retop: under 5 minutes for a riggable mesh from a 189×267 reference image. **Not bad.**

## Files

```
samples/
  alice_retop_49999f.obj   — 50k variant
  alice_retop_20000f.obj   — 20k variant (recommended for skinning)
  alice_retop_19600f.obj   — denser variant (floor)
```
