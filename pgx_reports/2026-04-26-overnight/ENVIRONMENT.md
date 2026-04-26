# ENVIRONMENT — Reproducibility Manifest & ARM64 Tool Audit

**Goal**: Make this dataset of decisions reproducible tomorrow. Also: tell the architect _which open-source tools are install-clean today on aarch64+CUDA13_ so the next experiment doesn't waste a night.

---

## 1. Hardware (the actual one, not the spec'd one)

```
Hostname:        dd5947387542 (docker container "simba-lab")
Container:       simba-ngc-pytorch:26.01-py3-daniel  (NVIDIA NGC PyTorch 26.01)
GPU:             NVIDIA GB10 (Grace Blackwell desktop, NOT B200)
Architecture:    aarch64 (ARM64) — material constraint
Unified memory:  119.6 GB (CPU + GPU shared, NOT discrete VRAM)
Driver:          NVIDIA 580.95.05
CUDA:            13.0 (in-container)
OS (container):  Ubuntu 24.04.3 LTS (kernel 6.14.0-1015-nvidia)
Python:          3.12.3 (system) + 3.11.14 (uv-installed for bpy attempts)
GPU mode:        EXCLUSIVE_PROCESS + MPS daemon (default thread% = 100)
Disk free:       695 GB at /workspace (=host /home/daniel/Simba)
```

### What "128GB B200" in the spec really meant

The architecture spec says "128GB Blackwell architecture GPU workstation (B200 level)". This is **factually incorrect on three counts**:

| Spec assumption | Reality | Why it matters |
|---|---|---|
| B200 (data-center) | GB10 (desktop / DGX Spark class) | Different power envelope, different thermals, no NVLink |
| 128 GB discrete HBM3e | 119.6 GB **unified** memory | OS + processes + GPU all share the same physical pool |
| x86_64 (assumed) | aarch64 (ARM64) | A meaningful fraction of ML wheels do not build on ARM |

**Practical impact**: when the spec says "Hunyuan3D 2.0 (16GB) × 8 = use 128GB at once", in reality every other process on the box (OS, file cache, your vLLM serving Qwen3) also draws from the same 119GB pool. The achievable concurrency is much lower than the spec implies.

---

## 2. Persistent paths (rebuild-safe)

The container is rebuilt frequently. Anything not in these paths gets lost:

```
/workspace                       → host /home/daniel/Simba          (rw, work tree)
/home/daniel/.cache/huggingface  → same                              (rw, model weights, ~50GB+)
/home/daniel/.cache/uv           → same                              (rw, uv pkg cache)
/home/daniel/.local              → same                              (rw, pip-user / claude-code bins)
/home/daniel/.claude             → same                              (rw, this session state)
```

**Everything in this report is under `/workspace/character-engine/pgx_reports/2026-04-26-overnight/`** and survives container rebuilds.

---

## 3. Pre-installed (NGC container) — the things that just work

| Package | Version | ARM64 status |
|---|---|---|
| torch | 2.10.0a0+nv26.01 (NGC build) | ✅ first-class |
| torchvision | 0.25.0a0+nv26.01 | ✅ |
| flash_attn | **2.7.4.post1** | ✅ functional (smoke-tested with `flash_attn_func`) |
| triton | 3.6.0 | ✅ |
| safetensors | 0.7.0 | ✅ |
| numpy / scipy / cv2 / PIL | latest | ✅ |
| huggingface_hub | 1.3.1 | ✅ |

**Note**: Once you `pip install transformers` etc., a newer `torch 2.11.0+cu130` from PyPI gets pulled in alongside the NGC build (the NGC build registers ops differently). flash_attn from the NGC container _still works_ with both. Do not `pip uninstall torch` — you'll lose the NGC ops.

---

## 4. Installed tonight (in `tools/pgx-env/` venv with `--system-site-packages`)

```
transformers 5.6.2
diffusers    0.37.1
accelerate   1.13.0
peft         0.19.1
sentencepiece, omegaconf, imageio, kornia, controlnet_aux,
open-clip-torch, ftfy, regex, einops, hf_transfer
realesrgan + basicsr + facexlib + gfpgan
opencv-python-headless 4.13.0.92  (replaced opencv-python which pulls libxcb)
```

### Install gotchas hit & resolved tonight

