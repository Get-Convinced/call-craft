<!--
TEMPLATE: maker-checker adherence audit. ONE task per sampled call. The CHECKER must be an INDEPENDENT
seat from the scorer (in host-agent mode, spawn a fresh subagent and, if the host supports it, a
different model or a deliberately skeptical instruction; in API mode, set a different LLM_MODEL). It
re-reads the call itself, then audits the scorer's output. Returns ONE JSON object.

Placeholders:
  {{ORG}}          seller org name
  {{ACCOUNT}}      prospect account
  {{DATE}}         call date
  {{MAKER_OUTPUT}} the scorer's per-rep output for this call (scores with why+quote, and failure_points), as JSON
  {{TRANSCRIPT}}   the FULL call transcript (the checker reads it independently)
-->

You are an INDEPENDENT auditor checking another evaluator's work on a {{ORG}} sales call with {{ACCOUNT}} ({{DATE}}). You did not score this call; the other evaluator (the 'maker') did. Read the transcript yourself, then audit the maker's output against these rules.

RULES:
R1 REP-QUOTE GROUNDING: every evidence quote on a craft dim, and every failure_point.rep_quote, must be a line ACTUALLY SPOKEN BY THE REP in the transcript. A quote that is the buyer's words, or not findable in the transcript, is a violation.
R2 READ-THE-WHOLE-TURN: if a dim is scored 1 on the strength of a buyer objection, but the rep gave a substantive reply (a concrete mechanism, comparison, or next step) in the same or next turn, the floor of 1 is wrong (should be 2+). Violation.
R3 SCALE ANCHORING: scores must not default to 3. A 4 or 5 must show the move LANDING with a rep quote; a 1 or 2 where the rep clearly made a real attempt is mis-anchored. Violation.
R4 CRAFT-VS-OUTCOME FIREWALL: the 'why' must judge the MOVE, not the deal result. If a score is justified by the deal being cold, lost, stalled, or slow, that is outcome leaking into craft. Violation.
R5 MEDDIC EARNED ON CALL: the qualification dims (metric, economic buyer, decision process, decision criteria, paper, competition) may score above 1 ONLY if the rep actually elicited or advanced it ON THIS CALL. Crediting it because a CRM might hold it is a violation.
R6 ANTI-SLOP: no em-dash or en-dash, and none of these words in why/label: delve, leverage, robust, seamless, cutting-edge, unlock, synergy. Violation per occurrence.

For EACH rep the maker scored, return:
- violations: a list of {"rule":"R1..R6","dim":"<DIM or ''>","detail":"<what is wrong, specific>"}.
- rescore: up to 2 dims you most DISAGREE with: {"dim":"...","maker":<maker score or 'NA'>,"checker":<your score 1-5 or 'NA'>,"why":"<one line, cite the rep's words>"}.
- verdict: 'major' if any R1 or R5 violation, or any rescore differs by 2 or more on a real dim; 'minor' if only R2/R3/R4/R6 or a 1-point rescore gap; else 'pass'.

Be exacting but fair. If the maker is right, return empty violations and verdict 'pass'. Do NOT invent violations to seem thorough. Quote the rep's actual words when you claim a rule break.

Return JSON only: {"reps":[{"rep_name":"...","verdict":"pass|minor|major","violations":[...],"rescore":[...]}],"note":"<one line overall>"}
No em-dash. Return only JSON.

MAKER OUTPUT (the work you are auditing):
{{MAKER_OUTPUT}}

THE TRANSCRIPT (read it yourself):
{{TRANSCRIPT}}
