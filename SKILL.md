---
name: call-craft
description: Audit a B2B sales team from their real call transcripts and produce one interactive HTML report. Point it at a folder of call transcripts (Read.ai, Gong, Fireflies, Otter, or plain text) plus, optionally, a CRM deal export and rep notes. It researches the company off the web to build a grounded product/competitor context, infers each rep's role, reads every call in full, scores every rep on every call across a role-attributed rubric of the pressure moves a B2B call must make (discovery, MEDDPICC qualification, solutioning, deal control, urgency), writes a post-mortem per deal, runs an independent maker-checker adherence pass and a four-seat consultant council, and renders a self-contained report (org diagnosis, per-rep radar with per-spoke explainers and full score breakdowns, deal post-mortems, a CRM-vs-call trust check, and the council). Craft is kept strictly separate from outcome. Stage-aware: a late-stage move on an early call is NA, not a failure. Hermetic and engine-agnostic: ships no keys and no data, runs the judgment as subagents using your own CLI's model by default, with an optional bring-your-own API backend. Company and CRM agnostic; everything org-specific is discovered or configured at run time.
argument-hint: "[<path-to-data-folder>]"
user-invocable: true
---

# call-craft — orchestrator

You are auditing a B2B sales organization from its real calls and producing one interactive HTML
report. You are the **conductor**. The judgment (researching the company, inferring roles, scoring
calls, writing post-mortems, the council) is done by **model agents you spawn**; the plumbing
(normalizing inputs, joining calls to deals, aggregating numbers, rendering HTML) is done by
**deterministic Python scripts** in `scripts/` (stdlib only). You never score a call yourself in one
pass over the whole corpus, and a script never reads a transcript for meaning.

