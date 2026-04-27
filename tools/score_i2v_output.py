"""Post-I2V scoring: extract frames + cross-frame CLIP-I + ref-CLIP-I."""
import sys, time, json, csv
from pathlib import Path
import torch
import numpy as np
import imageio.v3 as iio
from PIL import Image

ROOT = Path("/workspace/character-engine")
VIDEO = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-i2v/samples/alice_i2v.mp4"
SAMPLES = VIDEO.parent
REF = ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples/02_realesrgan_x4_756x1068.png"

assert VIDEO.exists(), f"video not found: {VIDEO}"

# Extract every-Nth frame
print(f"Loading video {VIDEO.name}...")
frames = list(iio.imiter(str(VIDEO)))
print(f"  {len(frames)} frames, shape={frames[0].shape}")

# Sample 8 evenly-spaced frames
sample_idxs = np.linspace(0, len(frames)-1, 8, dtype=int)
sampled = [Image.fromarray(frames[i]) for i in sample_idxs]
for i, img in zip(sample_idxs, sampled):
    img.save(SAMPLES / f"frame_{i:03d}.png")
print(f"  saved 8 sampled frames")

# Load CLIP
print("Loading CLIP-bigG-14...")
import open_clip
model, _, pp = open_clip.create_model_and_transforms("ViT-bigG-14", pretrained="laion2b_s39b_b160k")
model = model.to("cuda").eval()
print(f"  loaded, GPU={torch.cuda.memory_allocated()/1e9:.1f}GB")

ref_img = Image.open(REF).convert("RGB")

with torch.no_grad():
    rfeat = model.encode_image(pp(ref_img).unsqueeze(0).to("cuda"))
    rfeat /= rfeat.norm(dim=-1, keepdim=True)

    # CLIP-I to ref per frame
    feats = []
    for img in sampled:
        f = model.encode_image(pp(img).unsqueeze(0).to("cuda"))
        f /= f.norm(dim=-1, keepdim=True)
        feats.append(f)
    feats = torch.cat(feats, dim=0)
    sims_ref = (rfeat @ feats.T).cpu().numpy().flatten()
    print(f"\n CLIP-I to original ref (8 sampled frames):")
    for i, s in zip(sample_idxs, sims_ref):
        print(f"   frame {i:03d}: {s:.3f}")
    print(f"   mean: {sims_ref.mean():.3f}, std: {sims_ref.std():.3f}")

    # Cross-frame CLIP-I (consistency within video)
    cross = (feats @ feats.T).cpu().numpy()
    cross_off = cross[~np.eye(len(feats), dtype=bool)].reshape(len(feats), -1)
    print(f"\n Cross-frame CLIP-I (consistency within clip):")
    print(f"   mean off-diagonal: {cross_off.mean():.3f}")
    print(f"   min: {cross_off.min():.3f} (least similar pair)")

# Persist
ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
csv_path = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/RAW_NUMBERS.csv"
with open(csv_path, "a", newline="") as f:
    w = csv.writer(f)
    w.writerow(["E-11-I2V", "frames_actual", len(frames), "count", 1, "video frames", ts])
    w.writerow(["E-11-I2V", "clip_i_to_ref_mean", round(float(sims_ref.mean()), 4), "cosine", 8, "8 sampled frames vs ref", ts])
    w.writerow(["E-11-I2V", "clip_i_to_ref_std", round(float(sims_ref.std()), 4), "cosine", 8, "stability across frames", ts])
    w.writerow(["E-11-I2V", "clip_i_cross_frame_mean", round(float(cross_off.mean()), 4), "cosine", 56, "off-diagonal 8x8", ts])
    w.writerow(["E-11-I2V", "clip_i_cross_frame_min", round(float(cross_off.min()), 4), "cosine", 1, "least-similar pair", ts])

# Save metrics summary
with open(SAMPLES / "metrics.json", "w") as f:
    json.dump({
        "frames": len(frames),
        "clip_i_to_ref_per_frame": [float(x) for x in sims_ref],
        "clip_i_to_ref_mean": float(sims_ref.mean()),
        "clip_i_to_ref_std": float(sims_ref.std()),
        "clip_i_cross_frame_mean": float(cross_off.mean()),
        "clip_i_cross_frame_min": float(cross_off.min()),
        "video_size_MB": VIDEO.stat().st_size / 1e6,
    }, f, indent=2)
print(f"\n Saved metrics to {SAMPLES / 'metrics.json'}")
