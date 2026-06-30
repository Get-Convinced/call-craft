# RUNBOOK: running the sales-call audit

This is the operator procedure. Read it once before you start. The phase list and the non-negotiables
in `SKILL.md` hold throughout. You are the conductor: judgment is done by model agents you spawn,
plumbing is done by stdlib Python scripts in `scripts/`. A script never reads a transcript for
meaning, and you never score the whole corpus in one pass.

Scripts are stdlib-only Python 3.9+. There is no install step.

Set the run directory once and keep it set. Every script reads it (or takes `--workdir`):

```bash
export AUDIT_WORKDIR=/abs/path/to/this-run
```

A finished run directory:

```
$AUDIT_WORKDIR/
  config.json            Phase 4
  company_context.md     Phase 2
  .env                   optional, API mode only, gitignored, never committed
  raw/                   the operator's export. READ ONLY. never committed.
    transcripts/**       one file per call (Read.ai, Gong, Fireflies, Otter, Zoom, or plain text)
    crm/deals.csv  crm/stage_history.csv  crm/notes.csv   (all optional)
    docs/**              optional operator collateral folded into company research
  canonical/             Phase 3 output (transcripts.json, deals.json, notes.json, stage_history.json)
  analysis/              Phases 2 and 5 through 10 output
    company_context sources, roles.json, call_company.json,
    call_out/call_<id>.json, postmortem/deal_<unit>.json,
    adherence/*.json, council_output.json, report_data.json
  work/<run>/report.html Phase 11 output, the one self-contained report
```

Run top to bottom. Each phase below lists its **inputs**, the **command or prompt** to run, the
**gate** that must be true before you advance, and the **degradation tier** for a missing optional
input. Do not advance past a failed gate.

A note on the two execution paths, true for every judgment phase (2, 5, 7, 8, 9, 10):

- **Host-agent mode (default).** Each judgment unit is one task. Spawn a subagent per task, filling
  the matching prompt template from `prompts/` with that one unit of input, and run independent tasks
  in parallel up to the host's concurrency limit. The model is whatever your CLI runs. No key, no
  setup. Prefer this whenever a subagent capability exists. See `engine/README.md`.
- **API mode (opt-in).** For very large corpora or headless runs, the operator puts an
  OpenAI-compatible endpoint and key in a gitignored `$AUDIT_WORKDIR/.env`, and the `scripts/*_via_api.py`
  drivers loop the same prompt templates through `engine/llm.py`. The output JSON is identical, so the
  plumbing never cares which path ran. See `engine/README.md`.

---

## Phase 0: resolve engine and working folder

**Inputs:** none beyond the data-folder argument the operator gave the skill.

**Do:**

1. Resolve the engine. If your CLI can spawn subagents, use host-agent mode (the default); there is
   nothing to set up. Only fall to API mode if the operator asks for it or the corpus is too large to
   run as subagents. If API mode, confirm `$AUDIT_WORKDIR/.env` exists with the generic vars
   (`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`) and that it is gitignored. Never write
   a key into the skill.
2. Create the working tree:

   ```bash
   mkdir -p "$AUDIT_WORKDIR"/{raw/transcripts,raw/crm,raw/docs,canonical,analysis,work}
   ```

3. Tell the operator, in one line, which engine you resolved and roughly how many model reads the run
   will cost: about one read per in-scope call for scoring, one per deal for the post-mortem, plus a
   research swarm, role inference, an adherence sample, and the council. For a few hundred calls this
   is a large but routine batch. For thousands, plan a scoped pilot (Phase 4 `config.scope`).

**Gate:** the `raw/` tree exists, the engine is resolved and stated to the operator, and (API mode
only) the `.env` is present and gitignored.

**Degradation:** none. This phase always runs.

---

## Phase 1: intake

**Inputs:** the data folder. **Transcripts are required**; everything else is optional.

**Do:** run the intake subskill (`subskills/intake/`). Point it at the folder. It identifies the
transcript files (required) and asks the operator once, in a single prompt, for any optional inputs:
a CRM deal export, rep notes, stage history, and company docs. Prompt for each but never block on it.
Place transcripts under `raw/transcripts/`, CRM CSVs under `raw/crm/`, docs under `raw/docs/`. Record
in a short manifest what is present and what is absent.

