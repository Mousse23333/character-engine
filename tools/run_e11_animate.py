"""E-11-Animate: Wan 2.2 Animate-14B end-to-end on Alice + Wan example driving video.

Two-step run:
  1. Preprocess (on CPU ONNX since no onnxruntime-gpu on ARM):
        wan_animate/preprocess_data.py → pose / face conditioning
  2. Generate via Wan 2.2 Animate-14B inference

Outputs: alice_animated.mp4 in samples/
"""
import os, sys, time, subprocess, json
from pathlib import Path

# Use mesa libGL workaround
os.environ["LD_LIBRARY_PATH"] = (
    "/workspace/character-engine/tools/blender-4.5.1-git20250730.28c0962c45ac-aarch64/lib/mesa:"
    + os.environ.get("LD_LIBRARY_PATH", "")
)
os.environ["PYTHONUNBUFFERED"] = "1"

ROOT = Path("/workspace/character-engine")
WAN = ROOT / "tools/Wan2.2"

OUT = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-animate"
SAMPLES = OUT / "samples"
LOGS = OUT / "logs"
SAMPLES.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

ANIMATE_DIR = list(Path("/home/daniel/.cache/huggingface/hub/models--Wan-AI--Wan2.2-Animate-14B/snapshots").glob("*"))[0]
PROCESS_CKPT = ANIMATE_DIR / "process_checkpoint"
print(f"Animate model: {ANIMATE_DIR.name}")
print(f"Process ckpt:  {PROCESS_CKPT}")

alice_ref = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-B-2D-video/E-11-animate/samples/alice_ref_1024.png"
if not alice_ref.exists():
    src = ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples/02_realesrgan_x4_756x1068.png"
    from PIL import Image
    img = Image.open(src).convert("RGB")
    w, h = img.size; side = min(w, h); l = (w - side)//2; t = (h - side)//2
    sq = img.crop((l, t, l+side, t+side)).resize((1024, 1024), Image.LANCZOS)
    sq.save(alice_ref)
    print(f"Built {alice_ref.name}: {sq.size}")

DRIVE_VIDEO = WAN / "examples/wan_animate/animate/video.mp4"
print(f"Driving video: {DRIVE_VIDEO}")
assert DRIVE_VIDEO.exists()

PROCESS_OUT = SAMPLES / "preprocessed"
PROCESS_OUT.mkdir(exist_ok=True)

# ============================================================
# Step 1: Preprocess (CPU ONNX path)
# ============================================================
print("\n=== Preprocessing driving video (CPU ONNX — slow but ARM-compatible) ===")
t0 = time.time()

# Build a wrapper script that monkey-patches onnxruntime to force CPU,
# then runs preprocess_data.py with proper argv
preprocess_args = [
    "--ckpt_path", str(PROCESS_CKPT),
    "--video_path", str(DRIVE_VIDEO),
    "--refer_path", str(alice_ref),
    "--save_path", str(PROCESS_OUT),
    "--resolution_area", "832", "480",
    "--retarget_flag",
]

wrapper_code = (
    "import onnxruntime as _ort\n"
    "_orig = _ort.InferenceSession\n"
    "def _cpu_session(*a, **k):\n"
    "    k['providers'] = ['CPUExecutionProvider']\n"
    "    return _orig(*a, **k)\n"
    "_ort.InferenceSession = _cpu_session\n"
    "import sys\n"
    f"sys.argv = ['preprocess_data.py'] + {preprocess_args!r}\n"
    "import runpy\n"
    f"runpy.run_path('{WAN}/wan/modules/animate/preprocess/preprocess_data.py', run_name='__main__')\n"
)

ret = subprocess.run(
    [sys.executable, "-c", wrapper_code],
    cwd=str(WAN / "wan/modules/animate/preprocess"),
    env={
        **os.environ,
        "PYTHONPATH": (
            f"{WAN}:"
            f"{WAN}/wan/modules/animate/preprocess:"
            + os.environ.get("PYTHONPATH", "")
        ),
        "LD_LIBRARY_PATH": os.environ["LD_LIBRARY_PATH"],
    },
)
preprocess_time = time.time() - t0
print(f"\npreprocess return={ret.returncode}, time={preprocess_time:.1f}s "
      f"({preprocess_time/60:.1f} min)")

if ret.returncode != 0:
    print("PREPROCESS FAILED.")
    (OUT / "PREPROCESS_FAILED.txt").write_text(
        f"return={ret.returncode}, time={preprocess_time:.1f}s\nSee logs/run.log\n"
    )
    sys.exit(1)

print(f"Preprocessed outputs: {list(PROCESS_OUT.iterdir())[:10]}")

# ============================================================
# Step 2: Generate animation
# ============================================================
print("\n=== Generating animated video (Wan 2.2 Animate-14B) ===")
out_video = SAMPLES / "alice_animated.mp4"
t0 = time.time()

generate_cmd = [
    sys.executable,
    str(WAN / "generate.py"),
    "--task", "animate-14B",
    "--ckpt_dir", str(ANIMATE_DIR),
    "--src_root_path", str(PROCESS_OUT),
    "--refert_num", "1",
    "--save_file", str(out_video),
    "--frame_num", "33",  # ~2 sec @ 16fps; 4n+1
    "--offload_model", "True",
    "--convert_model_dtype",
    "--t5_cpu",
]
print("CMD:", " ".join(generate_cmd))

ret = subprocess.run(
    generate_cmd,
    cwd=str(WAN),
    env={
        **os.environ,
        "PYTHONPATH": str(WAN),
        "LD_LIBRARY_PATH": os.environ["LD_LIBRARY_PATH"],
    },
)
gen_time = time.time() - t0
print(f"\ngenerate return={ret.returncode}, time={gen_time:.1f}s ({gen_time/60:.1f} min)")

if ret.returncode == 0 and out_video.exists():
    print(f"\n=== ANIMATE-14B END-TO-END SUCCESS ===")
    print(f"  preprocess: {preprocess_time:.0f}s ({preprocess_time/60:.1f} min)")
    print(f"  generation: {gen_time:.0f}s ({gen_time/60:.1f} min)")
    print(f"  output: {out_video} ({out_video.stat().st_size/1e6:.1f} MB)")

    # Persist metric
    import csv
    csv_path = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/RAW_NUMBERS.csv"
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(csv_path, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow(["E-11-Animate", "preprocess_time", round(preprocess_time, 1), "seconds", 1, "CPU ONNX (no GPU on ARM)", ts])
        w.writerow(["E-11-Animate", "generation_time", round(gen_time, 1), "seconds", 1, "14B inference", ts])
        w.writerow(["E-11-Animate", "output_size_MB", round(out_video.stat().st_size/1e6, 1), "MB", 1, "alice + Wan example drive", ts])
        w.writerow(["E-11-Animate", "frame_num", 33, "frames", 1, "~2 sec @ 16fps", ts])
else:
    print("ANIMATE GENERATION FAILED")
