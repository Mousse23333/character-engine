# Character Engine

**AI-driven dynamic anime 3D character production pipeline**

A long-term research & engineering project to build a hybrid pipeline where AI handles
all asset production (the offline world), while traditional GPU rendering / physics /
composition handle real-time consumption (the online world).

---

## Project Status

**Phase 0** — Abstract architecture defined. PGX overnight capability survey pending.

---

## Documents

| Path | Purpose |
|------|---------|
| [`PIPELINE_ARCHITECTURE_SPEC.md`](./PIPELINE_ARCHITECTURE_SPEC.md) | Architecture record: paradigm, invariants (AC-0..7), offline/online separation, hybrid route |
| [`PGX_OVERNIGHT_CAPABILITY_SURVEY.md`](./PGX_OVERNIGHT_CAPABILITY_SURVEY.md) | Overnight task brief #1 — broad capability survey |
| [`PGX_TASK_ADDENDUM_001.md`](./PGX_TASK_ADDENDUM_001.md) ⭐ | **CURRENT TASK** — parallel evaluation of 2D vs 3D paradigms (AC-0 introduced) |
| [`test_assets/`](./test_assets/) | Reference materials (test character image, etc.) |
| `pgx_reports/` | Created by PGX AI — survey results land here |

---

## For the PGX AI

If you are the AI assistant on the PGX 128GB Blackwell workstation:

1. Read [`PIPELINE_ARCHITECTURE_SPEC.md`](./PIPELINE_ARCHITECTURE_SPEC.md) first (background, ~20 min)
2. Then read [`PGX_OVERNIGHT_CAPABILITY_SURVEY.md`](./PGX_OVERNIGHT_CAPABILITY_SURVEY.md) (your actual brief, ~15 min)
3. Execute experiments in `pgx_reports/<date>/`
4. Produce `EXECUTIVE_SUMMARY.md` + `ARCHITECT_DECISIONS.md` for the human architect to read in 5 min after waking up

You have authority to:
- Skip / reorder / replace tasks based on what produces decision-grade signal
- Add experiments not listed (`E-99-*`)
- Challenge the architecture document's assumptions in writing

You **must**:
- Stop and write `BLOCKING.md` if you spot major design flaws or hardware risks
- Save failure cases — they're more valuable than successes
- Optimize for **architect's reading time**, not your output volume

---

## Architectural Constraints (binding)

- **AC-1** 3D-first; 2D rendering allowed; pure 2D excluded
- **AC-2** Sandbox pipeline (extensible at runtime)
- **AC-3** Equipment × state space explosion → real-time composition required
- **AC-4** Style and Identity decoupled
- **AC-5** Animation rigging is open problem (long-term research)
- **AC-6** Fully open-source / replaceable / no SaaS lock-in
- **AC-7** Strict offline production / online composition separation

---

## License

TBD (research-stage project)
