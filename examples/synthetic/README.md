# Synthetic example: Northwind Cargo Cloud

This folder is **fully fictional sample data**, here so a stranger can run the skill end to end without
any real company's transcripts or CRM. Nothing here is a real company, person, deal, recording, or
number. The seller, the buyers, the names, the amounts, and the URLs are all invented. The recording
links point at `example.invalid`, which by definition never resolves. Do not treat any of it as fact.

## The fictional setup

- **Seller:** Northwind Cargo Cloud, a logistics SaaS that does automated dispatch planning, route
  optimization, a driver app, and delivery analytics for mid-market fleets. Reps in the data are
  Priya Anand (account executive), Marcus Bell (account executive), and Dana Whitfield (sales leader).
- **Buyers (all fictional):** Talindro Freight, Crestpoint Foods, Ridgeway Components, and Brightway
  Distribution.

## What is in here

```
raw/
  transcripts/
    2026-02-10_1030_Talindro-Freight-Discovery.txt        strong discovery call (Priya)
    2026-02-12_1400_Crestpoint-Foods-Product-Walkthrough.txt   no-pain feature tour (Marcus)
    2026-02-18_1100_Ridgeway-Components-Followup.txt       buyer objection the rep fumbles (Marcus)
    2026-03-24_1500_Talindro-Freight-Commercial-Close.txt  late-stage commercial and close plan (Priya + Dana)
  crm/
    crm_deals.csv     four deals: one negotiating, one lost, one on hold, one early with no call yet
    rep_notes.csv     short, optimistic rep notes that the calls do not always support
```

The four calls are written to span different deals and different quality on purpose, so a scorer can
tell good selling from bad:

- **Talindro discovery** is strong: the rep opens on why-now, pins the broken process, quantifies the
  cost and who carries it, identifies the economic buyer, and lands a dated mutual next step.
- **Crestpoint walkthrough** is a feature tour with no discovery: a tour of every module on demo data,
  no pain pinned, a vague "loop back when you are ready" close.
- **Ridgeway follow-up** is an objection the rep fumbles: the buyer challenges price against a cheaper
  competitor and raises a hard integration blocker, and the rep answers with "it is just more robust"
  and "most systems work out of the box" instead of substance.
- **Talindro close** is a late-stage call: the sales leader trades a concession for a longer term and a
  reference, the paper process and security review are mapped, and a dated mutual action plan is built.

The CRM and notes are deliberately rosier than the calls in places (for example, the notes call
Crestpoint and Ridgeway near-closed), which is exactly the gap the CRM-vs-call trust check is meant to
surface.

## How to run it

From your agentic CLI, point the skill at the `raw` folder in this directory:

```
/salescallaudit ./examples/synthetic/raw
```

The skill will research the (fictional) seller as best it can, normalize these transcripts and the
CRM, infer each rep's role, score every call, write the deal post-mortems, run the adherence check and
the council, and render one self-contained `report.html`.

Because Northwind Cargo Cloud is invented, the company-research phase will not find a real web
presence. That is expected: the skill will note the thin context and lower its confidence on the
accuracy and competitive dimensions, then score the calls on what is observable in the transcripts.
This is the same graceful degradation it uses on any company it cannot fully research.
