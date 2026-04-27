"""E-11 Equipment Test (path B AC-3 evaluation):

Goal: Test whether Wan 2.2 I2V can generate the same Alice character with
DIFFERENT outfits (equipment) by varying the prompt + reference image.

Method:
  1. Generate three "outfit variants" of Alice as still images (using
     SDXL prompt-only — quickly produces variants in different costumes)
  2. Run Wan 2.2 I2V on each variant
  3. Compare CLIP-I to original alice ref:
     - identity preservation (face + hair) — should be high
     - outfit conformance (the equipment stays through the motion) — measure
"""
import os, sys, time, csv
from pathlib import Path
import torch

# Use mesa libGL workaround
os.environ["LD_LIBRARY_PATH"] = (
    "/workspace/character-engine/tools/blender-4.5.1-git20250730.28c0962c45ac-aarch64/lib/mesa:"
    + os.environ.get("LD_LIBRARY_PATH", "")
)

ROOT = Path("/workspace/character-engine")
OUT = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-equipment"
SAMPLES = OUT / "samples"
SAMPLES.mkdir(parents=True, exist_ok=True)
LOGS = OUT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# Step 1: Generate outfit variants via SDXL prompt-only (no IP-Adapter — avoid the tuple issue)
from diffusers import StableDiffusionXLPipeline

print("Loading SDXL base...")
t0 = time.time()
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    use_safetensors=True,
).to("cuda")
print(f"loaded in {time.time()-t0:.1f}s, GPU={torch.cuda.memory_allocated()/1e9:.1f}GB")

# Three outfit variants of Alice
OUTFITS = {
    "default": "1girl, alice, blonde short hair, blue ribbon, blue lolita dress, white knee socks, blue mary jane shoes, large blue eyes, fair skin, full body, anime style, masterpiece",
    "armor": "1girl, alice, blonde short hair, blue ribbon, silver knight armor with blue trim, white knee socks, dark boots, large blue eyes, fair skin, full body, anime style, masterpiece, fantasy",
    "school_uniform": "1girl, alice, blonde short hair, blue ribbon, navy school uniform with white collar, plaid skirt, white knee socks, brown loafers, large blue eyes, fair skin, full body, anime style, masterpiece",
    "swimwear": "1girl, alice, blonde short hair, blue ribbon, blue striped swimsuit, no socks, sandals, large blue eyes, fair skin, beach background, full body, anime style, masterpiece",
}

variant_paths = {}
for name, prompt in OUTFITS.items():
    print(f"\nGenerating {name}...")
    t0 = time.time()
    img = pipe(
        prompt=prompt,
        negative_prompt="bad hands, bad anatomy, lowres, blurry",
        num_inference_steps=30,
        guidance_scale=7.0,
        height=1024, width=1024,
        generator=torch.Generator("cuda").manual_seed(42),
    ).images[0]
    p = SAMPLES / f"variant_{name}.png"
    img.save(p)
    variant_paths[name] = p
    print(f"  {time.time()-t0:.1f}s → {p.name}")

del pipe
torch.cuda.empty_cache()
print(f"\nGPU after pipe free: {torch.cuda.memory_allocated()/1e9:.2f}GB")

# Step 2: CLIP-I score variants vs original alice
print("\n=== CLIP-I scoring ===")
import open_clip
clip_model, _, clip_pp = open_clip.create_model_and_transforms("ViT-bigG-14", pretrained="laion2b_s39b_b160k")
clip_model = clip_model.to("cuda").eval()

from PIL import Image
ref_img = Image.open(ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples/02_realesrgan_x4_756x1068.png").convert("RGB")
with torch.no_grad():
    rfeat = clip_model.encode_image(clip_pp(ref_img).unsqueeze(0).to("cuda"))
    rfeat /= rfeat.norm(dim=-1, keepdim=True)
    scores = {}
    for name, p in variant_paths.items():
        img = Image.open(p).convert("RGB")
        f = clip_model.encode_image(clip_pp(img).unsqueeze(0).to("cuda"))
        f /= f.norm(dim=-1, keepdim=True)
        scores[name] = float((rfeat @ f.T).item())

print("CLIP-I vs original alice ref:")
for k, v in scores.items():
    print(f"  {k:20s} {v:.3f}")

# Persist
ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
csv_path = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/RAW_NUMBERS.csv"
with open(csv_path, "a") as f:
    w = csv.writer(f)
    for k, v in scores.items():
        w.writerow(["E-11-equipment", f"clip_i_{k}_vs_orig", round(v, 4), "cosine", 1, "SDXL prompt-only outfit variant", ts])

print(f"\nDone. {len(variant_paths)} variants generated; CLIP-I scored.")
print("Next: run Wan 2.2 I2V on each variant to test motion + equipment retention.")
