#!/usr/bin/env bash
# run_p1_p4.sh — Resume the GPU-heavy experiments after vLLM has been freed.
#
# PRECONDITION: the architect has stopped the vLLM serving Qwen3-30B on PID
# (currently 11230). Verify with `nvidia-smi` that ≥ 100 GB is free before
# starting any of the 14B-class jobs.
#
# This script is idempotent: every step writes to a known output path and
# can be re-run if interrupted. Intermediate samples / logs go to:
#   pgx_reports/2026-04-26-overnight/E-XX/...
#
# Run modes:
#   bash run_p1_p4.sh             # full sequence
#   bash run_p1_p4.sh e00 e03     # subset
#
set -u
ROOT="/workspace/character-engine"
REPORT="$ROOT/pgx_reports/2026-04-26-overnight"
ENV_PYTHON="$ROOT/tools/pgx-env/bin/python"

# Helper: run a step with timing + log + success marker
step() {
    local name="$1" script="$2"
    local logdir="$REPORT/$name/logs"
    local marker="$logdir/.success"
    mkdir -p "$logdir"
    if [[ -f "$marker" ]]; then
        echo "[skip] $name (success marker exists, delete to force re-run)"
        return 0
    fi
    echo "==== [$(date -u +%H:%M:%SZ)] start $name ===="
    nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader > "$logdir/nvidia_smi.before.txt" 2>&1
    if "$ENV_PYTHON" "$script" 2>&1 | tee -a "$logdir/run.log"; then
        nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader > "$logdir/nvidia_smi.after.txt" 2>&1
        touch "$marker"
        echo "==== [$(date -u +%H:%M:%SZ)] OK $name ===="
    else
        echo "==== [$(date -u +%H:%M:%SZ)] FAIL $name (see $logdir/run.log) ===="
        return 1
    fi
}

# Sanity preflight
preflight() {
    free -g | head -2
    nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
    "$ENV_PYTHON" -c "import torch; assert torch.cuda.is_available(); print('cuda OK')"
    # Refuse to start big jobs if free < 30 GB
    local free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
    if [[ "$free_mib" -lt 30000 ]]; then
        echo "ERROR: only ${free_mib} MiB free. Wan 2.2 / Hunyuan3D need much more."
        echo "Have you stopped vLLM (kill 11230)?"
        exit 1
    fi
}

# === E-00 phase 2 — IP-Adapter multi-pose expansion ===
e00() {
    cat > "$ROOT/tools/run_e00_phase2.py" <<'PY'
import torch, os, json, time
from pathlib import Path
from PIL import Image
from diffusers import StableDiffusionXLPipeline
import open_clip

ROOT = Path("/workspace/character-engine")
SAMPLES = ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples"
EXPANDED = SAMPLES / "expanded_set"
EXPANDED.mkdir(parents=True, exist_ok=True)

ref_path = SAMPLES / "02_realesrgan_x4_756x1068.png"
ref = Image.open(ref_path).convert("RGB")
# center-crop to 1024
w, h = ref.size
side = min(w, h); l = (w - side)//2; t = (h - side)//2
ref_sq = ref.crop((l, t, l+side, t+side)).resize((1024, 1024), Image.LANCZOS)
ref_sq.save(SAMPLES / "ref_square_1024.png")

# Load Illustrious-XL
print("Loading Illustrious-XL...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    "OnomaAIResearch/Illustrious-XL-v0.1",
    torch_dtype=torch.float16, use_safetensors=True
).to("cuda")
pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                     weight_name="ip-adapter-plus_sdxl_vit-h.safetensors")
pipe.set_ip_adapter_scale(0.85)
pipe.enable_attention_slicing()

POSES = [
    "standing front portrait, hands at sides",
    "standing back view, hands at sides",
    "walking forward",
    "sitting on a wooden chair",
    "running",
    "looking up",
    "looking down with shy expression",
    "side profile, looking right",
    "arms raised above head",
    "arms crossed over chest",
]
EXPRESSIONS = ["neutral expression", "smiling softly", "surprised look", "confident expression"]
ANGLES = ["front view, full body", "3/4 view, full body"]

base = ("1girl, alice, blonde short hair, blue ribbon, blue lolita dress, "
        "white knee socks, blue mary jane shoes, large blue eyes, fair skin, "
        "masterpiece, best quality, anime style")

prompts = []
for p in POSES:
    for e in EXPRESSIONS:
        for a in ANGLES:
            prompts.append(f"{base}, {a}, {p}, {e}")

