#!/usr/bin/env bash
# Background model preload — runs all night, idempotent (HF cache dedupe).
# Logs go to logs/model_downloads.log. Exit doesn't matter — caches persist.

set -u  # don't set -e, individual download failures shouldn't kill the script
export HF_HUB_ENABLE_HF_TRANSFER=1 2>/dev/null
LOG="/workspace/character-engine/pgx_reports/2026-04-26-overnight/E-16-environment/logs/model_downloads.log"
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1

source /workspace/character-engine/tools/pgx-env/bin/activate

dl() {
    local repo="$1"
    local note="${2:-}"
    echo "==== $(date -u +%H:%M:%SZ) DL: $repo  ($note) ===="
    python -c "
from huggingface_hub import snapshot_download
import sys, os
try:
    p = snapshot_download(repo_id='$repo', resume_download=True, max_workers=4)
    sz = sum(os.path.getsize(os.path.join(d,f)) for d,_,fs in os.walk(p) for f in fs if not os.path.islink(os.path.join(d,f)))
    print(f'OK  size={sz/1e9:.2f} GB  path={p}')
except Exception as e:
    print(f'FAIL  {type(e).__name__}: {e}')
    sys.exit(0)
"
}

echo "==== START: $(date -u) ===="
df -h /home/daniel/.cache/huggingface | tail -1

# === Tier 1: small, fast, definitely needed ===
dl "ai-forever/Real-ESRGAN" "Real-ESRGAN ~80MB"
dl "lllyasviel/Annotators" "DWpose / OpenPose annotators ~600MB"
dl "h94/IP-Adapter" "IP-Adapter weights ~3GB"
dl "h94/IP-Adapter-FaceID" "IP-Adapter FaceID ~1GB"
dl "InstantX/InstantID" "InstantID ~1.5GB"

# === Tier 2: SDXL family (二次元 inference ground truth) ===
dl "stabilityai/stable-diffusion-xl-base-1.0" "SDXL base ~7GB"
dl "OnomaAIResearch/Illustrious-XL-v0.1" "Illustrious 二次元 SDXL fine-tune ~7GB"

# === Tier 3: 3D ===
dl "tencent/Hunyuan3D-2" "Hunyuan3D 2.0 ~5GB"
dl "tencent/Hunyuan3D-2.1" "Hunyuan3D 2.1 if exists ~5GB"
dl "JeffreyXiang/TRELLIS-image-large" "TRELLIS large ~10GB"

# === Tier 4: Video (the expensive ones) ===
dl "Wan-AI/Wan2.2-T2V-A14B" "Wan 2.2 T2V 14B ~28GB"
dl "Wan-AI/Wan2.2-I2V-A14B" "Wan 2.2 I2V 14B ~28GB"

# === Tier 5: Rigging / animation (UniRig is small) ===
dl "VAST-AI/UniRig" "UniRig if on HF"
dl "fudan-generative-ai/UniRig" "UniRig variant"

# === Tier 6: Useful supplementary ===
dl "yzd-v/DWPose" "DWpose ONNX weights"

echo "==== DONE: $(date -u) ===="
df -h /home/daniel/.cache/huggingface | tail -1
du -sh /home/daniel/.cache/huggingface/hub/ 2>/dev/null
