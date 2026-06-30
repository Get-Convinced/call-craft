<!--
TEMPLATE: per-call rep scoring (the atom of the audit). ONE task per in-scope call.
Fill the {{PLACEHOLDERS}} and run it as one judgment task (a spawned subagent in host-agent mode, or one
engine/llm.py call in API mode). The task returns ONE JSON object matching schema/call_out.schema.json.
Run one task per in-scope call; the number of tasks MUST equal the number of in-scope transcripts.

Placeholders:
  {{ORG}}              seller org name
  {{ONELINER}}         one-line description of what the org sells
  {{COMPANY_CONTEXT}}  the product/competitor source-of-truth (company_context.md), truncated to ~6500 chars
  {{ACCOUNT}}          the prospect account on this call
  {{STAGE}}            current CRM stage for the deal, or "unknown" (stage-awareness only)
  {{ARC}}              one line per PRIOR call on this deal ("- <date>: <one line>"), or "(first recorded call)"
  {{REPS}}             one line per org rep to score: "- <name> [<key>] = <archetype> (<label>); RESPONSIBLE DIMS: <ids>. <responsibility>"
  {{RUBRIC_ANCHORS}}   the rubric dimensions with their 1-5 anchors (from schema/rubric.template.json)
  {{TRANSCRIPT}}       the FULL call transcript
-->

{{ORG}}: {{ONELINER}}

PRODUCT SOURCE-OF-TRUTH (judge technical accuracy/substance against this; a claim not supported here may be an overclaim. Naming a real customer or fact that appears below is accurate, not an overclaim):
{{COMPANY_CONTEXT}}

You are scoring how each {{ORG}} rep performed ON THIS ONE CALL with {{ACCOUNT}}. Score CRAFT only.

WHERE THIS CALL SITS IN THE DEAL (judge this from the CALL ITSELF; do NOT score the prior calls):
  CRM stage hint (may be "unknown", and is only a hint, never ground truth): {{STAGE}}
  Prior calls on this deal:
{{ARC}}

REPS to score (score each ONLY on their RESPONSIBLE DIMS; every other dim = "NA"):
{{REPS}}

RUBRIC (score 1-5 or "NA"):
{{RUBRIC_ANCHORS}}

Return ONE JSON object:
{"reps":[{"rep_key":"...","rep_name":"...","archetype":"...",
  "scores":{"<DIM_ID>":{"score":4,"confidence":"high|medium|low","why":"<one line>","quote":"<VERBATIM, spoken BY THE REP, required for 4/5 and 1/2>"}, ... one entry per responsible dim ...},
  "failure_points":[{"label":"<short>","dim":"<DIM id>","buyer_quote":"<verbatim buyer line that set it up, or ''>","rep_quote":"<verbatim rep line that is the failure>","why":"<why it cost pressure>"}],
  "signature":{"label":"<the rep's best moment on THIS call, or null>","dim":"...","quote":"<verbatim rep line>","why":"..."},
  "buyer_reaction":{"state":"engaged|neutral|skeptical|annoyed|disengaged","evidence":"<verbatim>"}
}]}

RULES (these define the method):
- QUALITATIVE FIRST: failure_points are the point of this. Each must cite the REP's own line (rep_quote) as the failure, not just the buyer's objection. 1-3 per rep.
- QUOTE = THE REP'S WORDS. For any craft dimension, the evidence quote must be a line spoken BY THE REP being scored. If your only quote is the buyer's, you have not scored the rep: find the rep's response in the same or next turn and quote THAT. An objection is the setup, never the score.
- READ THE WHOLE TURN. When the buyer raises an objection, quote the rep's reply that follows. If the rep replied with a concrete mechanism, comparison, or next action, the floor is 2, not 1.
- ANCHOR THE SCALE MIDDLE. 1 = no attempt / hand-waving only. 2 = attempted but did not land. 3 = substantive but not quantified or proven. 4-5 = made well AND it landed with the buyer (cite the rep quote). Did the rep explain HOW with a concrete example? If yes, minimum 3 on substance.
- CRAFT != OUTCOME. Score the move, not the result. A stalled/cold deal does not cap the scores. Buyer sentiment IN the call is craft-relevant; the CRM win/loss is not shown and must not be guessed.
- MEDDIC IS EARNED ON THE CALL. Score the qualification dimensions only from what the rep ELICITED or advanced ON THIS CALL. Do not credit a metric or an economic buyer just because it may exist in a CRM; if the rep did not draw it out here, it is not their craft here (NA or low).
- STAGE-AWARE / ARC-AWARE NA. First work out where this call sits in the cycle from its CONTENT: a first contact and discovery sound nothing like a demo, a proposal review, or a negotiation and close. The call itself is the primary signal; use the prior-call arc to confirm, and the CRM hint only if it agrees with what you read (it is often absent or wrong). A move not yet due at that point (paper process, mutual action plan, negotiation, senior threading on an early intro) is "NA", not 1.
- CALIBRATION: do not default to 3. A strong rep shows 4-5 with a rep quote; a weak one 1-2 with a rep quote; both show NA on moves that never came up. score is an integer 1-5 or "NA".
- Plain declarative prose. NEVER an em-dash or en-dash. Banned: delve, leverage, robust, seamless, cutting-edge, unlock, synergy. Return only JSON.

THE CALL (read it in full):
{{TRANSCRIPT}}
