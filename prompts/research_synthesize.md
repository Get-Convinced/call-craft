# Prompt — company context synthesis (judgment, runs once)

You fold a pile of raw research into one factual reference, `company_context.md`. Every downstream
scorer reads this file to know, for THIS product, what good discovery is, what a credible value claim
is, what a real qualification looks like, and whether a rep claim is supported or an overclaim. Keep
it factual, source-backed, and short. It is a reference, not marketing copy.

## Inputs

- **Company:** {COMPANY_NAME} ({COMPANY_DOMAIN})
- **Confirmed entity facts** (the disambiguation result): {ENTITY_CHECK}
- **Research findings** — the swarm's bundles, each fact carrying a source URL and a supporting
  snippet; the fetched page text; and the extracted operator-document text. Operator documents are the
  highest-trust source: where they conflict with stale web copy, the operator's own document wins.
  {RAW_FINDINGS}

## The output shape (match `schema/company_context.template.md` exactly)

Produce a Markdown file with these sections, in this order:

1. **A title line and a source-trust header.** Start with `# Company context — {COMPANY_NAME}` and a
   short paragraph that tells the downstream scorer how to use the file. It MUST state, in plain
   words: a customer, competitor, module, or fact named in a real source below is **accurate, not an
   overclaim**; only flag an overclaim when a rep claim CONTRADICTS this file or invents a capability
   or customer no source here supports. Without this header the scorer false-flags every true customer
   name a rep says out loud. (See `schema/company_context.template.md` for the tone and structure.)

2. **What the company sells** — one paragraph: the product, the buyer, the problem it solves.

3. **Products and modules** — the real product lines / modules / features, with their aliases if the
   product is sold under several names. Only what a source states.

4. **Customers (these are REAL; naming them is accurate)** — the named customers a source attributes
   to this company, with the use-case and any ROI/outcome number where a source gave one. Group
   anonymized references ("a national LPG distributor: 95% route compliance") separately from named
   ones. A logo on the company's own customers page is a valid source for "this is a customer."

5. **Who buys it and why** — typical buyer roles, the economic buyer, the trigger to buy, typical deal
   size and sales-cycle length where known.

6. **What a credible claim sounds like** — what the product can and CANNOT truthfully do. List the
   overclaim traps a rep might fall into (a capability the product does not have, a customer it does
   not have, a number it cannot back), so the scorer can judge technical accuracy. This section is
   only useful if it names the boundaries, not just the strengths.

7. **The competitive set** — the named incumbents this company displaces or is compared against, and
   the honest edge and weakness against each, so the scorer can judge positioning. Name the rivals;
   "various competitors" is useless to the scorer.

8. **Sales motion and roles** — the expected motion (who prospects, who demos, who closes) and how rep
   roles map to it. This anchors role inference downstream.

9. **Known good and known bad** — optional. Named exemplars of strong selling and recurring failure
   patterns, only if a source or operator document surfaced them. Calibration, not ground truth.

## The rules that make this file trustworthy

- **A customer / competitor / fact named in a real source IS accurate.** When a source attributes a
  customer, a module, or a number to this company, record it plainly. It is not an overclaim for the
  scorer to later see a rep say it. The whole point of this file is to let the scorer tell true claims
  from invented ones.
- **Never invent.** Do not add a customer, capability, competitor, module, or number that no source in
  the input supports. If the research is thin on a section, say it is thin. An honest gap is correct;
  a confident fabrication corrupts every score above it.
- **Capture all five anchors the scorer needs:** the products/modules, the real named customers with
  use-cases and ROI where found, the competitive positioning versus named incumbents, the ICP (who
  buys and why), and the buyer pains. A section that names none of these is not doing its job.
- **State the boundaries, not only the strengths.** The "What a credible claim sounds like" section
  must say what the product cannot do and where a rep would overclaim. A reference that only lists
  strengths cannot catch an overclaim.
- **Prefer the company's own words** (its site, earnings call, documents) for WHAT it sells, and
  third-party words (reviews, analysts) for HOW it is positioned against rivals.
- **Operator documents outrank stale web copy.** If a battlecard or pricing sheet conflicts with the
  website, use the document and note the conflict briefly.
- **Plain declarative prose. No slop.** No em-dashes or en-dashes anywhere in your prose. No buzzword
  filler (delve, leverage, robust, seamless, cutting-edge, synergy, paradigm, game-changer, and the
  rest). Verbatim quotes from a source are evidence and exempt; your own sentences are not. Do not
  editorialize or sell.
- **Keep it short and dense.** This file is prepended to many prompts. Dense fact, no padding. Aim for
  the density and structure shown in `schema/company_context.template.md`.

## Output

Return only the contents of `company_context.md` (Markdown). No preamble, no JSON wrapper, no closing
commentary. The conductor writes your output verbatim to `<workdir>/company_context.md`.