**Gate:** at least one transcript file is present and readable, and the operator has confirmed the
manifest of what is present versus missing. If there are zero transcripts, stop: this skill audits
calls, and there is nothing to audit.

**Degradation:**

- **No CRM export:** the run becomes craft-only. There is no funnel, no stall pile, and no
  CRM-vs-call MEDDIC trust check. Scoring still runs on every call. Note this in `config.caveats`.
- **No stage history:** the funnel degrades to a current-stage snapshot and the deal arc weakens.
  Note it.
- **No rep notes:** follow-through leans on the next call and stage movement only. Fine.
- **No company docs:** company research runs from the web alone.

---

## Phase 2: company research

**Inputs:** the company name and domain (from intake), plus any docs in `raw/docs/`.

**Do:** run the company-research subskill (`subskills/company-research/`).

1. **Disambiguate the entity first.** Name collisions are common; confirm you have the right company
   (the one whose reps are on these calls), by domain and by what the calls are plainly about.
2. **Plan where the knowledge lives:** official site, G2 / Capterra / TrustRadius, Gartner / Forrester,
   Crunchbase, LinkedIn, recent news, earnings if public, product docs.
3. **Fan out a research swarm in parallel** (one task per source target), each returning sourced facts.
4. **Fold in operator docs** from `raw/docs/`.
5. **Synthesize** `company_context.md` using `schema/company_context.template.md`: what the company
   sells, who buys and why, what a credible claim sounds like (and the overclaim traps), the
   competitive set, and the sales motion and roles. This file is the product and competitor
   source-of-truth the scorer grounds on. Keep it factual and short. No slop.

**Gate:** `company_context.md` exists, names the right entity, and its "What a credible claim sounds
like" and "Sales motion and roles" sections are filled (the scorer and role inference depend on them).
Show the operator the one-paragraph product summary for a sanity check.

**Degradation:** if web research is thin or the operator gave no docs, write what is grounded, mark
the unknowns plainly in `company_context.md`, and lower the scorer's confidence on accuracy and
competitive dimensions. Never invent a competitor or a claim.

---

## Phase 3: normalize (plumbing, with one mapping judgment)

**Inputs:** `raw/transcripts/**`, and if present `raw/crm/deals.csv`, `raw/crm/stage_history.csv`,
`raw/crm/notes.csv`.

**Do:**

```bash
python3 scripts/normalize.py
```

It parses `raw/` into the canonical model: `canonical/transcripts.json`, and if present
`canonical/deals.json`, `canonical/stage_history.json`, `canonical/notes.json`. It splits each
transcript into speaker turns, reads the header (title, date, attendees, emails, recording URL,
duration), and maps CRM columns by synonym (`config.ingest.*_columns`). This is **structure only,
never meaning**.

When the CRM headers do not match the synonym lists, have a model propose the column mapping
(`prompts/crm_mapping.md`): the model reads the header row and the first few data rows and returns a
`{canonical: actual_header}` map, which you fold into `config.ingest.crm_columns`. The script applies
the map; the model never reads a transcript here.

Read the printed coverage report. Every transcript that parses into at least one turn is carried
forward. Only exact id-duplicates and unparseable files are dropped, each listed with a reason.

**Gate:** the canonical call count equals the number of transcript files the operator expects (minus
any explicitly listed drops). Do not proceed until this matches. Record the count; it is the
read-every-call denominator for Phase 7.

**Degradation:** with no CRM, only `canonical/transcripts.json` is produced and the deals/notes/stage
files are empty. The run continues craft-only.

---

## Phase 4: config

**Inputs:** intake manifest, `company_context.md`, the canonical files (for the real stage labels and
attendee domains).

