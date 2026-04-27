# Path C — Hybrid 2D + 3D (sketched, not implemented)

**Status**: 💡 **Architectural sketch based on tonight's observations**
**Date**: 2026-04-27

This is the path the architect explicitly invited me to propose IF I saw "two paths each fail, but combined they work". I do see it.

---

## The split

| Concern | Use | Reason |
|---|---|---|
| **Character body & equipment** (Identity ② + Equipment ⑤ + State ⑥) | **3D mesh + texture** (Path A: Hunyuan3D) | Deterministic composition. Equipment swap = mesh layer swap. State = shader uniforms. **AC-3 scales naturally.** |
| **Animation** (Production line ⑦) | **2D video** (Path B: Wan 2.2 Animate or I2V) | The 3D rigging line is engineering-incomplete on open-source for anime. Bypass it entirely by using a video model that conditions on a 2D character render. |
| **Style** (Production line ①) | Either, depends on stage | At gen-time: SDXL/Illustrious LoRA. At render-time: NPR shader on the 3D mesh, OR style-lock the video model. |

## The flow (proposed MVP)

```
Offline (slow, batchable):
  Concept → SDXL/Illustrious + IP-Adapter → multi-view image set
                          ↓
                   Hunyuan3D 2.0/2.5 → textured 3D mesh
                          ↓
                   trimesh retop → animation-ready mesh
                          ↓
                  (optional, x86 worker): UniRig → rigged FBX
                          ↓
              Asset Repository (immutable, versioned)
                          ↓
       Static render of character in default pose → "canonical 2D ref"

Online (fast, per request):
  Equipment + state → recompose 3D character → render to 2D ref image
                          ↓
                  Wan 2.2 I2V/Animate(ref=2D-ref-image, drive=animation-clip)
                          ↓
                       Animated MP4 / sprite frames
                          ↓
                       PIXI game render
```

**The key insight**: instead of building a fragile end-to-end 3D animation pipeline (which fails at rigging + DWpose), we use 3D for **identity composition** (where it shines) and 2D video for **motion delivery** (where Wan 2.2 shines). The 3D->2D projection is the bridge.

## Where this beats each path standalone

- vs. pure 3D (Path A): no need to solve rigging immediately. **Defer the rigging blocker by a year while still shipping content.**
- vs. pure 2D (Path B): equipment + state combinatorics are tractable (deterministic 3D composition + per-frame video gen, not full re-prompt-per-combination).

## Where it's worse than each path standalone

- More plumbing: TWO pipelines to maintain (mesh assets + video models)
- 2D video at runtime: still expensive (~10 min/sec at 832×480 today). Caching is mandatory.
- The 3D→2D bridge has to be aesthetically aligned with the video model's stylistic biases — quality risk.

## What this implies for AC-1.1

The architect's question — **"are Animation Assets 2D or 3D?"** — answers via Path C as:

> **Both. Identity Assets are 3D. Animation Assets are 2D video clips conditioned on a 3D-rendered ref frame.**

The Asset Contract (architecture's §6) needs schemas for both:

```yaml
IdentityAsset:
  3d_mesh: glb path
  rig: optional (FBX path, or null until rigging line lands)
  default_pose_render: PNG (for video model conditioning)

AnimationAsset:
  video: MP4 path
  frame_count: int
  source_identity: IdentityAsset.uuid
  source_motion: MotionAsset.uuid (e.g., a Mixamo FBX or driving video)
```

## Concrete next steps if architect picks Path C

1. (1 day) Asset Contract schema design — both classes above + Equipment + State + Style
2. (1 week) Productionize SDXL → Hunyuan3D mesh pipeline (already 80% working)
3. (3 days) Productionize 3D-render-to-2D-ref bridge (3D scene + camera + render to PNG)
4. (1 week) Wan 2.2 Animate-14B integration (after preprocess port)
5. (1-2 weeks) PIXI integration + caching layer
6. (parallel, deferred) UniRig porting, bring rigging online when x86 worker available

**Total to MVP**: 3-4 weeks if work is parallelized.

## The risk that kills this

The aesthetic bridge: 3D PBR mesh render vs. anime cel-shaded 2D output. If the renders going into Wan 2.2 don't look "anime enough", the video model's style transfer may drift heavily, breaking identity preservation.

**Mitigation**: NPR shader pass on the 3D ref (HoyoToon-class) BEFORE feeding to Wan. Now the video model sees a 2D anime-styled ref, not a PBR render.

(Note: this requires Blender x86 worker again — but only as a render service, not for the runtime path.)
