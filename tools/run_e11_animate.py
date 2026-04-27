"""E-11-Animate: Wan 2.2 Animate-14B end-to-end on Alice + driving video.

Workflow:
  1. Preprocess: extract pose + face from driving video (uses Wan's preprocess module)
  2. Generate: Wan2.2-Animate-14B(ref_image=alice, processed_motion) → animated video
  3. Score: per-frame CLIP-I, hand/face artifact rate, time, VRAM

Note: This script assumes:
  - decord shim is installed (we did this earlier)
  - Wan 2.2 Animate-14B weights are at /home/daniel/.cache/huggingface/hub/models--Wan-AI--Wan2.2-Animate-14B/snapshots/<id>/
  - The driving video is examples/wan_animate/animate/video.mp4 (bundled with Wan repo)

Run mode: animation (NOT replace mode — replace requires SAM2 mask which we skip).
"""
import os, sys, time, subprocess, json
from pathlib import Path

# Use mesa libGL for any opengl-leaning deps
os.environ["LD_LIBRARY_PATH"] = (
    "/workspace/character-engine/tools/blender-4.5.1-git20250730.28c0962c45ac-aarch64/lib/mesa:"
    + os.environ.get("LD_LIBRARY_PATH", "")
)

ROOT = Path("/workspace/character-engine")
WAN = ROOT / "tools/Wan2.2"
sys.path.insert(0, str(WAN))

OUT = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-animate"
SAMPLES = OUT / "samples"
LOGS = OUT / "logs"
SAMPLES.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

# ===== Step 0: confirm Animate-14B model is downloaded =====
ANIMATE_DIR = list(Path("/home/daniel/.cache/huggingface/hub/models--Wan-AI--Wan2.2-Animate-14B/snapshots").glob("*"))[0]
PROCESS_CKPT = ANIMATE_DIR / "process_checkpoint"
print(f"Animate model dir: {ANIMATE_DIR}")
print(f"Process checkpoint dir: {PROCESS_CKPT}")
assert PROCESS_CKPT.exists(), f"process_checkpoint not found at {PROCESS_CKPT}"

# Check that the main 14B safetensors are present (pattern: diffusion_pytorch_model-00001-of-XXXX.safetensors)
shards = list(ANIMATE_DIR.glob("diffusion_pytorch_model-*.safetensors"))
print(f"Found {len(shards)} weight shards (expected ~6+)")

# ===== Step 1: Prepare inputs =====
# Reference image: alice (square 1024)
alice_ref = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-animate/samples/alice_ref_1024.png"
if not alice_ref.exists():
    # Build it from the upscaled image
    src = ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples/02_realesrgan_x4_756x1068.png"
    from PIL import Image
    img = Image.open(src).convert("RGB")
    w, h = img.size
    side = min(w, h); l = (w - side)//2; t = (h - side)//2
    sq = img.crop((l, t, l+side, t+side)).resize((1024, 1024), Image.LANCZOS)
    sq.save(alice_ref)
    print(f"Built {alice_ref.name}: {sq.size}")

# Driving video: use Wan's bundled example
DRIVE_VIDEO = WAN / "examples/wan_animate/animate/video.mp4"
print(f"Driving video: {DRIVE_VIDEO}, exists={DRIVE_VIDEO.exists()}")

# ===== Step 2: Preprocess driving video → pose / face / bg / mask =====
PROCESS_OUT = SAMPLES / "preprocessed"
PROCESS_OUT.mkdir(exist_ok=True)

print("\n=== Preprocessing driving video ===")
t0 = time.time()
preprocess_cmd = [
    str(WAN / "wan/modules/animate/preprocess/preprocess_data.py"),
    "--ckpt_path", str(PROCESS_CKPT),
    "--video_path", str(DRIVE_VIDEO),
    "--refer_path", str(alice_ref),
    "--save_path", str(PROCESS_OUT),
    "--resolution_area", "832", "480",  # smaller resolution for first test
    "--retarget_flag",
    # NO --use_flux (closed-source weights)
    # NO --replace_flag (animation mode, not replace)
]
print("CMD:", " ".join(preprocess_cmd))
ret = subprocess.run(
    [sys.executable] + preprocess_cmd,
    cwd=str(WAN / "wan/modules/animate/preprocess"),
    env={**os.environ, "PYTHONPATH": str(WAN), "LD_LIBRARY_PATH": os.environ["LD_LIBRARY_PATH"]},
    capture_output=False,
)
preprocess_time = time.time() - t0
print(f"\npreprocess ret={ret.returncode}, time={preprocess_time:.1f}s")

if ret.returncode != 0:
    print("PREPROCESS FAILED — see preceding output for details")
    print("This is a key checkpoint. Writing partial result to RAW_NUMBERS.")
    # Persist failure note
    with open(OUT / "PREPROCESS_FAILED.txt", "w") as f:
        f.write(f"preprocess returncode: {ret.returncode}\nelapsed: {preprocess_time:.1f}s\n")
    sys.exit(1)
print(f"\npreprocess done. Outputs in {PROCESS_OUT}")
print("contents:", list(PROCESS_OUT.iterdir())[:10])

# ===== Step 3: Generate animation =====
print("\n=== Generating animated video ===")
t0 = time.time()
generate_cmd = [
    "generate.py",
    "--task", "animate-14B",
    "--ckpt_dir", str(ANIMATE_DIR),
    "--src_root_path", str(PROCESS_OUT),
    "--refert_num", "1",
    "--save_file", str(SAMPLES / "alice_animated.mp4"),
    "--frame_num", "81",  # ~5 sec at 16fps; must be 4n+1
    "--offload_model", "True",
    "--convert_model_dtype",
]
print("CMD:", " ".join(generate_cmd))
ret = subprocess.run(
    [sys.executable] + generate_cmd,
    cwd=str(WAN),
    env={**os.environ, "PYTHONPATH": str(WAN), "LD_LIBRARY_PATH": os.environ["LD_LIBRARY_PATH"]},
    capture_output=False,
)
gen_time = time.time() - t0
print(f"\ngenerate ret={ret.returncode}, time={gen_time:.1f}s ({gen_time/60:.1f} min)")

if ret.returncode != 0:
    print("GENERATE FAILED")
    sys.exit(1)
print(f"Output video: {SAMPLES / 'alice_animated.mp4'}")
print(f"=== E-11-Animate end-to-end SUCCESS ===")
print(f"  preprocess: {preprocess_time:.0f}s")
print(f"  generation: {gen_time:.0f}s ({gen_time/60:.1f} min)")
