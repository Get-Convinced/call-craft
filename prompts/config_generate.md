# Prompt — generate config.json (once per run)

You write the run's `config.json`. Everything org-specific lives in this one file so the rest of the
skill stays company and CRM agnostic. You fill it from two things you already have: the intake
manifest (what inputs exist) and the short company-research summary (who the org is, what they sell,
how they sell). The shape and the field docs are in `schema/config.template.json`; produce a complete
config that validates against it.

## Input

- `<workdir>/intake.json` — the manifest from Phase 1. Tells you whether deals / notes / stage history
  exist, the transcript count, and the date range hint.
- The company-research summary from Phase 2 (or `company_context.md` if it is already written): org
  name, domain(s), product one-liner, the sales motion and roles, the competitive set.
- If a CRM deals export exists, the **distinct raw stage labels** seen in it (the linker needs these
  to build `stage_map`). If you do not have them yet, leave `stage_map` empty and note that it gets
  filled after the stage labels are known.

## Output

A single JSON object: the complete `config.json`. Match `schema/config.template.json` exactly. Drop
the `_doc` / `_example` helper keys (the loader strips them, but a clean file is better). Fill:

```json
{
  "org_name": "<the selling org's name>",
  "product_oneliner": "<one plain sentence: what they sell, to whom, solving what>",
  "as_of_date": "<YYYY-MM-DD, the run date or the manifest's latest call date>",
  "org_domains": ["<email domain(s) of the selling org's reps>"],

  "scope": {
    "date_from": null,
    "date_to": null,
    "sample_deal_ids": null
  },

  "stage_map": { },
  "stage_order": ["lead", "qualify", "demo", "poc", "proposal", "negotiation", "won", "lost", "stalled"],

  "stalled_definition": {
    "derived_from": "auto",
    "stage_names": [],
    "inactivity_days": null
  },

  "roles": {
    "overrides": [],
    "name_fixes": []
  },

  "rubric": { "overrides": {} },

  "min_calls_to_rank_rep": 3,

  "caveats": [ ],

  "org_asr_aliases": [ ],
  "exclude_accounts": [ ],
  "account_aliases": [ ]
}
```

## How to fill each field

- **org_name / product_oneliner** — straight from research. The one-liner is one plain sentence,
  factual, no adjectives. It anchors every judgment prompt.
- **as_of_date** — the date the audit speaks as of. Use the run date, or the latest call date in the
  manifest if you want every "stalled / no recent activity" judgment anchored to the corpus.
- **org_domains** — the email domain(s) of the selling org's own reps (e.g. `acme.com`). This is how
  the pipeline splits internal reps from external buyers and partners, so get it right. Include every
  domain the org uses. If research did not surface it, infer it from the transcripts' header emails
  that recur across many calls, and say it is inferred.
- **scope** — leave nulls for a full run. Set `date_from` / `date_to` only if the operator asked to
  narrow the window; set `sample_deal_ids` only for a scoped pilot before the full corpus.
- **stage_map** — map each raw stage label to a canonical rung
  (`lead`, `qualify`, `demo`, `poc`, `proposal`, `negotiation`, `won`, `lost`, `stalled`). Fill this
  from the distinct raw labels in the deals export. If you do not have the labels yet, leave it `{}`
  and flag that the linker will print the real labels, after which this gets filled and the run
  repeated. With no CRM at all, leave it `{}` (the funnel is skipped, craft-only).
- **stage_order** — the default rung order is fine for most orgs; reorder only if the org's motion
  genuinely differs.
- **stalled_definition** — leave `derived_from: "auto"` so the linker detects the stall pile. Set
  `"config"` with explicit `stage_names` only if the org has a named parking stage (Hold, Nurture,
  Parked) you want to force.
- **roles** — leave `overrides` and `name_fixes` empty here. Phase 5 (role inference) fills role
  overrides; name_fixes get added as diarization variants surface. Do not pre-guess people.
- **rubric.overrides** — leave `{}` unless the org's motion needs a weight change. Defaults in
  `schema/rubric.template.json` are role-attributed already.
- **min_calls_to_rank_rep** — default 3. Lower to 2 only for a very small corpus where 3 would rank
  nobody.
- **caveats** — start with the two standing caveats (calls are one channel, so absence is flagged not
  penalized; craft is separated from outcome). Add one line for each missing optional input the
  manifest shows: no CRM means craft-only with no deal funnel; no stage history means the funnel is a
  current-stage snapshot; no notes means follow-through leans on calls and stage movement only. State
  the corpus size and date range. Keep each caveat one plain sentence.
- **currency** — discover it, do not assume it. Look at the CRM amount column (a header like "Amount
  (USD)" or values with a symbol) and at how money is spoken on the calls ("fifty-eight thousand
  dollars", "two crore rupees", "forty thousand euros"). Set `symbol` to the right glyph and `code` to
  the ISO code. Use `style: "indian"` only if the amounts are spoken in lakh and crore; otherwise
  `style: "short"` (thousand, million, billion). If you genuinely cannot tell, default to the symbol of
  the region the calls are in and say so in the caveats.
- **org_asr_aliases** — common transcription mis-hearings of the org or product name (for example an
  ASR engine writing "North Wind" for "Northwind", or "Acme Soft" for "AcmeSoft"). List `{wrong, right}`
  style entries so the scorer is not thrown by a mis-transcribed brand. Leave `[]` if none are known yet.
- **exclude_accounts** — accounts that are not real buying accounts and should be dropped from the
  report: the selling org itself, advisory/consulting firms, channel partners that are not the end
  customer, internal test accounts. List by display name. Leave `[]` if none.
- **account_aliases** — fold every spelling/legal-suffix variant of one company onto a single
  canonical name: `{"canonical": "Sekisui Chemical", "variants": ["Sekisui", "SekiSui Chemicals"]}`.
  This stops one opportunity from splitting across three account keys. Seed it from research where you
  already know an account goes by several names; leave `[]` otherwise.

## Rules

- Produce a **complete** config that validates against `schema/config.template.json`. Do not omit
  required keys; use the empty/null defaults above where you have nothing.
- Never fabricate org domains, stage labels, or accounts. Where you inferred a value, note it in
  `caveats` so the operator can correct it.
- The config must degrade with the inputs: if the manifest shows transcripts only, the CRM-dependent
  fields (`stage_map`, `account_aliases`, `exclude_accounts`) are empty and the caveats say craft-only.
- No em-dashes, no en-dashes, no buzzwords in any prose you write into the config.
- Return only the JSON.
