"""Score Animate-14B output: extract frames + CLIP-I to ref + cross-frame consistency.
Same approach as score_i2v_output.py, but on Animate's MP4."""
import sys, time, json, csv
from pathlib import Path
import torch
import numpy as np
import imageio.v3 as iio
from PIL import Image

ROOT = Path("/workspace/character-engine")
VIDEO = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-animate/samples/alice_animated.mp4"
SAMPLES = VIDEO.parent
REF = ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples/02_realesrgan_x4_756x1068.png"

assert VIDEO.exists()

print(f"Loading {VIDEO.name}...")
frames = list(iio.imiter(str(VIDEO)))
print(f"  {len(frames)} frames, shape={frames[0].shape}")

# Sample 12 frames evenly (more frames since Animate is longer)
N = 12
sample_idxs = np.linspace(0, len(frames)-1, N, dtype=int)
sampled = [Image.fromarray(frames[i]) for i in sample_idxs]
for i, img in zip(sample_idxs, sampled):
    img.save(SAMPLES / f"frame_{i:04d}.png")
print(f"  saved {N} sampled frames")

print("Loading CLIP-bigG-14...")
import open_clip
model, _, pp = open_clip.create_model_and_transforms("ViT-bigG-14", pretrained="laion2b_s39b_b160k")
model = model.to("cuda").eval()
ref_img = Image.open(REF).convert("RGB")

with torch.no_grad():
    rfeat = model.encode_image(pp(ref_img).unsqueeze(0).to("cuda"))
    rfeat /= rfeat.norm(dim=-1, keepdim=True)

    feats = []
    for img in sampled:
        f = model.encode_image(pp(img).unsqueeze(0).to("cuda"))
        f /= f.norm(dim=-1, keepdim=True)
        feats.append(f)
    feats = torch.cat(feats, dim=0)
    sims_ref = (rfeat @ feats.T).cpu().numpy().flatten()
    print(f"\nCLIP-I to original ref ({N} sampled frames):")
    for i, s in zip(sample_idxs, sims_ref):
        print(f"  frame {i:04d}: {s:.3f}")
    print(f"  mean: {sims_ref.mean():.3f}, std: {sims_ref.std():.3f}, min: {sims_ref.min():.3f}, max: {sims_ref.max():.3f}")

    cross = (feats @ feats.T).cpu().numpy()
    cross_off = cross[~np.eye(len(feats), dtype=bool)].reshape(len(feats), -1)
    print(f"\nCross-frame CLIP-I:")
    print(f"  mean off-diag: {cross_off.mean():.3f}")
    print(f"  min: {cross_off.min():.3f}")

ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
csv_path = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/RAW_NUMBERS.csv"
with open(csv_path, "a", newline="") as f:
    w = csv.writer(f)
    w.writerow(["E-11-Animate", "frames_actual", len(frames), "count", 1, "video frames", ts])
    w.writerow(["E-11-Animate", "preprocess_time", 64, "seconds", 1, "CPU ONNX (no GPU on ARM)", ts])
    w.writerow(["E-11-Animate", "generation_time", 1428, "seconds", 1, "4 windows x 20 sample steps", ts])
    w.writerow(["E-11-Animate", "output_size_MB", round(VIDEO.stat().st_size/1e6, 2), "MB", 1, "alice + Wan example drive", ts])
    w.writerow(["E-11-Animate", "clip_i_to_ref_mean", round(float(sims_ref.mean()), 4), "cosine", N, "vs original alice ref", ts])
    w.writerow(["E-11-Animate", "clip_i_to_ref_std", round(float(sims_ref.std()), 4), "cosine", N, "frame-stability", ts])
    w.writerow(["E-11-Animate", "clip_i_to_ref_min", round(float(sims_ref.min()), 4), "cosine", 1, "worst frame", ts])
    w.writerow(["E-11-Animate", "clip_i_cross_frame_mean", round(float(cross_off.mean()), 4), "cosine", N*(N-1), "off-diagonal", ts])
    w.writerow(["E-11-Animate", "clip_i_cross_frame_min", round(float(cross_off.min()), 4), "cosine", 1, "least-similar pair", ts])

with open(SAMPLES / "metrics.json", "w") as f:
    json.dump({
        "frames": len(frames),
        "preprocess_time_s": 64,
        "generation_time_s": 1428,
        "video_size_MB": VIDEO.stat().st_size / 1e6,
        "clip_i_to_ref": {
            "mean": float(sims_ref.mean()),
            "std": float(sims_ref.std()),
            "min": float(sims_ref.min()),
            "max": float(sims_ref.max()),
            "per_frame": [float(x) for x in sims_ref],
        },
        "clip_i_cross_frame": {
            "mean": float(cross_off.mean()),
            "min": float(cross_off.min()),
        },
    }, f, indent=2)
print(f"\nSaved metrics → {SAMPLES / 'metrics.json'}")
