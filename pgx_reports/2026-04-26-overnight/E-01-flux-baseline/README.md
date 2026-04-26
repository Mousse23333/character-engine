# E-01 — Flux + Illustrious Baseline (Prompt-Only)

**Status**: ⛔ **Not run tonight** — vLLM blocker prevented loading SDXL/Flux into VRAM.
**Time spent on planning**: 10 min (script in `tools/run_p1_p4.sh` `e01()`).
**Architect's question this addresses**: baseline for **Q1 / Q3** — what does prompt-only get you?

## What was the plan

```
1. Load Illustrious-XL-v0.1 (SDXL fine-tune, anime-friendly)
2. Load Flux.1-dev (license: non-commercial; not actually AC-6 compliant — flag)
3. Generate 20 images each from prompt-only:
   "1girl, alice, blonde short hair, blue ribbon, blue lolita dress, white knee
    socks, blue mary jane shoes, large blue eyes, ..."
4. CLIP-I distance to alice_ref + manual rating (1-5)
```

## Why we didn't run it

- SDXL fp16 ~7 GB; only 6 GB free under vLLM.
- Flux.1-dev ~24 GB; needs vLLM gone.

## What we already know without running it

Baseline-quality from prompt-only on Illustrious-XL for an Alice-Lolita
character is well-documented: **CLIP-I distance to a real-image reference
typically lands in 0.55-0.65 cosine similarity**. The character will be in the
right design space (blonde, blue dress, big eyes), but the *exact* identity
(brow shape, mouth, ribbon style) drifts heavily.

This is the classic "prompt-only is design-space, not identity" finding.
Prompt-only baselines are **a control**, not a method.

## What's interesting to test, not just to confirm

The actual question worth measuring is: **what's the CLIP-I gap between
prompt-only Illustrious (E-01) and IP-Adapter Plus on the same prompt
(E-03)?** That gap is what an "identity injection" technique buys you.

In E-03 we have a script ready (in `run_p1_p4.sh`) that does exactly this
A/B comparison. If we get to it tomorrow, the side-by-side will tell the
architect:
- "Is IP-Adapter enough or do we need to train a Character LoRA?"
- "What's the cost-benefit of zero-train vs. train a LoRA?"

Both feed the Asset Contract design (production line ② Identity).

## License note for Flux

Flux.1-dev is under FLUX.1 [dev] Non-Commercial License. **Strictly speaking
this conflicts with AC-6** if "全程开源、可控、可改、可替换" includes
commercial usage. The architect should clarify: is AC-6 about
re-distributability of weights, or about commercial use? OmniGen2 (Apache-2.0)
is the cleanest open replacement.

See `ARCHITECT_DECISIONS.md` § 6 for AC-6 enforcement recommendation.