**Do:** generate `config.json` from `schema/config.template.json` using `prompts/config_generate.md`.
Fill `org_name`, `product_oneliner`, `as_of_date`, `org_domains` (the selling org's email domains),
`terminology.stall_label`, and the rubric overrides if any. Leave `stage_map` and `stage_order` until
the real stage labels are visible from `canonical/deals.json` / `canonical/stage_history.json`, then
map each raw label to a canonical rung. Set `scope` if the operator wants a date window or a pilot.

**Gate:** `config.json` validates against `schema/config.template.json`, `org_domains` is non-empty
and correct (it decides who is a rep versus a customer), and `stage_map` covers every raw stage label
seen in the CRM. If there is no CRM, `org_domains` still must be right.

**Degradation:** no CRM means no `stage_map`/`stage_order` to fill; leave them empty and set
`scoring_universe` to score external calls without a CRM join. Carry the no-funnel caveat forward.

---

## Phase 5: roles (judgment) with a role-table gate

**Inputs:** `canonical/transcripts.json`, `canonical/deals.json` (owners, if present),
`company_context.md` (the "Sales motion and roles" section).

**Do:** build the roster (every `org_domains` email seen on calls, plus every CRM deal owner). For
each person, run `prompts/role_inference.md`: a model reads a sample of that person's calls **in full**
plus their CRM ownership and returns an archetype (founder-exec / sales-leader / ae-closer /
se-solutions / sdr-prospector / partner-external), seniority, join/leave hints, and which rubric
dimensions their role is responsible for, with a one-line rationale and the call ids it relied on.
Write `analysis/roles.json`. Run one task per person; independent tasks in parallel.

**Gate, show the operator the full role table.** Founders and externals to exclude, leavers and
joiners, and anyone external miscounted as a rep are corrected in `config.roles.overrides` and
`config.roles.name_fixes`. Roles are confirmed before any scoring is trusted.

**Degradation:** with thin CRM (no owners), the roster is built from call attendance alone and
seniority/role confidence drops; mark low confidence and lean harder on the operator's eyeball of the
table.

---

## Phase 6: link (plumbing)

**Inputs:** `canonical/*.json`, `config.json` (stage map, org domains, stall definition).

**Do:**

```bash
python3 scripts/link.py
```

It joins calls to deals by account, builds the funnel from stage history, groups opportunity units,
auto-detects the stall stage (the non-terminal stage the most deals enter and never win), and
classifies each call's internal / external / partner bucket from attendee email domains. It prints a
leak table and the verification gates. This is pure plumbing on ids, domains, and stage labels.

**Account-naming judgment pass.** Calls whose account name does not match the CRM are left unjoined.
Have a model read each unjoined call (`prompts/account_naming.md`) and name the customer company,
classify `call_status` (live / no_show / aborted), `transcript_quality` (good / fair / poor), and
`bucket` (external_customer / partner / internal). Write `analysis/call_company.json` and rerun
`link.py`. This is judgment (a model reading the call), never a keyword rule.

**Gate, show the operator the verification counts** before any scoring is trusted: deals parsed,
distinct deals ever at the demo stage, stage-history rows, transcripts ingested, calls joined to a
deal, in-scope calls to score, and the stall-pile size with its recovery rate. Confirm `stage_map`
and the detected stall stage now that the real labels are visible; fix `config.json` and rerun if
needed.

**Degradation:** no CRM means there is nothing to join to. The funnel, leak table, and stall pile are
skipped. Every external call still becomes an in-scope scoring unit (set
`scoring_universe.include_external_accounts_without_crm_deal`). The account-naming pass still runs so
calls are bucketed and quality-flagged.

---

## Phase 7: score calls ‖ parallel (judgment)

**This is the core. It runs ONE TASK PER IN-SCOPE CALL, in parallel.**

**Inputs:** each in-scope call's full canonical text, `company_context.md`, `analysis/roles.json`,
the rubric (`schema/rubric.template.json` merged with `config.rubric.overrides`), and the call's
linked deal context from Phase 6 (its stage, so scoring is stage-aware) when a CRM exists.

**Do:** for each in-scope call, run `prompts/call_score.md` as its own task. The task reads the call
**in full** and, for each org rep on that call, returns per-dimension scores (1 to 5, or NA) with the
rep's own-words quote as evidence, a per-dimension one-line justification, a confidence flag, and the
qualitative failure points. Collect the results with:

```bash
python3 scripts/merge_scores.py        # writes analysis/call_out/call_<id>.json per call
```

In **host-agent mode**, spawn one subagent per in-scope call and run them in parallel batches sized to
the host's limit. In **API mode**, run `python3 scripts/score_via_api.py`, which loops the same
`prompts/call_score.md` template through `engine/llm.py` over the same in-scope call list. Either
path writes the identical `call_out/call_<id>.json` shape.

**The read-every-call invariant.** The number of scoring tasks dispatched MUST equal the number of
in-scope canonical transcripts. Verify it: count `analysis/call_out/call_*.json` and confirm it
equals the in-scope call count from Phase 6. If short, calls were skipped: find them and run them.
No grep, keyword list, or "score the top N" is allowed to decide which calls matter.

Apply the non-negotiables while scoring:

- Score **every** org rep on the call, not just the primary speaker (co-presenter under-attribution
  is a known failure).
- Where an expected move is simply **not visible** in the corpus, score the dimension **NA with low
  confidence**, never a low mark for absence. A move that **is** visible but done badly scores low.
- The evidence quote for a rep's craft must be the **rep's own words**. The buyer's objection is the
  setup, never the score.
- Be stage-aware: a move not yet due at the call's stage is NA, not a failure.

**Gate:** `len(call_out/call_*.json) == in-scope call count`, and every rep on every scored call
appears in some rep's score block (no co-presenter dropped). Spot-check three cited quotes against
their transcripts: verbatim, attributed to the rep.

**Degradation:**

- **No CRM (craft-only):** there is no deal stage to make scoring stage-aware, so the scorer judges
  what is due from the call's own arc and marks more dimensions NA with lower confidence. The
  qualification dimensions that depend on CRM corroboration (paper process, decision process) lean on
  the transcript alone.
- **Thin or poor transcripts:** calls flagged `transcript_quality: poor` in Phase 6 are excluded from
  scoring by `scoring_universe.exclude_transcript_quality`. Fair-quality calls are scored at lower
  confidence. A genuinely sparse call yields more NA, not invented marks.

---

## Phase 8: post-mortems ‖ parallel (judgment)

**Inputs:** for each deal (opportunity unit), its deals row with stage history, its notes, and the
full text of **every one of its calls**, plus the call scores from Phase 7.

**Do:** run `prompts/postmortem.md` as one task per deal, in parallel. Each returns the deal arc,
where it lost pressure, why it stalled, the stall archetype, the one change that would have mattered,
and the **CRM-vs-call MEDDIC check** (which MEDDIC fields the CRM claims versus which a rep was
actually seen earning on a recording: recorded, observed, or contradicted). Write
`analysis/postmortem/deal_<unit>.json`.

**Gate:** one post-mortem file exists for every in-scope deal that has at least one call. Every MEDDIC
"observed" claim cites a call and a quote; every "contradicted" claim cites the CRM field and the
contradicting call moment.

**Degradation:** **no CRM means no post-mortems and no MEDDIC trust check** (there are no deals to
write a mortem for and no CRM fields to verify). Skip this phase; the report renders the craft pages
only. With CRM but no stage history, the arc is reconstructed from call dates and current stage, at
lower confidence.

---

## Phase 9: adherence, maker-checker ‖ parallel (judgment)

**Inputs:** a sample of the Phase 7 call scores plus the same calls' full text, the rubric calibration,
and `company_context.md`.

**Do:** run `prompts/adherence_check.md` with an **independent** agent, a different seat or model than
the scorer, over a sample of scored calls, in parallel. It re-reads each sampled call, audits the
scores against the calibration rules (especially any low mark resting on absence, and any high mark
not backed by a rep quote), and does a spot re-score. Write the per-call audits under
`analysis/adherence/` and roll them into a punch-list for human review. In host-agent mode, force a
fresh context so the checker is genuinely blind to the scorer's reasoning. In API mode, point the
checker at a different `LLM_MODEL` if the operator has one.

**Gate:** the adherence pass-rate is computed and the punch-list of disagreements is produced.
Overturned scores are corrected in the call_out files (and Phase 7 re-merged) before aggregation.
Report the pass-rate honestly; do not bury flagged calls.

**Degradation:** if the corpus is small, audit every call rather than a sample. If only one model is
available (host-agent mode, single model), the checker still runs in a fresh blind context; note that
maker and checker share a model and treat the pass-rate as a consistency check rather than a true
second opinion.

---

## Phase 10: council (judgment)

**Inputs:** the aggregate digest (funnel, stall pile, per-deal craft-vs-outcome summaries, per-rep
craft spread and role bars, dimension averages, trend), built by the aggregator from Phases 7 and 8.

**Do:** run `prompts/council.md`: four consultant seats **blind to each other** over the digest
(pipeline diagnostician, sales-craft coach, deal-strategy partner, enablement/ops skeptic), then a
synthesis seat over the four. Run each seat in a fresh context so they stay blind. Write
`analysis/council_output.json` as `{ "seats": [ ...4... ], "synthesis": { ... } }` with the keys the
template names.

**Gate:** four seat outputs plus one synthesis exist, every seat finding traces to a digest reference,
and the synthesis keeps craft separate from outcome and recommends no ranking of founders or external
partners.

**Degradation:** craft-only runs (no CRM) give the council a craft-and-rubric digest with no funnel
or stall pile; the pipeline-diagnostician seat then works from call-stage signals only and says so.

---

## Phase 11: aggregate and render (plumbing)

**Inputs:** `analysis/call_out/*.json`, `analysis/postmortem/*.json` (if any), `analysis/roles.json`,
`analysis/council_output.json`, the canonical files, `config.json`, the rubric.

**Do:**

```bash
python3 scripts/aggregate.py     # rolls per-call atoms up to rep / deal / org -> analysis/report_data.json
python3 scripts/report_app.py    # renders one self-contained work/<run>/report.html
```

`aggregate.py` computes each rep's role-weighted craft composite (NA excluded, low-confidence
down-weighted) and, in a **separate** block, their CRM outcomes (deals owned, stage outcomes, ARR,
win/loss/stall). It never folds an outcome field into the composite. `report_app.py` writes one
hash-routed, self-contained HTML app: Diagnosis, Reps (radar plus per-spoke explainers plus full
per-call score breakdowns), Deals (post-mortems), CRM check, and Council.

