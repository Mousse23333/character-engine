# E-09 — Mixamo / FBX Animation Retargeting

**Status**: ⛔ **Not run tonight** — needs E-08 rigged output as input.
**AC-6 conflict**: spec said "upload to Mixamo" — that's a closed SaaS. **Replaced** with offline FBX library + Blender retarget.

## What we are NOT doing

- Uploading any data to mixamo.com (violates AC-6 — closed SaaS)
- Using AccuRIG (closed-source — same reason)

## What we will do (planned)

1. Download Mixamo's standard humanoid animation pack (one-time, free, redistributable inside our project repo since they're released under Mixamo's standard license that allows redistribution as part of derivative works).
   - Idle, walk, run, wave, jump, sit (6 standard clips, ~10 MB total)
2. Use **Blender's bone retargeter** (Blender 4.5 has a built-in `Animation > Retarget` node since 4.4) on the E-08 rigged Alice mesh.
3. Render side-by-side: Alice in Idle, Walk, Run, Wave.

## Failure modes to expect

| Issue | Likelihood | Workaround |
|---|---|---|
| Bone names don't match (Mixamo uses `mixamorig:Hips`, custom rig might use `Hip`) | 100 % | Build a name-mapping (one-time, <5 LoC) |
| Bind pose differs (T-pose vs A-pose) | 70 % | Re-bind via Blender; recompute skinning weights against new bind pose |
| Skinning artifacts at hip / shoulder under high motion | 60 % | Manual weight paint; OR upgrade to Hunyuan3D 2.5 rigging which may have better weights |
| Anime proportions break realistic motion | 50 % | Scale animation amplitude per joint; this is genuinely hard |

## Why offline-FBX > Mixamo SaaS

| Dimension | Mixamo SaaS | Offline FBX library |
|---|---|---|
| AC-6 compliance | ❌ closed | ✅ free + redistributable |
| Stability | depends on Adobe | ✅ files don't change |
| Reproducibility | non-deterministic upload | ✅ deterministic |
| Iteration speed | upload ~3 min/try | ✅ Blender hotkey, <1 s |

The architect should **edit the spec** to remove "upload to Mixamo" wording; this is a writing oversight, not an architectural problem.

## What this directory will contain after run

- `samples/alice_idle.mp4`
- `samples/alice_walk.mp4`
- `samples/alice_wave.mp4`
- `samples/clipping_artifacts.png` — annotated screenshots of perforations
- `details.md` — bone-name-map + retarget settings

## Architectural insight

If you're committed to the spec's pipeline: this step (FBX retarget) is the
**most boring, least-risky** step in Production Line ⑦. The hard parts are
upstream (mesh → rig) and downstream (rig + animation → online composition).

If you migrate to Wan 2.2 Animate-14B as Production Line ⑦ (per
ARCHITECT_DECISIONS.md § 1.1), then E-09 doesn't exist — Wan's preprocessor
takes a driving video directly.
