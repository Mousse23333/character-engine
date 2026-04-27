"""E-05 texture-only: load existing shape from E-05, run Hunyuan3D Paint pipeline only."""
import torch, time, sys, os
from pathlib import Path
from PIL import Image

ROOT = Path("/workspace/character-engine")
HUNY = ROOT / "tools/Hunyuan3D-2"
sys.path.insert(0, str(HUNY))

OUT = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-A-3D/E-05-hunyuan3d/samples"

import trimesh
mesh = trimesh.load(OUT / "02_alice_shape.obj")
print(f"loaded shape: V={len(mesh.vertices):,} F={len(mesh.faces):,}")

img = Image.open(OUT / "01_alice_input_1024.png").convert("RGBA")

from hy3dgen.texgen import Hunyuan3DPaintPipeline
torch.cuda.reset_peak_memory_stats()
t0 = time.time()
paint = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
print(f"paint pipeline loaded: {time.time()-t0:.1f}s, GPU={torch.cuda.memory_allocated()/1e9:.2f}GB")

t0 = time.time()
textured = paint(mesh, image=img)
texture_time = time.time() - t0
print(f"texture inference: {texture_time:.1f}s, GPU peak={torch.cuda.max_memory_allocated()/1e9:.2f}GB")

textured.export(str(OUT / "03_alice_textured.glb"))
print(f"saved → 03_alice_textured.glb")
print(f"final mesh: V={len(textured.vertices):,} F={len(textured.faces):,}")
