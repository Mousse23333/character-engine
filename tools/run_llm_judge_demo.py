"""Demonstrate LLM-as-Judge on real-style architectural reasoning tasks.

This is a live demonstration of how Qwen3-30B (via the existing vLLM endpoint)
can be used to do LLM-as-Judge work for the character-engine project, even
without GPU resources for image-VLM evaluation.

Used cases demonstrated:
1. Score consistency between a reference description and a hypothetical
   IP-Adapter generation description
2. Validate the proposed run_p1_p4.sh E-00 generation config
3. Independent architectural review of one Architecture Constraint with
   evidence from this report
"""
import json, sys
sys.path.insert(0, '/workspace/character-engine/tools')
from llm_judge import consistency_score, review_generation_config, architectural_review, health_check

OUT = "/workspace/character-engine/pgx_reports/2026-04-26-overnight/E-99-discoveries/llm_judge_demo.json"

print("Health check:", health_check())
print()

# ============================================================
# 1. Consistency scoring on hypothetical IP-Adapter outputs
# ============================================================
print("=== TEST 1: LLM-judge ranks IP-Adapter quality vs ref ===")
ref_desc = ("Anime girl, blonde short hair (chin-length), large blue ribbon "
            "tied on top of head, sky-blue Lolita-style dress with white lace "
            "trim, white knee-high socks, blue Mary Jane shoes with strap, "
            "very large sky-blue eyes, pale skin, fair complexion, "
            "front-facing standing portrait, plain gray background")

candidates = {
    "ipadapter_high_fidelity": (
        "Anime girl, blonde short hair, large blue bow on head, "
        "blue dress with white lace, white socks, blue strapped shoes, "
        "big blue eyes, fair skin, full body, neutral pose, gray background"
    ),
    "ipadapter_drift_outfit": (
        "Anime girl, blonde short hair, blue ribbon, dark navy gothic dress "
        "with red lace trim, black thigh-high socks, black boots, "
        "large blue eyes, pale skin, dynamic pose, dark background"
    ),
    "ipadapter_drift_identity": (
        "Anime girl, brown wavy long hair, no ribbon, blue mini skirt with "
        "white shirt, white sneakers, brown eyes, tan skin, walking, "
        "outdoor garden scene"
    ),
}

results = {}
for name, desc in candidates.items():
    print(f"\n--- judging {name} ---")
    s = consistency_score(ref_desc, desc)
    print(json.dumps(s, indent=2, ensure_ascii=False))
    results[name] = s

# Score ranking
print("\n=== Score ranking ===")
for name in sorted(results, key=lambda k: -results[k].get("overall_score", 0)):
    score = results[name].get("overall_score", "ERR")
    verdict = results[name].get("verdict", "ERR")
    print(f"  {score}/10  {verdict:8s}  {name}")

# ============================================================
# 2. Validate generation config for E-00 IP-Adapter run
# ============================================================
print("\n\n=== TEST 2: LLM-judge reviews E-00 IP-Adapter config ===")
config = {
    "experiment": "E-00 phase 2 — single ref → 80 candidates",
    "base_model": "OnomaAIResearch/Illustrious-XL-v0.1",
    "ip_adapter": "h94/IP-Adapter sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors",
    "ip_adapter_scale": 0.85,
    "num_inference_steps": 24,
    "guidance_scale": 6.0,
    "n_candidates": 80,
    "prompt_template": "1girl, alice, blonde short hair, blue ribbon, blue lolita dress, white knee socks, blue mary jane shoes, large blue eyes, fair skin, masterpiece, best quality, anime style, {angle}, {pose}, {expression}",
    "filter_step": "CLIP-I (ViT-bigG-14, laion2b_s39b_b160k) top-40",
    "intended_use": "training data for Illustrious Character LoRA"
}
review = review_generation_config(config)
print(json.dumps(review, indent=2, ensure_ascii=False))
results["e00_config_review"] = review

# ============================================================
# 3. Independent architectural review of AC-5
# ============================================================
print("\n\n=== TEST 3: independent review of AC-5 (Animation is open problem) ===")
evidence = """AC-5 says: 'Animation is an open problem in 2026; AI 在该环节当前业界开源解最弱'.

Evidence collected this overnight:
- DWpose / OpenPose return 0 keypoints on anime characters (distribution
  mismatch with COCO-WholeBody training data)
- UniRig (SIGGRAPH 2025) requires 60 GB VRAM for skinning
- UniRig anime-trained checkpoint (Rig-XL/VRoid) is still in preparation
- Wan 2.2 model card explicitly discourages LoRA training
- BUT: Wan 2.2 Animate-14B (Apache-2.0) does single-image + driving-video
  → animated character video in one model, 23-50 GB single-GPU
- Hunyuan3D 2.5 added integrated rigging support
- Mixamo offline FBX library is redistributable and works for retargeting

The architecture wants: rigged 3D animation assets that can drive a
character in PIXI 2D game via 3D→2D projection. The bottleneck is the
'rigged 3D' part — Wan 2.2 Animate produces 2D video, not rigged motion.
"""
ac5_review = architectural_review("AC-5", evidence)
print(json.dumps(ac5_review, indent=2, ensure_ascii=False))
results["ac5_independent_review"] = ac5_review

# ============================================================
# Persist
# ============================================================
with open(OUT, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nSaved → {OUT}")