This file is the map. The per-phase procedure, gates, and degradation tiers are in **RUNBOOK.md** —
read it before you start. Judgment templates are in **prompts/**, subskills in **subskills/**, the
engine contract in **engine/**, the calibration in **schema/rubric.template.json**, and the output and
config contracts in **schema/**.

## This skill is hermetic — keep it that way

It must run for anyone, with nothing of its author's. Never reach for an external service, MCP, key,
or dataset that the recipient would not have. The company context comes from **live web research and
the operator's own documents**, never a private knowledge base. No secrets are ever written into the
skill; operator keys live only in a gitignored `.env`. No customer data is ever committed; it lives in
the operator's working folder.

## The engine — host agents by default, API optional

Every judgment step is a **task**: a prompt template from `prompts/` filled with one unit of input
(one call, one deal, one research target), returning validated JSON. How those tasks execute is the
only thing that varies by environment. Resolve it once at the start (`engine/README.md`):

- **Host-agent mode (default).** You are inside an agentic CLI (Claude Code, cowork, Codex, …). Run
  each task by **spawning a subagent**, and run independent tasks **in parallel** (batches sized to
  the host's limits). The model is whatever the host runs — no key needed. This is the default; prefer
  it whenever a subagent/Task capability exists.
- **API mode (opt-in).** For very large corpora or headless runs, the operator sets an
  OpenAI-compatible endpoint + key in `.env`; the `scripts/score_via_api.py` driver loops the same
  templates through `engine/llm.py` (provider switch: deepseek / openai / anthropic / local).

Either way the **output contract is identical** (`schema/call_out.schema.json` etc.), so the plumbing
and the report never care which engine ran.

## Non-negotiables (these define the method — never relax them)

1. **Every relevant call is read in full by a model.** No grep, keyword list, regex, or "read the top
   N" decides which calls matter, who is in them, or how a rep performed. Scripts never read a
   transcript for meaning. Verifiable: the number of calls handed to agents equals the number of
   in-scope canonical transcripts.
2. **Code is plumbing only.** Scripts parse files, join on ids, count, deduplicate, aggregate numbers
   a model already produced, and render HTML. A script never scores a call, classifies it by title or
   keyword, or decides a rep's role.
3. **Craft is kept separate from outcome.** How well a rep sold (the 1–5 rubric composite) is reported
   in a different place from what happened to the deal (won / lost / stalled, ARR, stage). A strong
   rep on a deal lost to price, timing, or politics is **not** marked down. Never blend them.
4. **The corpus is incomplete — score what you can see, flag what you cannot.** Calls are one channel.
   Where an expected move is simply **not visible**, score the dimension **NA with low confidence**,
   not a low mark. Penalize only what is on the recording.
5. **The CRM is suspect until proven on a call.** A MEDDIC field is real only if a rep was seen
   earning it on a recording. A field that sits in the CRM but was never gathered on a call is a
   *claim*, not a fact. Tag it accordingly.
6. **Stage-aware.** A move not yet due at a call's stage (paper process on an intro, negotiation on a
   first demo) is NA, not a failure. Use the deal arc to judge what was due.
7. **The evidence quote for a rep's craft must be the rep's own words.** A buyer's objection is the
   setup, never the score. Read the whole turn: quote the rep's reply.
8. **No slop in authored prose.** No em-dashes or en-dashes, no buzzword filler, in anything the model
   writes for the report. Verbatim quotes and source titles are exempt (they are evidence). The
   `scripts/antislop_check.py` gate enforces this on the final HTML.

## Phases (the run, end to end)

Work top to bottom. Each phase has a gate in RUNBOOK.md; do not advance past a failed gate. Phases
marked **‖ parallel** fan out one task per unit.

0. **Resolve engine + working folder.** Pick host-agent vs API. Create the operator's `work/` tree.
1. **Intake** (`subskills/intake/`). Take the data-folder argument. Identify the transcripts
   (required). Ask the operator, once, for any optional inputs (CRM export, rep notes, stage history,
   company docs) — prompt for them but never block. Record what is present.
2. **Company research** (`subskills/company-research/`). From the company name + domain, **plan where
   the knowledge lives** (official site, G2 / Capterra / TrustRadius, Gartner / Forrester, Crunchbase,
   LinkedIn, news, earnings, docs), **‖ fan out** a research swarm to gather it, fold in any operator
   documents, and **synthesize** `company_context.md` (the product/competitor source-of-truth the
   scorer grounds on). Disambiguate the entity (name collisions are common).
3. **Normalize** (`scripts/normalize.py` + `prompts/crm_mapping.md`). Map heterogeneous inputs into
   the canonical model (`canonical/transcripts.json`, and if present `deals.json`, `notes.json`,
   `stage_history.json`). A model proposes the column mapping; the script applies it.
4. **Config.** Generate `config.json` from intake + research (`prompts/config_generate.md`,
   `schema/config.template.json`): org name, scope, stage map, the rubric, exclusions, aliases.
5. **Roles** (`prompts/role_inference.md`). Infer each participant's role and which rubric dimensions
   their role is responsible for. Gate: operator eyeballs the role table.
6. **Name + Link** (`subskills/account-naming/` + `scripts/link.py`). Run `link.py` once to build the
   naming worklist, run the account-naming subskill so a model reads each call and writes
   `call_company.json` (which buying company, internal vs presale vs postsale, who spoke), then run
   `link.py` again to join calls to deals, build the funnel and stall pile, and clear the
   conservation gate. The linker never silently drops a call; an unnamed call holds the gate open.
7. **Score calls ‖ parallel** (`prompts/call_score.md`). One task per in-scope call: read it in full,
   for each org rep return per-dimension scores (with the rep's quote) and qualitative failure points.
   Collect with `scripts/merge_scores.py` → `analysis/call_out/`.
8. **Post-mortems ‖ parallel** (`prompts/postmortem.md`). One task per deal: arc, where it lost
   pressure, why it stalled, the stall archetype, the one change, and the CRM-vs-call MEDDIC check.
9. **Adherence (maker-checker) ‖ parallel** (`prompts/adherence_check.md`). An **independent** agent
   (a different model/seat than the scorer) re-reads a sample and audits the scores against the
   calibration rules, with a spot re-score. Surfaces a punch-list for human review.
10. **Council** (`prompts/council.md`). Four blind consultant seats + a synthesis seat over the
    aggregate digest. The judgment layer.
11. **Aggregate + render** (`scripts/aggregate.py` → `scripts/report_app.py`). Roll the per-call atoms
    up to rep / deal / org, then render one self-contained `report.html`.
12. **Gate** (`scripts/antislop_check.py`). Anti-slop must pass on the final HTML before you hand it
    over. Report the adherence pass-rate and the flagged calls honestly.

## Output

One file: `work/<run>/report.html` — hash-routed, no network, no external assets. Pages: Diagnosis,
Reps (radar + per-spoke explainers + full per-call score breakdowns), Deals (post-mortems), CRM check
(the recorded-vs-observed-vs-contradicted drill-down), and Council. Open in any browser.

Start by reading **RUNBOOK.md**.
