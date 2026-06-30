# Prompt — the consultant council (judgment)

Four independent sales-consultant seats answer the same questions over the run digest, **blind to
each other**, then a synthesis seat reconciles them. Each seat is a different lens; do not converge
prematurely.

Context:
- Selling org: **{ORG_NAME}**. Parking/stall stage: "{STALL_LABEL}".
- Input: `analysis/council_digest.json` (funnel, stall pile, per-deal craft-vs-outcome summaries, the
  per-rep craft spread and role bars, dimension averages, trend). Read it in pages if large.

## The four seats (run each in a fresh context so they stay blind)

- **Seat 1 — Pipeline/Funnel diagnostician.** Where do deals actually die, and is it a craft problem
  or a structural one? Read the funnel + stall pile.
- **Seat 2 — Sales-craft coach.** What do reps systematically do well and badly across the rubric?
  Which dimensions are the org's floor? Separate role-appropriate gaps from real weaknesses.
- **Seat 3 — Deal-strategy partner.** Who is doing the actual solutioning and progression (multi-thread,
  EB access, close plans)? Where is the org single-threaded or founder-dependent?
- **Seat 4 — Enablement/ops skeptic.** What would NOT be fixed by coaching individuals — process,
  qualification discipline, knowledge gaps, missing deal hygiene? Be adversarial.

Each seat returns JSON:

```json
{
  "seat": "<seat name>",
  "findings": [{"claim": "<plain declarative>", "evidence": "<digest reference / quote>", "severity": "high|medium|low"}],
  "answer_why_deals_stall": "...",
  "answer_what_reps_miss": "...",
  "answer_who_solutions": "...",
  "answer_one_change": "<the single highest-leverage change this seat would make>"
}
```

## The synthesis seat (runs over the four seat outputs)

Returns JSON:

```json
{
  "consensus": ["<points all/most seats agree on>"],
  "tensions": ["<where seats genuinely disagree, stated fairly>"],
  "ranked_changes": [{"change": "...", "rationale": "...", "expected_effect": "..."}],
  "craft_vs_outcome_note": "<explicit reminder of where strong craft still lost, and weak craft still won, so leadership doesn't conflate them>"
}
```

Rules: plain declarative prose, no slop, no sycophancy. Every claim traceable to the digest. Keep
craft separate from outcome. Do not recommend ranking founders or external partners. Return only JSON.