| Issue | Fix |
|---|---|
| `realesrgan` weights from `ai-forever/Real-ESRGAN` are flat state_dict, not `{params:…}` wrapped | Wrote minimal RRDBNet inference; bypass `RealESRGANer` |
| `basicsr` imports `torchvision.transforms.functional_tensor` (removed in tv ≥ 0.17) | sed-patch `from torchvision.transforms.functional import rgb_to_grayscale` |
| `opencv-python` (GUI) requires libxcb at runtime; container has no X libs | `uv pip install opencv-python-headless` |
| uv cache stuck on antlr4-runtime with EACCES | `rm -rf .cache/uv/sdists-v9/pypi/antlr4-python3-runtime` |
| `bpy` PyPI has no Linux/ARM wheels (only macOS arm64 + Linux x86_64) | Pivoted retopology to community evidence + scripted x86 worker plan |
| `Blender 4.5.1 ARM64` (community build from lfdevs/blender-linux-arm64) needs libX11.so.6 at runtime | No sudo to install libx11; document as ARM-blocked |

---

## 5. Open-source tool ARM64 audit (the architecture spec's tools)

> Legend: ✅ install-clean • ⚠️ patch needed • ❌ can't install on this box • ❓ untested but suspect

### Image generation / character consistency

| Tool | Version | ARM64 | VRAM | License | Verdict |
|---|---|---|---|---|---|
| **Real-ESRGAN** (super-res) | ai-forever weights | ✅ tested | 0.76 GB peak | BSD-3 | **READY** — 0.6 s for our test image |
| **SDXL base** (`stabilityai/stable-diffusion-xl-base-1.0`) | 1.0 | ✅ pulled | ~7 GB fp16 | OpenRAIL-M | downloading |
| **Illustrious-XL** (anime SDXL FT) | v0.1 | ✅ pulled | ~7 GB | OpenRAIL-M | downloading |
| **IP-Adapter Plus SDXL** | h94 | ✅ pulled | +1 GB on SDXL | Apache-2.0 | downloading |
| **PuLID for SDXL** | guozinan | ❓ ARM untested | ~2 GB on SDXL | Apache-2.0 | needs SDXL backbone — defer |
| **InstantID** | InstantX | ✅ pulled | +2 GB on SDXL | Apache-2.0 | downloading |
| **OmniGen 2** | VectorSpaceLab | ❓ untested | ~12-15 GB | **Apache-2.0** | **direct open replacement for Flux Kontext** — Flux Kontext is closed-source, spec was wrong |
| **Flux dev / Flux.1** | BFL | ❓ ARM untested | ~24 GB | non-commercial | spec lists this; license issue separate from ARM |
| **Flux Kontext** | BFL | ❌ **NOT OPEN-SOURCE** | n/a | API-only | spec assumption error #2 |

### 3D generation

| Tool | Version | ARM64 | VRAM | License | Verdict |
|---|---|---|---|---|---|
| **Hunyuan3D 2.0** | tencent/Hunyuan3D-2 | ⚠️ custom CUDA ops (`custom_rasterizer`, `differentiable_renderer`) need compile — **untested on ARM** | shape: 6 GB / shape+texture: 16 GB | Apache-2.0 (model), tencent-hunyuan-noncomm (text) | **HIGH RISK** — the custom op compile is the failure point you'll hit |
| **Hunyuan3D 2.1** | June 2025 release | ⚠️ same risk | similar | Apache-2.0 | not validated |
| **Hunyuan3D 2.5** | June 2025 system tech report | ⚠️ same | similar — adds rigging support | Apache-2.0 | **adds auto-rigging** — directly relevant to AC-4 / E-08 |
| **Hunyuan3D 3.0** | site-only | ❓ unclear if OSS | unknown | unknown | likely closed |
| **TRELLIS** | microsoft/TRELLIS | ❌ "tested only on Linux" (= x86) | 16 GB | MIT | high ARM risk; multi-output (gaussian/RF/mesh) |

### Rigging / animation

| Tool | Version | ARM64 | VRAM | License | Verdict |
|---|---|---|---|---|---|
| **UniRig** | VAST-AI-Research | ❌ no ARM mention; needs spconv + flash_attn | **skinning ≥ 60 GB**; skeleton smaller | Apache-2.0 | Articulation-XL2.0 ckpt out; **Rig-XL/VRoid ckpt still in prep as of doc date** |
| **HumanRig / ASMR** | various academic | ❓ | unclear | research | low community traction |
| **Blender Rigify** | bundled with Blender | ❌ no Blender on ARM in this container (libX11 missing, no sudo); bpy PyPI has no Linux ARM wheels | CPU | GPL | **blocked tonight**; runs fine on x86 |
| **AccuRIG 2** | Reallusion | ❌ **closed-source SaaS** (free to use) — violates AC-6 | n/a | proprietary | spec self-contradicts |
| **DWpose** | IDEA-Research | ✅ ONNX branch avoids mmcv | 2-3 GB | Apache-2.0 | downloads in flight |
| **EasyMocap** | zju3dv | ❓ | depends on SMPL-X module | research | not pursued tonight |

### Video generation (the expensive ones)

