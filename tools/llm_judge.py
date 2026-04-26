"""LLM-as-Judge wrapper using the locally-running vLLM Qwen3-30B endpoint.

Usage:
    judge = LLMJudge()
    score = judge.score_anime_consistency(ref_path="ref.png", candidate_path="cand.png")

The vLLM endpoint at http://localhost:8000 is for text-only Qwen3-30B —
it cannot accept images directly. We provide three modes:
  1. text_describe: caller supplies textual descriptions of ref + candidate
  2. paired_score:  caller supplies image embeddings (we score similarity claim)
  3. config_check:  validate a generation config makes sense for an anime LoRA

For actual image-image VLM judging, use a local CLIP / DINO embedding distance,
not LLM-as-Judge. This wrapper exists for prompt validation, generation config
review, and qualitative assessment of textual descriptions.
"""
from __future__ import annotations
import json, requests, time

VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_ID = "qwen3-30b-a3b"


def _chat(messages, max_tokens=512, temperature=0.0, timeout=60):
    """Single chat completion against local vLLM."""
    r = requests.post(VLLM_URL, json={
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def consistency_score(ref_description: str, candidate_description: str) -> dict:
    """Given textual descriptions of two images, return a structured score."""
    prompt = f"""You are an evaluator for anime character consistency.
You will be given two textual descriptions: a reference character and a candidate generation.
Score the candidate on a 0-10 scale across these axes, and identify discrepancies.

Reference:
{ref_description}

Candidate:
{candidate_description}

Respond with strict JSON:
{{
  "identity_match": <0-10>,
  "outfit_match": <0-10>,
  "hair_match": <0-10>,
  "color_palette_match": <0-10>,
  "pose_appropriateness": <0-10>,
  "overall_score": <0-10>,
  "discrepancies": ["string", ...],
  "verdict": "match" | "drift" | "fail"
}}
"""
    out = _chat([
        {"role": "system", "content": "You are a precise anime character consistency evaluator. Output strict JSON only."},
        {"role": "user", "content": prompt}
    ])
    # Best-effort JSON extraction
    s = out.find("{"); e = out.rfind("}") + 1
    if s >= 0 and e > s:
        try:
            return json.loads(out[s:e])
        except Exception:
            pass
    return {"raw": out, "parse_error": True}


def review_generation_config(config: dict) -> dict:
    """Sanity-check a Wan/SDXL/HunyuanVideo generation config for anime LoRA."""
    prompt = f"""You are a senior generative AI engineer.
Review this generation/training config for an anime character pipeline.
Identify problems, suboptimal choices, and risk factors.

Config:
{json.dumps(config, indent=2)}

Respond with strict JSON:
{{
  "issues": [{{"severity": "high|med|low", "field": "...", "comment": "..."}}],
  "suggestions": ["..."],
  "overall_verdict": "good|acceptable|broken"
}}
"""
    out = _chat([
        {"role": "system", "content": "You are a generative-AI config reviewer."},
        {"role": "user", "content": prompt}
    ])
    s = out.find("{"); e = out.rfind("}") + 1
    if s >= 0 and e > s:
        try:
            return json.loads(out[s:e])
        except Exception:
            pass
    return {"raw": out, "parse_error": True}


def architectural_review(constraint_id: str, evidence: str) -> dict:
    """Have the LLM challenge an Architecture Constraint given experimental evidence.

    Useful for letting Qwen3 sanity-check our own architectural conclusions.
    """
    prompt = f"""You are an independent senior architect reviewing the
character-engine project. Below is one of the architectural constraints (AC-X)
and experimental evidence collected. Decide if the AC should be kept, modified,
or dropped, and explain your reasoning.

Constraint ID: {constraint_id}
Evidence:
{evidence}

Respond with strict JSON:
{{
  "verdict": "keep|modify|drop",
  "reasoning": "...",
  "proposed_modification": "..." (if applicable, else null),
  "confidence": 0.0-1.0
}}
"""
    out = _chat([
        {"role": "system", "content": "You are an independent architectural reviewer. Push back when warranted."},
        {"role": "user", "content": prompt}
    ], max_tokens=800)
    s = out.find("{"); e = out.rfind("}") + 1
    if s >= 0 and e > s:
        try:
            return json.loads(out[s:e])
        except Exception:
            pass
    return {"raw": out, "parse_error": True}


def health_check() -> dict:
    """Verify endpoint is alive and responsive. Used in scripts before batch."""
    t0 = time.time()
    try:
        out = _chat([{"role": "user", "content": "Reply with the word: ok"}],
                    max_tokens=5, timeout=10)
        return {"alive": True, "latency_ms": int((time.time()-t0)*1000), "reply": out.strip()[:30]}
    except Exception as e:
        return {"alive": False, "error": str(e)}


if __name__ == "__main__":
    # Quick smoke test
    print("health:", health_check())

    # Test the consistency scorer
    ref = "1girl, blonde short hair, blue ribbon hair accessory, blue Lolita dress, " \
          "white knee-high socks, blue mary jane shoes, large blue eyes, fair skin, " \
          "front-facing portrait, plain gray background"
    cand_good = "1girl, blonde short hair with blue bow on top, dark blue Lolita dress, " \
                "white socks, blue shoes, big eyes, standing pose, neutral background"
    cand_bad = "1girl, brown long hair, red dress, no socks, sneakers, walking outdoors"

    print("\nGOOD candidate:")
    print(json.dumps(consistency_score(ref, cand_good), indent=2, ensure_ascii=False))

    print("\nBAD candidate:")
    print(json.dumps(consistency_score(ref, cand_bad), indent=2, ensure_ascii=False))