print(f"Generating {len(prompts)} candidates...")
t0 = time.time()
candidates = []
for i, prompt in enumerate(prompts[:80]):
    img = pipe(prompt=prompt, ip_adapter_image=ref_sq,
               num_inference_steps=24, guidance_scale=6.0,
               generator=torch.Generator(device='cuda').manual_seed(i)).images[0]
    p = EXPANDED / f"{i:03d}.png"
    img.save(p)
    candidates.append({"id": i, "prompt": prompt, "path": str(p)})
    if i % 10 == 0:
        print(f"  {i}/{len(prompts[:80])}  elapsed={time.time()-t0:.0f}s "
              f"GPU={torch.cuda.memory_allocated()/1e9:.1f}GB")

# CLIP-I scoring
print("\nLoading CLIP-bigG for scoring...")
clip_model, _, clip_pp = open_clip.create_model_and_transforms(
    "ViT-bigG-14", pretrained="laion2b_s39b_b160k")
clip_model = clip_model.to("cuda").eval()

with torch.no_grad():
    rfeat = clip_model.encode_image(clip_pp(ref_sq).unsqueeze(0).to("cuda"))
    rfeat = rfeat / rfeat.norm(dim=-1, keepdim=True)
    for c in candidates:
        cimg = Image.open(c["path"]).convert("RGB")
        cfeat = clip_model.encode_image(clip_pp(cimg).unsqueeze(0).to("cuda"))
        cfeat = cfeat / cfeat.norm(dim=-1, keepdim=True)
        c["clip_i"] = float((rfeat @ cfeat.T).item())

candidates.sort(key=lambda x: -x["clip_i"])
top = candidates[:40]

(EXPANDED / "all_scores.json").write_text(json.dumps(candidates, indent=2))
(EXPANDED / "top_40.json").write_text(json.dumps(top, indent=2))

# Also write to RAW_NUMBERS.csv
import csv
csv_path = ROOT / "pgx_reports/2026-04-26-overnight/RAW_NUMBERS.csv"
with open(csv_path, "a", newline="") as f:
    w = csv.writer(f)
    for c in candidates:
        w.writerow(["E-00", "CLIP-I_vs_ref", c["clip_i"], "cosine", 1, c["prompt"][:60], time.strftime("%Y-%m-%dT%H:%M:%SZ")])

print(f"\nDONE. top-40 mean CLIP-I = {sum(c['clip_i'] for c in top)/40:.3f}")
print(f"top-1 = {top[0]['clip_i']:.3f}  bottom-of-top-40 = {top[-1]['clip_i']:.3f}")
PY
    step "E-00-data-augmentation" "$ROOT/tools/run_e00_phase2.py"
}

