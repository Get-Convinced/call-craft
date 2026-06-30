# Data contracts

The judgment engine and the plumbing meet at these JSON shapes. Whatever runs the model (host subagents
or the API drivers) must produce exactly these, because the aggregator and the renderer read them. All
files live under the operator's working folder.

## canonical/ (produced by normalize.py from the operator's raw inputs)

- `transcripts.json` — array of `{call_id, date, title, recording_url, participants:[...], transcript|segments, ...}`.
  `transcript` is the full text (or `segments:[{speaker, text, ts}]`). Never summarized.
- `deals.json` (optional) — array of `{deal_id, account, stage, owner, amount, created, close_date, meddic:{metric,economic_buyer,decision_process,decision_criteria,champion,pain,competition,paper}}`.
- `notes.json` (optional) — array of `{deal_id|deal_name, author, created, content}`.
- `stage_history.json` (optional) — array of `{deal_id|deal_name, from_stage, moved_to, modified_time}`.

## analysis/ intermediate (produced by the plumbing)

- `opp_index.json` (link.py) — the deal-units: `{unit_index, account, deal_ids, in_scope_call_ids, in_scope_call_count, outcome, arr, stage}`.
- `roles.json` (role inference, a judgment phase) — `{<norm_name>: {name, is_org_rep, archetype}}`.
- `call_company.json` (link.py) — per call: `{<call_id>: {org_participants:[...], one_line, call_phase}}`.

## analysis/call_out/call_<id>.json (one per in-scope call — the scoring atom)

```
{call_id, unit_index, account, date, title, recording_url, stage,
 reps:[{rep_key, rep_name, archetype, composite,
        scores:{<DIM_ID>:{score:1-5|"NA", confidence:"high|medium|low", why, quote}},
        failure_points:[{label, dim, buyer_quote, rep_quote, why}],
        signature:{label, dim, quote, why}|null,
        buyer_reaction:{state, evidence}}]}
```
Produced by filling `prompts/call_score.md`. `composite` is added by the plumbing (role-weighted mean),
the model returns the rest. One file per in-scope transcript (the read-every-call invariant).

## analysis/postmortem/deal_<unit>.json (one per deal)

```
{unit_index, account, outcome, arr,
 headline, arc, lost_pressure:{date, moment, why}, why_hold,
 stall_archetype, coachable, one_change,
 meddic_check:[{field, crm_value, status:"observed|claimed|contradicted|absent", evidence}]}
```
Produced by filling `prompts/postmortem.md`.

## analysis/adherence_calls/check_<id>.json (maker-checker, sampled calls)

```
{call_id, account, date, note,
 reps:[{rep_name, verdict:"pass|minor|major",
        violations:[{rule:"R1..R6", dim, detail}],
        rescore:[{dim, maker, checker, why}]}]}
```
Produced by filling `prompts/adherence_check.md`. `merge_scores.py` rolls these up into `analysis/adherence.json`.

## analysis/council_output.json (one, the judgment layer)

```
{seats:[{seat, findings:[{claim, evidence, severity}], answer_why_deals_stall, answer_what_reps_miss,
         answer_who_solutions, answer_one_change}],
 synthesis:{consensus:[...], tensions:[...], ranked_changes:[{change, rationale, expected_effect}], craft_vs_outcome_note}}
```
Produced by filling `prompts/council.md` over `analysis/council_digest.json` (built by `digest.py`).

## analysis/report_data.json (produced by aggregate.py; the only input to report_app.py)

`{org{...,adherence,council}, calls[], deals[], reps[], dims, dim_names, dim_groups, groups}`. Numbers
here are aggregates; the per-call qualitative detail lives in `calls[].reps[]`. The renderer is
self-contained: `report_app.py` reads this and writes one `report.html`.
