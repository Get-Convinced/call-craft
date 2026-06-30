# Prompt — CRM column mapping (one export at a time)

You map the real column headers of one tabular export onto the skill's canonical fields. The
normalizer (`scripts/normalize.py`) is pure plumbing: it cannot guess that a column called
`Opp Owner` is the deal owner or that `Amt (USD)` is the ARR. You make that call once, it applies it
to every row. You never read the rows for meaning, you only read enough to recognize what each column
holds.

This runs once per CRM/notes/stage file the intake manifest marked `present`. The export's `kind`
(`crm_deals`, `crm_notes`, or `stage_history`) tells you which output block to fill.

## Input

You are given, for one file:

- its `kind` (`crm_deals` | `crm_notes` | `stage_history`),
- the header row (the list of column names),
- a few sample rows (3 to 5) so you can recognize what each column actually contains.

## Output

Return JSON exactly in this shape. Fill only the block matching this file's `kind`; you may emit the
other blocks as empty objects or omit them. Every canonical field maps to a **source column name**
(a string that appears in the header) or `null` if the export does not carry it. Never invent a
column name that is not in the header.

```json
{
  "kind": "crm_deals",
  "deals": {
    "deal_id":            "<source column or null>",
    "deal_name":          "<source column or null>",
    "account":            "<source column or null>",
    "owner":              "<source column or null>",
    "stage":              "<source column or null>",
    "amount_arr":         "<source column or null>",
    "amount_otc":         "<source column or null>",
    "created_date":       "<source column or null>",
    "close_date":         "<source column or null>",
    "products":           "<source column or null>",
    "region":             "<source column or null>",
    "next_step":          "<source column or null>",
    "meddic_metric":            "<source column or null>",
    "meddic_economic_buyer":    "<source column or null>",
    "meddic_decision_process":  "<source column or null>",
    "meddic_decision_criteria": "<source column or null>",
    "meddic_champion":          "<source column or null>",
    "meddic_pain":              "<source column or null>",
    "meddic_competition":       "<source column or null>",
    "meddic_paper_process":     "<source column or null>"
  },
  "notes": {
    "deal_id":      "<source column or null>",
    "deal_name":    "<source column or null>",
    "author":       "<source column or null>",
    "created_date": "<source column or null>",
    "content":      "<source column or null>"
  },
  "stage_history": {
    "deal_id":      "<source column or null>",
    "deal_name":    "<source column or null>",
    "from_stage":   "<source column or null>",
    "to_stage":     "<source column or null>",
    "duration_days":"<source column or null>",
    "moved_at":     "<source column or null>"
  }
}
```

## What each canonical field means

**deals**
- `deal_id` — the stable opportunity id (Record Id, Opportunity Id, Deal Id). The join key. If the
  export has no id at all, leave it `null`; the normalizer falls back to `deal_name` as the key.
- `deal_name` — the opportunity name.
- `account` — the buying company / account name.
- `owner` — the rep who owns the deal.
- `stage` — the raw pipeline stage label, verbatim. Do not map it to a canonical rung here; that is
  `config.stage_map`'s job later.
- `amount_arr` — recurring revenue / annual contract value / the headline deal amount.
- `amount_otc` — one-time charge (implementation, setup), if a separate column exists.
- `created_date`, `close_date` — opportunity created date and (expected or actual) close date.
- `products` — products/lines on the deal, if present.
- `region` — geo/region, if present.
- `next_step` — the recorded next step, if present.
- `meddic_*` — the eight MEDDPICC slots. Map any column that clearly holds that slot's content
  (Metric / Economic Buyer / Decision Process / Decision Criteria / Champion / Identify Pain /
  Competition / Paper Process). Most exports carry only a few. Leave the rest `null`.

**notes**
- `deal_id` / `deal_name` — the reference back to the deal the note belongs to (one or both).
- `author` — who wrote the note (Note Owner / Created By).
- `created_date` — when the note was written.
- `content` — the free-text note body. This is the one field that must be present for notes to be
  useful; if you cannot find it, the operator gave a file that is not really notes.

**stage_history**
- `deal_id` / `deal_name` — the reference back to the deal (one or both).
- `from_stage` — the stage the deal moved out of.
- `to_stage` — the stage it moved into (Moved To / New Stage).
- `duration_days` — days spent in the prior stage, if recorded.
- `moved_at` — the timestamp of the change (Modified Time / Change Date).

## Rules

- **Map only to columns that exist.** Every value is a literal header string or `null`. If unsure
  between two columns, pick the one the sample rows confirm; if neither fits, use `null`.
- **Tolerate missing fields.** A sparse export is normal. Mark every absent field `null`. Only
  `content` (for notes) is load-bearing; everything else degrades gracefully.
- **Keep raw labels raw.** Do not normalize stage names, dates, or amounts. The normalizer parses
  dates and the linker maps stages. You only point at columns.
- **One file, one block.** Set `kind` to this file's kind and fill that block. Do not guess columns
  for a kind this file is not.
- Return only the JSON.
