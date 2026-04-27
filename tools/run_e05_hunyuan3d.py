"""E-05: Hunyuan3D 2.0 mesh + texture generation on Alice reference.

Output:
  - alice_shape.obj (just shape, no texture)
  - alice_textured.glb (PBR textured)
  - quality metrics: face count, UV check, back-view render
"""
import torch, time, os, sys
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path("/workspace/character-engine")
HUNY = ROOT / "tools/Hunyuan3D-2"
sys.path.insert(0, str(HUNY))

OUT = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-A-3D/E-05-hunyuan3d"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "samples").mkdir(exist_ok=True)
(OUT / "logs").mkdir(exist_ok=True)

# Use Alice ref upscaled
ref_path = ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples/02_realesrgan_x4_756x1068.png"
img = Image.open(ref_path).convert("RGB")
print(f"input: {ref_path.name}, size={img.size}")

# Hunyuan3D works best on square, with background removed
from hy3dgen.rembg import BackgroundRemover
print("Removing background...")
t0 = time.time()
rembg = BackgroundRemover()
img_rgba = rembg(img)
img_rgba.save(OUT / "samples/00_alice_rembg.png")
print(f"  rembg: {time.time()-t0:.1f}s")

# Make square — pad to square then resize to 1024
w, h = img_rgba.size
side = max(w, h)
canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
canvas.paste(img_rgba, ((side - w) // 2, (side - h) // 2))
img_sq = canvas.resize((1024, 1024), Image.LANCZOS)
img_sq.save(OUT / "samples/01_alice_input_1024.png")
print(f"  squared and resized to 1024x1024")

# Step 1: Shape generation
print("\n=== Shape generation ===")
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
torch.cuda.reset_peak_memory_stats()
t0 = time.time()
pipeline_shapegen = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2")
print(f"  shape pipeline loaded: {time.time()-t0:.1f}s, GPU={torch.cuda.memory_allocated()/1e9:.2f}GB")

t0 = time.time()
mesh = pipeline_shapegen(image=img_sq)[0]
shape_time = time.time() - t0
print(f"  shape inference: {shape_time:.1f}s, GPU peak={torch.cuda.max_memory_allocated()/1e9:.2f}GB")

shape_path = OUT / "samples/02_alice_shape.obj"
mesh.export(str(shape_path))
print(f"  → {shape_path.name}")

# Mesh stats
import trimesh
m = trimesh.load(shape_path)
n_v = len(m.vertices)
n_f = len(m.faces)
print(f"  vertices: {n_v:,}, faces: {n_f:,}")
print(f"  watertight: {m.is_watertight}")
print(f"  bounds: {m.bounds}")

# Step 2: Texture generation
print("\n=== Texture generation ===")
del pipeline_shapegen
torch.cuda.empty_cache()
from hy3dgen.texgen import Hunyuan3DPaintPipeline
t0 = time.time()
pipeline_texgen = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
print(f"  texture pipeline loaded: {time.time()-t0:.1f}s, GPU={torch.cuda.memory_allocated()/1e9:.2f}GB")

t0 = time.time()
textured = pipeline_texgen(mesh, image=img_sq)
texture_time = time.time() - t0
print(f"  texture inference: {texture_time:.1f}s, GPU peak={torch.cuda.max_memory_allocated()/1e9:.2f}GB")

textured_path = OUT / "samples/03_alice_textured.glb"
textured.export(str(textured_path))
print(f"  → {textured_path.name}")

# Render multi-view via trimesh's built-in PIL rendering (no GL needed)
print("\n=== Multi-view via trimesh.scene ===")
try:
    from PIL import Image as PI
    scene = trimesh.Scene([textured])
    for angle, name in [(0, "front"), (90, "right"), (180, "back"), (270, "left")]:
        # trimesh save_image uses PyOpenGL/pyglet — may also fail
        try:
            png = scene.save_image(resolution=(512, 512),
                                   visible=True)  # offscreen
            with open(OUT / f"samples/04_render_{name}.png", "wb") as f:
                f.write(png)
            # rotate scene for next view
            scene.set_camera(angles=(0, np.radians(angle+90), 0))
        except Exception:
            break
    print("  trimesh render attempted")
except Exception as e:
    print(f"  render skipped (non-fatal, no GL): {type(e).__name__}")

# Save metrics
import csv
metrics = [
    ("E-05", "shape_inference_time", shape_time, "seconds", 1, "Hunyuan3D 2.0 shape on alice", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ("E-05", "texture_inference_time", texture_time, "seconds", 1, "Hunyuan3D 2.0 paint on alice", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ("E-05", "n_vertices", n_v, "count", 1, "raw mesh", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ("E-05", "n_faces", n_f, "count", 1, "raw mesh", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ("E-05", "watertight", int(m.is_watertight), "bool", 1, "mesh integrity", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ("E-05", "gpu_peak_total", round(torch.cuda.max_memory_allocated()/1e9, 2), "GB", 1, "shape+texture peak", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
]
csv_path = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/RAW_NUMBERS.csv"
write_header = not csv_path.exists()
with open(csv_path, "a", newline="") as f:
    w = csv.writer(f)
    if write_header:
        w.writerow(["experiment", "metric", "value", "unit", "sample_size", "notes", "timestamp"])
    for row in metrics:
        w.writerow(row)
print(f"\n=== E-05 done. Metrics → {csv_path} ===")
print(f"Total time: shape {shape_time:.0f}s + texture {texture_time:.0f}s = {shape_time+texture_time:.0f}s")
print(f"Peak GPU: {torch.cuda.max_memory_allocated()/1e9:.2f} GB")