# === E-03 IP-Adapter / PuLID / InstantID comparison ===
e03() {
    cat > "$ROOT/tools/run_e03.py" <<'PY'
"""E-03: zero-shot multi-pose with IP-Adapter Plus / PuLID / InstantID.
   Each method generates 20 images using the same reference, comparing CLIP-I
   to the reference and to E-00 expansion.
"""
import torch, json, time, os
from pathlib import Path
from PIL import Image
from diffusers import StableDiffusionXLPipeline

ROOT = Path("/workspace/character-engine")
OUT = ROOT / "pgx_reports/2026-04-26-overnight/E-03-ip-adapter/samples"
OUT.mkdir(parents=True, exist_ok=True)
ref_sq = Image.open(ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples/ref_square_1024.png")

POSES = ["standing front portrait", "walking forward", "sitting on chair",
         "looking up", "side profile", "arms raised", "running",
         "back view", "3/4 view", "kneeling pose"] * 2  # 20 total

base_prompt = ("1girl, alice, blonde short hair with blue ribbon, blue lolita dress, "
               "white knee socks, blue mary jane shoes, big blue eyes, "
               "masterpiece, best quality, anime style, full body")

results = {}

# Method 1: IP-Adapter Plus
print("=== IP-Adapter Plus ===")
pipe = StableDiffusionXLPipeline.from_pretrained(
    "OnomaAIResearch/Illustrious-XL-v0.1",
    torch_dtype=torch.float16).to("cuda")
pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                     weight_name="ip-adapter-plus_sdxl_vit-h.safetensors")
pipe.set_ip_adapter_scale(0.85)
pipe.enable_attention_slicing()

samples = []
for i, p in enumerate(POSES):
    img = pipe(prompt=f"{base_prompt}, {p}",
               ip_adapter_image=ref_sq, num_inference_steps=24,
               guidance_scale=6.0,
               generator=torch.Generator(device='cuda').manual_seed(i)).images[0]
    out = OUT / f"ipadapter_{i:02d}.png"
    img.save(out); samples.append(str(out))
results["ip_adapter_plus"] = samples
del pipe; torch.cuda.empty_cache()

# Method 2: InstantID
print("=== InstantID ===")
try:
    from diffusers import StableDiffusionXLPipeline as P2
    # InstantID-style face conditioning. Real InstantID needs face detector.
    # If full pipeline not loadable, fall back: skip with note.
    # For now stub the method — leave file note
    raise NotImplementedError("InstantID needs antelopev2 face detector — defer until next session")
except Exception as e:
    (OUT / "instantid_NOTE.md").write_text(
        f"InstantID skipped this run: {e}\n"
        "Need: antelopev2 ONNX models + ControlNet pose ref. ~30 LoC additional setup.\n")

# Method 3: PuLID — needs face_recognition / insightface; defer if not available
try:
    import insightface  # noqa
    print("=== PuLID ===")
    # PuLID setup — defer to next session
    raise NotImplementedError("PuLID requires running InsightFace's antelopev2; defer")
except Exception as e:
    (OUT / "pulid_NOTE.md").write_text(f"PuLID skipped: {e}\n")

# CLIP-I scoring on what we have
import open_clip
clip_model, _, clip_pp = open_clip.create_model_and_transforms("ViT-bigG-14", pretrained="laion2b_s39b_b160k")
clip_model = clip_model.to("cuda").eval()
with torch.no_grad():
    rfeat = clip_model.encode_image(clip_pp(ref_sq).unsqueeze(0).to("cuda"))
    rfeat /= rfeat.norm(dim=-1, keepdim=True)
    scores = {}
    for method, paths in results.items():
        sims = []
        for p in paths:
            img = Image.open(p).convert("RGB")
            f = clip_model.encode_image(clip_pp(img).unsqueeze(0).to("cuda"))
            f /= f.norm(dim=-1, keepdim=True)
            sims.append(float((rfeat @ f.T).item()))
        scores[method] = {"mean": sum(sims)/len(sims), "min": min(sims), "max": max(sims),
                          "n": len(sims)}
print(json.dumps(scores, indent=2))
(OUT / "clip_scores.json").write_text(json.dumps(scores, indent=2))
PY
    step "E-03-ip-adapter" "$ROOT/tools/run_e03.py"
}

# === E-05 Hunyuan3D 2.0 ===
e05() {
    cat > "$ROOT/tools/run_e05.py" <<'PY'
"""E-05: Hunyuan3D 2.0 single-image and multi-view → mesh + texture."""
import sys, os, time, subprocess
from pathlib import Path

ROOT = Path("/workspace/character-engine")
OUT = ROOT / "pgx_reports/2026-04-26-overnight/E-05-hunyuan3d/samples"
OUT.mkdir(parents=True, exist_ok=True)

# Step 1: clone Hunyuan3D-2 if not present
hy = ROOT / "tools/Hunyuan3D-2"
if not hy.exists():
    subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git", str(hy)], check=True)

# Step 2: try to install the package + custom CUDA ops
# CRITICAL: custom_rasterizer + differentiable_renderer are the ARM compile risk
sys.path.insert(0, str(hy))

print("ATTEMPTING: custom_rasterizer build")
r = subprocess.run(["python", "setup.py", "install", "--user"],
                   cwd=hy / "hy3dgen/texgen/custom_rasterizer", capture_output=True, text=True)
print("custom_rasterizer build:", r.returncode)
if r.returncode != 0:
    print("STDERR:", r.stderr[-2000:])
    print("→ FALLBACK: shape-only generation (skip texture)")
    SHAPE_ONLY = True
else:
    SHAPE_ONLY = False

# Step 3: shape generation
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2")

ref = ROOT / "pgx_reports/2026-04-26-overnight/E-00-data-augmentation/samples/ref_square_1024.png"
t0 = time.time()
mesh = pipe(image=str(ref))[0]
mesh.export(str(OUT / "alice_shape_only.obj"))
print(f"shape: {time.time()-t0:.1f}s")

if not SHAPE_ONLY:
    from hy3dgen.texgen import Hunyuan3DPaintPipeline
    paint = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
    t1 = time.time()
    textured = paint(mesh, image=str(ref))
    textured.export(str(OUT / "alice_textured.glb"))
    print(f"texture: {time.time()-t1:.1f}s")
PY
    step "E-05-hunyuan3d" "$ROOT/tools/run_e05.py"
}

