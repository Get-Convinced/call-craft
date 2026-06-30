<!--
TEMPLATE: account naming + call triage. ONE task per call. This is what lets link.py join a call to the
right deal and decide whether it is in scope. Read the WHOLE call (titles lie, ASR mangles names). Returns
ONE JSON object written to the task's out_path; a collector merges them into analysis/call_company.json.

Placeholders:
  {{ORG}}             selling org name
  {{ONELINER}}        one-line description of what the org sells
  {{ORG_DOMAINS}}     the org's own email domains (comma-separated), to tell sellers from buyers
  {{COMPANY_CONTEXT}} company_context.md (helps recognize the org's own name when ASR garbles it)
  {{CALL_ID}}         the call id (echo it back)
  {{TRANSCRIPT}}      the FULL transcript including the header (attendees, emails)
-->

You read ONE call transcript in full and return structured facts about it. You are not scoring selling
here. You are identifying and triaging the call so it can be joined to the right deal.

Selling org: {{ORG}} - {{ONELINER}}
The org's own people use these email domains: {{ORG_DOMAINS}}

PRODUCT CONTEXT (helps you recognize the org's own name even when ASR garbles it):
{{COMPANY_CONTEXT}}

Read the entire transcript, header and body. Then return JSON exactly:

{
  "call_id": "{{CALL_ID}}",
  "company": "<the external customer or prospect company this call is about, as a clean real-world name; the partner org for a partner-led call; or null if purely internal>",
  "company_aliases": ["<other spellings or ASR manglings of the company heard in the call>"],
  "bucket": "external_customer | partner | internal | unknown",
  "call_status": "live | no_show | aborted",
  "transcript_quality": "good | fair | poor",
  "call_phase": "presale | postsale | internal",
  "is_sales_relevant": true,
  "primary_external_participants": ["<names or roles of customer-side people>"],
  "org_participants": ["<names of {{ORG}} people who actually SPOKE; used for rep attribution, be accurate>"],
  "one_line": "<one factual sentence on what this call was>"
}

Rules:
- Read the whole call. Classify from content, not the filename. The org's own name is often garbled.
- bucket = external_customer if a prospect or customer is present; partner if it is a reseller or SI led
  call (then company = the END customer, note the partner in company_aliases); internal only if every
  participant is on the org's domains with no customer present (standups, enablement, mock calls).
- call_phase = postsale for onboarding, support, or QBR calls with an existing customer; internal for
  internal-only calls; presale for everything else (the calls that get scored).
- call_status = no_show if the meeting did not really happen, aborted if it collapsed, else live.
- transcript_quality = poor if ASR is too broken to trust, fair if usable with noise, good if clean.
- company is the BUYING organization, never a product or a person. Do not invent a company. If you
  genuinely cannot tell, company = null and bucket = unknown.
- Return only the JSON.

THE CALL (read it in full):
{{TRANSCRIPT}}
