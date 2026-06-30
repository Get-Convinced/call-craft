# Prompt — rep role inference (judgment, one rep at a time)

You decide what ONE person's role is at the selling org, so the rubric can hold them to the right
bar. A junior prospector must not be measured against a closer's expectations.

Context:
- Selling org: **{ORG_NAME}** — {PRODUCT_ONELINER}
- (Prepend `company_context.md`, especially its "Sales motion and roles" section.)

You are given, for this person:
- their identity (name, email — note whether the email is on the org's domains {ORG_DOMAINS}),
- the CRM deals they OWN (names, stages, amounts) — may be empty,
- the full text of a sample of calls they spoke on (read them in full),
- how often and in what kind of call (intro / demo / technical / commercial / internal) they appear.

Return JSON exactly:

```json
{
  "email": "<email or null>",
  "name": "<canonical display name>",
  "archetype": "founder-exec | sales-leader | ae-closer | se-solutions | sdr-prospector | partner-external",
  "seniority": "leadership | senior | mid | junior",
  "is_org_rep": true,
  "exclude_from_ranking": false,
  "joined_hint": "<YYYY-MM or null — earliest sign they were active>",
  "left_hint": "<YYYY-MM or null — if they disappear mid-corpus>",
  "rationale": "<one or two plain sentences: what they actually do on calls + own in CRM>",
  "evidence_call_ids": ["<2-4 call ids this rests on>"],
  "confidence": "high | medium | low"
}
```

Rules:
- **Judge from behavior, not title guesses.** Who do they act like on calls — opening and booking
  (sdr), running demos and answering technical depth (se), owning commercial and closing (ae),
  steering strategy and coaching the room (leader), parachuting exec-to-exec (founder)?
- `partner-external` (and `is_org_rep: false`) if their email is NOT on the org's domains and they
  behave as a channel partner or customer-side participant — even if they appear in many calls. Set
  `exclude_from_ranking: true`. The org-domain check is decisive but read the call to be sure.
- Founders/execs: `exclude_from_ranking: true` (still analyzed, never ranked).
- If someone spans roles, pick the dominant one and say so in the rationale.
- Do not fabricate join/leave dates; use null unless the corpus clearly shows it.
- Return only the JSON.