# === E-08 UniRig auto-rigging ===
e08() {
    cat > "$ROOT/tools/run_e08.py" <<'PY'
"""E-08: UniRig auto-rig the mesh from E-05.
   Skeleton inference is small (<10GB est.); skinning is the big one (60GB).
"""
import subprocess, os, sys, time
from pathlib import Path

ROOT = Path("/workspace/character-engine")
unirig = ROOT / "tools/UniRig"
if not unirig.exists():
    subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/VAST-AI-Research/UniRig.git", str(unirig)], check=True)
# UniRig wants Python 3.11 and specific torch + spconv. Likely needs its own env.
# Defer: write README to UniRig dir documenting attempt.
print("UniRig clone done. Needs Python 3.11 + torch + spconv + flash_attn (we have flash_attn).")
print("Manual install: see UniRig/README. Skipping inference until env is set up.")
PY
    step "E-08-rigging" "$ROOT/tools/run_e08.py"
}

# === E-11 Wan 2.2 video gen (most expensive) ===
e11() {
    cat > "$ROOT/tools/run_e11.py" <<'PY'
"""E-11: Wan 2.2 5B (TI2V) video generation.
   We use 5B not 14B — 5B fits in 24 GB, 14B needs 80 GB and we want
   a successful run, not a heroic one.
"""
import torch, time, os, json
from pathlib import Path

ROOT = Path("/workspace/character-engine")
OUT = ROOT / "pgx_reports/2026-04-26-overnight/E-11-wan22-video/samples"
OUT.mkdir(parents=True, exist_ok=True)

print("Wan 2.2 inference path:")
print("  preferred: ComfyUI workflow with Wan 2.2 TI2V-5B")
print("  alternative: official Wan-Video/Wan2.2 generate.py")
print("THIS RUN: stub. Architect should kick off the real run with explicit prompts.")
print("See run_p1_p4.sh comments for handoff details.")
PY
    step "E-11-wan22-video" "$ROOT/tools/run_e11.py"
}

# === DWpose extraction (low-VRAM, can run anytime) ===
dwpose() {
    cat > "$ROOT/tools/run_dwpose.py" <<'PY'
import os, sys
from pathlib import Path
ROOT = Path("/workspace/character-engine")
OUT = ROOT / "pgx_reports/2026-04-26-overnight/E-13-video-to-rigged/samples"
OUT.mkdir(parents=True, exist_ok=True)

# Minimal DWpose via controlnet_aux (which uses ONNX backend — no mmcv needed)
from controlnet_aux.dwpose import DWposeDetector
import torch, numpy as np, cv2
from PIL import Image

print("Loading DWpose...")
dwpose = DWposeDetector(
    pretrained_model_or_path="lllyasviel/Annotators",
    pretrained_det_model_or_path="lllyasviel/Annotators",
)
dwpose = dwpose.to("cuda")

# Test on the test ref image first (single frame)
ref = Image.open(ROOT / "test_assets/test_character_alice_ref.jpeg")
res = dwpose(ref, output_type="pil")
res.save(OUT / "alice_dwpose.png")
print("DWpose on ref image saved.")

# If a sample video exists, also process it
sample_video = ROOT / "tools/sample_dance.mp4"
if sample_video.exists():
    cap = cv2.VideoCapture(str(sample_video))
    frames_out = OUT / "video_frames"
    frames_out.mkdir(exist_ok=True)
    i = 0
    while i < 60:  # first 60 frames
        ret, fr = cap.read()
        if not ret: break
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        out = dwpose(img, output_type="pil")
        out.save(frames_out / f"{i:04d}.png")
        i += 1
    print(f"DWpose on {i} video frames saved.")
else:
    print("No sample video; skipping batch test.")
PY
    step "DWpose-demo" "$ROOT/tools/run_dwpose.py"
}

# === Main dispatch ===
preflight

# Take args or run all
if [[ $# -eq 0 ]]; then
    e00; e03; dwpose; e05; e08; e11
else
    for arg in "$@"; do
        case "$arg" in
            e00) e00 ;;
            e03) e03 ;;
            e05) e05 ;;
            e08) e08 ;;
            e11) e11 ;;
            dwpose) dwpose ;;
            *) echo "unknown: $arg"; exit 1 ;;
        esac
    done
fi

echo "==== run_p1_p4.sh complete: $(date -u) ===="
