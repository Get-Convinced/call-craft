# Prompt — company research plan (judgment, runs once)

You plan where the truth about ONE company lives on the web, so a research swarm can go gather it
efficiently. You do not gather here. You decide what to gather, from which sources, in what order, and
how to confirm you are even looking at the right company.

The output of this plan grounds an entire sales-call audit. If the plan sends the swarm to the wrong
entity or to thin sources, every downstream score is wrong. Be deliberate.

## Inputs

- **Company name:** {COMPANY_NAME}
- **Domain:** {COMPANY_DOMAIN}
- **Already known** (from the homepage fetch, operator documents, and any transcript leads):
  {KNOWN_SO_FAR}
  (This may include: what the company appears to sell, a product category, named customers or
  competitors heard on calls, the headquarters location, the founder/CEO, funding stage, headcount
  band. Use it. Empty is fine.)

## What you must reason about

1. **Entity disambiguation first.** Company names collide constantly ("Atlas", "Apollo", "Apex",
   "Orion" each name several real companies). Decide how the swarm will CONFIRM it has
   the right company before gathering anything. Anchor on the domain, not the name. Pick the
   discriminators a subagent can check on a page: the domain, the product category, the headquarters,
   the founder/CEO, the funding round. Write the `entity_check` as a short instruction a subagent can
   apply: "Confirm the page is about the company at {domain} that sells X, headquartered in Y, founded
   by Z. If the page is about a different company with the same name, discard it."

2. **Where does THIS company's product, customers, and positioning actually live?** It differs by
   company type. Reason about which the company is, then prioritize accordingly:
   - **Public company:** earnings-call transcripts, investor relations decks, and annual-report
     language state the segment, flagship customers, and competitive set in the company's own words.
     Prioritize `earnings` and `official_site` high.
   - **Venture-backed startup:** Crunchbase has the one-line "what they do" plus funding and headcount;
     the official site has product and customers; G2 / Capterra / TrustRadius reviews have the
     competitors buyers actually compared and the pains those buyers had. Prioritize `official_site`,
     `crunchbase`, and one review site.
   - **Category with a Gartner Magic Quadrant or Forrester Wave** (CRM, observability, CDP, ERP,
     security, and similar): the analyst writeup names the incumbents and the category for free.
     Include `gartner` / `forrester`.
   - **Services / niche B2B with little third-party coverage:** lean on `official_site`
     customers/case-study pages, `news`, and `linkedin` for size and segment.

3. **Prioritize.** Fan-out is bounded. Priority 1 is the spine: the official site plus whichever of
   {reviews, earnings, Crunchbase} is richest for this company type. Priority 2 fills the competitive
   set and the named-customer proof. Priority 3 is color (press, LinkedIn headcount). Do not make
   everything priority 1.

## Source types you may use

`official_site`, `g2`, `capterra`, `trustradius`, `gartner`, `forrester`, `crunchbase`, `linkedin`,
`news`, `earnings`, `competitor`, `docs`. Use only what fits this company. A pre-seed startup has no
earnings page; a 20-year-old private services firm may have no G2 listing. Do not pad the plan with
sources that will be empty.

## Output — return only this JSON

```json
{
  "entity_check": "<one short instruction a subagent applies to confirm every page is the right company, anchored on the domain plus 2-3 discriminators>",
  "company_type": "public | venture-backed | bootstrapped-private | services-niche | unknown",
  "targets": [
    {
      "source_type": "official_site | g2 | capterra | trustradius | gartner | forrester | crunchbase | linkedin | news | earnings | competitor | docs",
      "queries": ["<web search query or specific URL/page to fetch>", "..."],
      "why": "<what this source is expected to yield for THIS company: product modules, named customers, the competitive set, pricing, segment, etc.>",
      "priority": 1
    }
  ]
}
```

Rules:
- The `official_site` target should name the specific pages to fetch (homepage, /product or /platform,
  /pricing, /customers or /case-studies), not just the domain.
- Review and analyst targets should phrase queries that surface the COMPETITORS and the BUYER PAINS,
  not only the rating ("<company> vs", "<company> alternatives", "<company> competitors", "<category>
  Gartner magic quadrant").
- For a `competitor` target, the queries fetch the rival's own positioning page so the swarm learns
  how the rival frames itself against this company.
- 5 to 9 targets is the right size. Fewer leaves the context thin; more burns fan-out on color.
- Plain declarative prose in `why` and `entity_check`. No buzzword filler, no em-dashes or en-dashes.
- Return only the JSON, nothing else.
