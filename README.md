# Character Engine

**AI-driven dynamic anime 3D character production pipeline**

A long-term research & engineering project. Hybrid architecture:
**traditional topology = skeleton (immutable), AI = flesh (filled into slots)**.

---

## Project Status

**Phase 0** — Architecture v0.2 drafted. Awaiting architect confirmation of 4 pending decisions before next PGX research round.

---

## Documents

### Active (read these)
| Path | Purpose |
|------|---------|
| [`PIPELINE_ARCHITECTURE_SPEC_v0.2.md`](./PIPELINE_ARCHITECTURE_SPEC_v0.2.md) ⭐ | **CURRENT architecture** — 4-tier model, AC-0..AC-8, full industry-standard adoption |
| [`PGX_OVERNIGHT_CAPABILITY_SURVEY.md`](./PGX_OVERNIGHT_CAPABILITY_SURVEY.md) | First overnight brief — broad capability survey (still useful reference) |
| [`test_assets/`](./test_assets/) | Reference materials (test character image, etc.) |
| `pgx_reports/` | PGX AI's experiment outputs |

### Historical (kept for traceability)
| Path | Purpose |
|------|---------|
| [`PIPELINE_ARCHITECTURE_SPEC.md`](./PIPELINE_ARCHITECTURE_SPEC.md) | v0.1 — superseded by v0.2 |
| [`PGX_TASK_ADDENDUM_001.md`](./PGX_TASK_ADDENDUM_001.md) | Paradigm comparison brief (completed; informed v0.2) |

---

## For the PGX AI

If you are the AI assistant on the PGX workstation:

1. **Read [`PIPELINE_ARCHITECTURE_SPEC_v0.2.md`](./PIPELINE_ARCHITECTURE_SPEC_v0.2.md) first** — this is the current authoritative architecture. v0.1 and ADDENDUM 001 are superseded but retained for context.
2. Wait for `PGX_TASK_ADDENDUM_002.md` — the next concrete task brief. It will be added once the architect confirms the 4 pending decisions in v0.2 §13.
3. Past survey reports in `pgx_reports/` are valid evidence base for the next round.

You have authority to:
- Skip / reorder / replace tasks based on decision-grade signal
- Add experiments not listed (`E-99-*`)
- Challenge architecture assumptions in writing

You **must**:
- Stop and write `BLOCKING.md` if you spot major design flaws or hardware risks
- Save failure cases — they're more valuable than successes
- Optimize for **architect's reading time**, not output volume

---

## Architectural Constraints (v0.2, binding)

- **AC-0** Traditional skeleton + AI flesh (highest principle — AI generates only inside fixed slots)
- **AC-1** 3D-first; 2D video as optional outermost effect (micro-motion etc.)
- **AC-2** Sandbox pipeline (extensible at runtime)
- **AC-3** Equipment × state explosion → real-time COMPOSITION (not real-time generation)
- **AC-4** Style and Identity decoupled (dual LoRA)
- **AC-5** Animation reduced from "open problem" to "Mixamo + VRM solved; only NPR/cage research remains"
- **AC-6** Fully open-source / no SaaS lock-in
- **AC-7** Strict offline production / online composition separation (Asset Contract bridge)
- **AC-8** Industry standards adopted only, not invented (VRM 1.0 / Mixamo / Modular Avatar / ARKit 52)

---

## Four-Tier Architecture (v0.2 core)

```
TIER 0  Industry standards     (immutable; zero AI)        — VRM 1.0, slots, UV, Mixamo, ARKit 52
TIER 1  Base avatar            (one-time human; AI assist) — VRoid-derived canonical body
TIER 2  AI slot filling        (per-asset; AI primary)     — Hunyuan3D + DAZ-style transfer + conformance
TIER 3  Online composition     (deterministic; zero AI)    — Three.js + shared skeleton + cache
```

---

## License

TBD (research-stage project)