**Gate:** `report.html` opens with no network and renders every page. Spot-check three composite cells:
none folds in an outcome field. Confirm the report's role table is the operator-confirmed one from
Phase 5.

**Degradation:** craft-only runs render the Diagnosis, Reps, and Council pages; the Deals and CRM-check
pages either render empty with a stated caveat or are hidden, per `config.caveats`.

---

## Phase 12: gate (plumbing)

**Inputs:** the rendered `report.html`.

**Do:**

```bash
python3 scripts/antislop_check.py "$AUDIT_WORKDIR"/work/*/report.html
```

It must exit 0. It scans the report's authored editorial fields for AI cliche, sycophancy, and em or
en dashes. Verbatim quotes and source titles are exempt (they are evidence).

**Gate, final.** Anti-slop exits 0. Show the operator the Diagnosis and Reps pages and the confirmed
role table before treating the run as published. Report the Phase 9 adherence pass-rate and the
flagged calls honestly.

**Degradation:** none. The anti-slop gate always runs and must pass on the final HTML.

---

## Verifying the method held (before handover)

- `len(call_out/call_*.json)` equals the in-scope call count from Phase 6, so every call was read.
- Every rep on every scored call appears in some score block, so no co-presenter was dropped.
- No craft composite folds in an outcome field; spot-check three cells.
- Three cited quotes are verbatim and attributed to the named rep.
- The role table is the operator-confirmed one.
- (CRM runs) one post-mortem per in-scope deal with a call; every MEDDIC "observed" cites a quote.
- `antislop_check.py` exits 0 on the final report.
