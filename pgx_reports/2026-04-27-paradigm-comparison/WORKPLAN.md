# Paradigm Comparison Workplan — 2026-04-27

**Task**: PGX_TASK_ADDENDUM_001 — parallel evaluation of 2D-video vs 3D pipeline.
**Time budget**: ~12-16 hours (full GPU now).
**Architect's mandate**: data, not advice. Both paths in measured form.

---

## Priority order (per ADDENDUM § 7)

| # | Task | Path | Decision value |
|---|---|---|---|
| 1 | E-11-Animate end-to-end | B | does B work today? |
| 2 | E-09 end-to-end (Hunyuan3D → rig → retarget → animate) | A | does A work today? |
| 3 | E-11-Animate-state (equipment in 2D) | B | does B handle AC-3? |
| 4 | E-05/E-07/E-08 quality details | A | quality scoring |
| 5 | E-14 NPR | A | only if A survives |

---

## Path B: Wan 2.2 Animate-14B (start here — highest ROI)

### Pre-flight
- [x] Wan 2.2 14B Animate weights cached (verified: `Wan2.2-Animate-14B` 28+ GB on disk)
- [x] Wan 2.2 repo cloned, all deps install except `decord`
- [ ] Patch `wan/animate.py` decord → imageio video reader (~50 LoC)
- [ ] Source 4-5 short open-source dance/walk/wave video clips for driving motion
- [ ] Prepare alice ref at 1024×1024 (already done in E-00 last night)

### Execution
- [ ] Patch + smoke test: load Wan2.2-Animate-14B model on freed GB10
- [ ] Single 5-second generation: alice + driving walk video
- [ ] 4 more clips: idle / wave / run / sit
- [ ] CLIP-I cross-frame within each clip (5 frames sampled)
- [ ] CLIP-I cross-clip (alice consistency across 5 separate generations)
- [ ] aesthetic predictor distribution
- [ ] DWpose extract on outputs (predicted 0 keypoints — confirms anime distribution)
- [ ] manual hand/face artifact rate (sample 20 frames)
- [ ] VRAM peak + per-clip wall time

### Equipment test (E-11-Animate-state)
- [ ] Generate alice variant with armor (use IP-Adapter-Plus output) as alternate ref
- [ ] Run Animate-14B with armor-alice + same driving video
- [ ] Score: equipment retention CLIP-I

### Pass/fail criteria for B
- ✅ Pass: end-to-end runs, CLIP-I cross-frame ≥ 0.85, hand/face artifact <30%, equipment retention shows >0.7 IoU/CLIP-I
- ❌ Fail: install blocker, OOM, identity collapse, character disappears mid-clip

---

## Path A: Hunyuan3D → retop → rig → retarget (parallel after B kicked off)

### Pre-flight
- [x] Hunyuan3D 2.0 custom ops compiled (last night)
- [x] Hunyuan3D-2 + 2.1 weights cached (~70 GB)
- [x] Hunyuan3D-2.5 — needs to verify whether weights publicly available (rigging-integrated)
- [x] PyMeshLab installed (CPU retop)
- [ ] Mixamo offline FBX library — download 4-5 standard animations once
- [ ] UniRig inference path — bypass bpy/open3d via trimesh shim

### Execution

**E-05 Hunyuan3D mesh**:
- [ ] Run Hunyuan3D 2.0 shape-gen on alice ref — log mesh face count, UV
- [ ] Run Hunyuan3D 2.0 paint-gen (texture)
- [ ] Render front + back + side; flag back-view artifacts
- [ ] If 2.5 weights work: also try 2.5 integrated rig

**E-07 PyMeshLab retop**:
- [ ] Quadric edge collapse → ~5000 faces
- [ ] Save .obj, evaluate edge flow

**E-08 UniRig**:
- [ ] Patch UniRig src to skip bpy/open3d for our test path
- [ ] Skeleton inference with Articulation-XL2.0 ckpt
- [ ] If memory permits: skinning (60 GB)
- [ ] Otherwise: hand-off skeleton, skip skinning

**E-09 retarget**:
- [ ] Download Mixamo offline FBX (idle/walk/wave/run from Mixamo's free downloads)
- [ ] Bone-name remap (mixamorig:Hips → ARP_Hips etc.)
- [ ] trimesh-based skinning + animation export
- [ ] Render animation MP4

### Pass/fail criteria for A
- ✅ Pass: end-to-end "static image → moving anime character video" works, even if quality is rough
- ❌ Fail: blocker at any step (most likely UniRig memory + bpy dep)

---

## Path C: Hybrid (only if both A and B partial-pass)

Sketch on the fly when we see what each yields.

---

## 9-dimension scoring table (final deliverable)

Will be filled after experiments. Template lives in `EXECUTIVE_SUMMARY.md`.

---

## Time budget allocation

| Activity | Hours |
|---|---|
| Path B setup + first run | 2-3h |
| Path B full quality eval | 1-2h |
| Path B equipment test | 1h |
| Path A E-05 + E-07 | 1-2h |
| Path A E-08 + E-09 | 2-3h |
| Path A NPR (if alive) | 1h |
| Final scoring + report writing | 1-2h |
| Buffer | 1-2h |

Total: ~10-15h, fits ADDENDUM § 7 (12-16h) budget.

---

## Working principles

- Stop fighting tooling that's not on the critical path (e.g., I burned 30 min on IP-Adapter Plus tuple bug — set aside, not blocking path B/A)
- Document failure modes precisely; failure data is decision data
- Commit + push every ~1h so the architect can sample progress
- Single quality sample > many shallow samples
