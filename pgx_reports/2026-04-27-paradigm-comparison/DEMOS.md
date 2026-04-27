# Demos — what to look at, in priority order

All files in this list are **on GitHub** (pushed today). Click a path to view in the GitHub UI; or `git pull` to get them locally.

---

## ⭐ Highest-priority demos (the reason architects asked for measurements)

### 1. Wan 2.2 Animate-14B end-to-end output — actual motion ✨

**The big one.** Single ref image + driving video → animated character.

| File | Size | What |
|---|---|---|
| `path-B-2D-video/E-11-animate/samples/alice_animated.mp4` | 2.4 MB | **The output: 106 frames @ 30 fps, ~3.5 sec, 624×624 — Alice dancing per the driving video's motion** |
| `path-B-2D-video/E-11-animate/samples/frame_0000.png` | 260 KB | Frame 0 — Alice standing |
| `path-B-2D-video/E-11-animate/samples/frame_0057.png` | 280 KB | Frame 57 — mid-dance |
| `path-B-2D-video/E-11-animate/samples/frame_0105.png` | 264 KB | Frame 105 — feet extended, mid-step |
| `path-B-2D-video/E-11-animate/samples/preprocessed/src_pose.mp4` | 127 KB | Extracted pose from driving video (visualized) |
| `path-B-2D-video/E-11-animate/samples/preprocessed/src_face.mp4` | 221 KB | Extracted face landmarks |
| `path-B-2D-video/E-11-animate/samples/metrics.json` | 1 KB | CLIP-I numbers (0.893 ref, 0.917 cross-frame) |

> **Architect:** open `alice_animated.mp4` in any video player. This was generated end-to-end on this aarch64+GB10 hardware in 25 minutes from a single Alice reference image plus the bundled Wan example dance video.

### 2. Hunyuan3D 2.0 textured mesh — full PBR 3D character

| File | Size | What |
|---|---|---|
| `path-A-3D/E-05-hunyuan3d/samples/03_alice_textured.glb` | **16 MB** | **The 3D model.** Open in Blender, online viewer (`gltf.report`), or any GLTF tool. V=327k F=418k + 2048² PBR texture. |
| `path-A-3D/E-05-hunyuan3d/samples/02_alice_shape.obj` | 16 MB | Shape only (no texture) — V=209k F=418k |
| `path-A-3D/E-05-hunyuan3d/samples/00_alice_rembg.png` | 363 KB | Input after background removal |
| `path-A-3D/E-05-hunyuan3d/samples/01_alice_input_1024.png` | 348 KB | Squared 1024² input fed to Hunyuan3D |

> **Architect:** drag-drop the `.glb` into https://gltf.report/ to spin it around in 3D in your browser.

### 3. Wan 2.2 I2V (subtle micro-motion baseline)

For comparison with Animate — same stack, but no driving video.

| File | Size | What |
|---|---|---|
| `path-B-2D-video/E-11-i2v/samples/alice_i2v.mp4` | 1.4 MB | 33 frames @ 16 fps, ~2 sec, 736×528 — Alice standing with breathing-level motion only |
| `path-B-2D-video/E-11-i2v/samples/frame_000.png` | 224 KB | Frame 0 |
| `path-B-2D-video/E-11-i2v/samples/frame_032.png` | 308 KB | Frame 32 — visually nearly identical to frame 0 (proof that I2V on a static prompt produces minimal motion) |
| `path-B-2D-video/E-11-i2v/samples/metrics.json` | 1 KB | CLIP-I 0.954 to ref, 0.976 cross-frame |

### 4. Equipment swap test (the AC-3 negative finding)

| File | Size | What |
|---|---|---|
| `path-B-2D-video/E-11-equipment/samples/variant_default.png` | 1.5 MB | Alice in default Lolita (CLIP-I 0.748 vs original) |
| `path-B-2D-video/E-11-equipment/samples/variant_armor.png` | 1.6 MB | Alice in knight armor (CLIP-I 0.623) |
| `path-B-2D-video/E-11-equipment/samples/variant_school_uniform.png` | 1.5 MB | Alice in sailor uniform (CLIP-I 0.697) |
| `path-B-2D-video/E-11-equipment/samples/variant_swimwear.png` | 1.4 MB | Alice in swimwear (CLIP-I 0.613) |

> **Architect:** stack these against the original Alice — face/hair/eye-style preserved, but **outfit is the dominant CLIP-I signal**. Pure prompt-only equipment swap drops CLIP-I 30 points. This is why I recommend Path C.

### 5. Path A retopped meshes (CPU quadric decimation)

| File | Size | What |
|---|---|---|
| `path-A-3D/E-07-retop/samples/alice_retop_49999f.obj` | 3.0 MB | 50k tris (12% of original) |
| `path-A-3D/E-07-retop/samples/alice_retop_20000f.obj` | 912 KB | 20k tris — recommended for skinning |
| `path-A-3D/E-07-retop/samples/alice_retop_19600f.obj` | 857 KB | 19.6k tris (the trimesh non-manifold floor) |

---

## What's NOT in git (and why)

| File | Why excluded |
|---|---|
| `tools/Wan2.2/` (model code clone) | repo, fetched on demand |
| `tools/Hunyuan3D-2/` | same |
| `tools/UniRig/` | same |
| `tools/blender-arm64.tar.gz` | 343 MB binary — see download URL in scripts |
| `tools/pgx-env/` | venv (machine-specific) |
| HF cache (Wan/Hunyuan/SDXL weights) | 440 GB — see `tools/download_models.sh` |

---

## Quick local-view guide

```bash
git pull origin main
cd character-engine

# Watch the Animate output (the main attraction)
mpv pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-animate/samples/alice_animated.mp4
# or vlc / ffplay / any browser

# Look at the 3D mesh
# (Drag-drop into https://gltf.report/ in browser — easiest)
ls pgx_reports/2026-04-27-paradigm-comparison/path-A-3D/E-05-hunyuan3d/samples/03_alice_textured.glb

# Compare static vs animated
mpv pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-i2v/samples/alice_i2v.mp4
mpv pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-animate/samples/alice_animated.mp4

# Equipment variants side-by-side
ls pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-equipment/samples/
```
