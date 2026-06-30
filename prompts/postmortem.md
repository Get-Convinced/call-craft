<!--
TEMPLATE: per-deal post-mortem. ONE task per deal (a deal = its in-scope calls grouped).
Fill the {{PLACEHOLDERS}} and run as one judgment task. Returns ONE JSON object matching the postmortem
shape that aggregate.py reads (analysis/postmortem/deal_<unit>.json).

Placeholders:
  {{ORG}}            seller org name
  {{ACCOUNT}}        the prospect account
  {{STAGE}}          current CRM stage(s) for the deal, or "unknown"
  {{CRM_MEDDIC}}     the MEDDIC fields the CRM holds for this deal ("field: value | ..."), or "(CRM MEDDIC empty)"
  {{STAGE_HISTORY}}  stage transitions with dates, or "none"
  {{NOTES}}          rep notes (treat as suspect/optimistic), or "none"
  {{FINDINGS}}       per-call failure findings already produced by the scorer, or "none"
  {{TRANSCRIPTS}}    the deal's calls, in date order, read in full (cap the total length)

STALL ARCHETYPES (use exactly one): value-not-quantified, buyer-gated-deferral, no-pain-feature-tour,
economic-buyer-never-met, deferred-proof-loop, structurally-dead-disqualify, lost-to-competitor, won, still-active
-->

Write the POST-MORTEM for the {{ORG}} deal with {{ACCOUNT}} (current CRM stage: {{STAGE}}). Read the calls in full. Then be honest about why it is where it is.

STAY SUSPICIOUS OF THE CRM. More is said on these recorded calls than on email, phone, or in person. For each MEDDIC field the CRM claims, decide from the CALLS whether the rep actually EARNED it: 'observed' (you saw the rep elicit or confirm it on a call, cite it), 'claimed' (it is in the CRM but never seen being gathered on any call, so treat it as unverified), or 'contradicted' (a call shows otherwise). You cannot mark 'observed' or 'contradicted' without a verbatim call quote, and you cannot mark 'claimed' or 'contradicted' for a CRM field that is blank.

CRM MEDDIC on file: {{CRM_MEDDIC}}
CRM stage history: {{STAGE_HISTORY}}
Rep notes (suspect, often optimistic): {{NOTES}}
Per-call failure findings: {{FINDINGS}}

Return JSON: {
"headline":"<one sentence on the deal's state and why>",
"arc":"<short: how it opened, what moved it, where it stuck>",
"lost_pressure":{"date":"<call date>","moment":"<the verbatim line where momentum was lost>","why":"<why that moment cost the deal>"},
"why_hold":"<the real reason it parked or lost, in plain words>",
"stall_archetype":"<one of the archetypes listed above>",
"coachable":true,
"meddic_check":[{"field":"metric|economic_buyer|decision_process|decision_criteria|champion|pain|competition|paper","crm_value":"<or ''>","status":"observed|claimed|contradicted|absent","evidence":"<call quote if observed/contradicted, else ''>"}],
"one_change":"<the single move that most would have changed the outcome>"
}

Plain prose, no em-dash or en-dash, no buzzwords. The lost_pressure.moment and any observed/contradicted evidence MUST be verbatim from a call. Return only JSON.

THE CALLS:
{{TRANSCRIPTS}}