| Tool | Version | ARM64 | VRAM (single GPU) | License | Verdict |
|---|---|---|---|---|---|
| **Wan 2.2 T2V-A14B** | Wan-Video/Wan2.2 | ❓ ARM untested | **80 GB** | Apache-2.0 | spec target; needs vLLM gone |
| **Wan 2.2 I2V-A14B** | same | ❓ | **80 GB** | Apache-2.0 | same |
| **Wan 2.2 TI2V-5B** | same | ❓ | **24 GB** (consumer-friendly) | Apache-2.0 | **the practical option** — 5 s @ 720p in <9 min on a 4090 |
| **Wan 2.2 Animate-14B** | same | ❓ | **23-50 GB** depending on host GPU | Apache-2.0 | **NEW — direct open-source character animation/replacement model**; **ref + driving video → animated character video**; **bypasses retarget pipeline entirely** |
| **HunyuanVideo** | tencent/HunyuanVideo | ❓ | ~60 GB at 720p | tencent-hunyuan-noncomm | larger than Wan; **redundant given Wan availability** |

> **Wan 2.2 LoRA caveat**: model card explicitly says "we do not recommend using LoRA models trained on Wan2.2, since weight changes during training may lead to unexpected behavior". This **directly contradicts the architecture spec's plan** to train a Character LoRA on Wan 2.2. See `ARCHITECT_DECISIONS.md`.

### LoRA training

| Tool | Version | ARM64 | VRAM | License | Verdict |
|---|---|---|---|---|---|
| **Kohya ss / sd-scripts** | kohya-ss/sd-scripts | ✅ pure pytorch, expected to work | 12 GB SDXL LoRA | Apache-2.0 | for SDXL/Illustrious LoRA |
| **diffusion-pipe** | tdrussell | ❓ deepspeed on ARM unclear | Wan 2.2 14B LoRA: 24 GB w/ block-swap (slow), realistically 48-80 GB | **GPL-3.0** ⚠️ (license re-mixed with ComfyUI in Q1 2026) | `wan_14b_min_vram.toml` exists; 24 GB possible at 5-10× slower |
| **ai-toolkit** | ostris | ❓ | similar to diffusion-pipe | Apache-2.0 | alternative |

### Retopology / mesh processing

| Tool | Version | ARM64 | License | Verdict |
|---|---|---|---|---|
| **Instant Meshes** (wjakob) | C++ binary | ⚠️ no ARM binary; build from source untested | GPL | gold-standard quad remesher |
| **Blender QuadriFlow** | built-in | ❌ no Blender on ARM here | GPL | community-recommended for AI mesh |
| **PyMeshLab** | cnr-isti-vclab | ✅ has ARM wheel (likely) | GPL | usable proxy |
| **trimesh** | mikedh | ✅ pure python | MIT | for mesh handling, no remesh |

### NPR rendering (out-of-scope for tonight)

| Tool | Type | License | Status |
|---|---|---|---|
| **HoyoToon** | Blender add-on | community | Blender-blocked |
| **festivities/Blender-miHoYo-Shaders** | Blender add-on | MIT | Blender-blocked |

---

## 6. The tools you _can definitely_ run tonight, no GPU contention

(verified to fit in the 6 GB free under vLLM):

- ✅ **Real-ESRGAN x4 / x2** (0.76 GB peak)
- ✅ **DWpose ONNX inference** (estimated 2-3 GB) — model weights downloading
- ✅ **CLIP-I scoring** with OpenCLIP ViT-bigG (~3 GB once loaded)
- ✅ **PyMeshLab CPU operations** (RAM only)
- ✅ **trimesh / pyrender** (RAM only)
- ✅ **LLM-as-Judge via vLLM Qwen3-30B** (no extra VRAM — uses already-loaded vLLM)

## 7. The tools that need vLLM out of the way

(everything ≥ 8 GB):

- ❌ SDXL inference → 7 GB
- ❌ IP-Adapter / PuLID / InstantID → 8-10 GB on SDXL
- ❌ Hunyuan3D 2.0 shape → 6 GB (borderline; texture pushes to 16 GB)
- ❌ Wan 2.2 14B inference → 80 GB
- ❌ Wan 2.2 5B inference → 24 GB (workable on freed GB10)
- ❌ Wan 2.2 Animate-14B → 23-50 GB
- ❌ UniRig skinning → 60 GB

## 8. Reproduction commands (for the next session)

```bash
# Activate environment
cd /workspace/character-engine
source tools/pgx-env/bin/activate

# Verify GPU + flash_attn alive
python -c "import torch, flash_attn; print('cuda', torch.cuda.is_available(), 'flash_attn', flash_attn.__version__)"

# Verify vLLM-as-Judge if running
python tools/llm_judge.py

# Run Real-ESRGAN x4 on the test image
python tools/run_realesrgan.py

# Continue post-blocking experiments
bash tools/run_p1_p4.sh   # to be created — see B4 task
```
