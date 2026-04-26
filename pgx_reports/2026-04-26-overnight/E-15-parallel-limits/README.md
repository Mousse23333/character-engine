# E-15 — Hardware Parallel Limits

**Status**: ⛔ **Cannot test under current vLLM blocker**. The result we'd get is "vLLM holds 103 GB; everything else has to fit in 6 GB".
**Architect's question**: implicit Q (T4 from spec) — "what's the night-batch parallel ceiling?"

## What the spec assumed

> "Hunyuan3D 2.0 (16GB) × 8 路 / HunyuanVideo 720p (60-80GB) × 1 路 / Flux/Illustrious × 5+ 路 / LoRA train + ComfyUI + 视频生成 同时"

This assumed **128 GB discrete VRAM**. The reality is **119 GB unified memory shared with OS+vLLM+caches**. The above ceiling is too optimistic by ~50 % at minimum, and on this specific machine (with Qwen3-30B vLLM running) by ~95 %.

## What we can confidently say without measuring

### When vLLM is gone
- **Wan 2.2 14B inference**: 80 GB. Cannot run alongside anything else of consequence.
- **Wan 2.2 Animate-14B**: 23-50 GB. Could pair with **one** Hunyuan3D 2.0 shape (6 GB) and **one** SDXL (7 GB), with margin.
- **Wan 2.2 5B (TI2V)**: 24 GB. Most flexible — pair with several SDXL/IP-Adapter inferences.
- **Hunyuan3D 2.0 shape only**: 6 GB. **8× concurrent at 48 GB total** is plausible. The spec was right about this one.
- **Hunyuan3D 2.0 textured**: 16 GB. **2-3× concurrent at 32-48 GB**, leaving room for SDXL.
- **SDXL/Illustrious + IP-Adapter**: 8-9 GB. **4-5× concurrent at ~40 GB**.
- **LoRA training (SDXL)**: 18-22 GB at fp16. Single instance pair-able with SDXL inferences.
- **LoRA training (Wan 2.2 14B with diffusion-pipe block-swap)**: 24-80 GB depending on swap. Single instance only, can't share.

### Best night-batch schedules

**For maximum throughput (lots of cheap data)**:
```
Hunyuan3D 2.0 shape × 6  (= 36 GB)
SDXL+IP-Adapter × 4      (= 32 GB)
DWpose batch processing  (= 3 GB)
Headroom + OS            (= 48 GB)
```

**For maximum quality (bigger models, fewer)**:
```
Wan 2.2 14B inference × 1  (= 80 GB)
SDXL inference × 1         (= 8 GB)
DWpose                     (= 3 GB)
Headroom                   (= 28 GB)
```

**For training a Character LoRA + serving inference for QA**:
```
LoRA train (SDXL) × 1      (= 22 GB)
SDXL+IP-Adapter inference × 2 (= 18 GB)
Headroom + OS              (= 79 GB)  // gen test images during training
```

## What is hard to estimate without measuring

- **Memory fragmentation**. Unified memory + many small allocations may cause early OOM well before sum-of-allocations equals total.
- **Bus contention**. GB10 has fewer NVLink lanes than B200; many concurrent CUDA streams may serialize.
- **MPS thread % default**. Currently set to 100 % (single-tenant); for true parallelism, drop to 4 % per the entrypoint default. **The architect's other entrypoint script already has this knob.**

## What we'd test in 30 minutes (when GPU freed)

```bash
# 1. Set MPS to 25% (allow up to 4 concurrent processes)
mps-set-pct 25

# 2. Launch increasing concurrency
# Round 1: 1× SDXL
# Round 2: 2× SDXL
# Round 3: 4× SDXL
# Round 4: 4× SDXL + 2× Hunyuan3D shape
# Round 5: + 1× LoRA train
# Round 6: + Wan 2.2 5B

# Find the OOM / slowdown wall.
```

This is **a half-hour experiment, not an overnight one**. It belongs in a tooling-readiness sprint, not a capability survey.

## Architectural insight

For your **dev/research** environment: 119 GB unified is plenty for serial heavy experiments + one parallel light job (vLLM as evaluator).

For **production batch jobs** (the spec's "夜间批跑"): plan for either
- (a) a **dedicated** workstation per heavy job, OR
- (b) a **scheduler** that runs jobs in series and co-schedules small ones.

The spec's "all running concurrently" framing is aspirational. The realistic posture is **batch-sequenced with light cohabitation**.
