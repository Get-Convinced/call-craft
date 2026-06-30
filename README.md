# call-craft

Turn a sales team's real call transcripts into an interactive audit report: per-call scoring on a
role-attributed rubric, deal post-mortems, a CRM-vs-call trust check, per-rep radar with per-spoke
explainers, an independent maker-checker pass, and a four-seat consultant council. Craft is scored
separately from outcome. Every call is read in full; numbers only appear once they aggregate.

This skill is **self-contained and engine-agnostic**. It ships no API keys and no data. It runs inside
any agentic CLI that can read/write files, run Python (stdlib only), search the web, and spawn
subagents — Claude Code, Claude cowork, Codex, and similar. By default the judgment work runs as
subagents using **your** CLI's own model, so there is nothing to sign up for.

## What you provide

| Input | Required? | Formats |
|-------|-----------|---------|
| **Call transcripts** | **Yes** | Read.ai, Gong, Fireflies, Otter, Zoom, or plain text. One file per call, or an export. |
| CRM deal export | Optional | CSV / XLSX / JSON from Salesforce, HubSpot, Zoho, Pipedrive, etc. Unlocks the funnel + CRM trust check. |
| Rep notes | Optional | Any text/CSV. Used as a (suspect) signal, never as truth. |
| Stage history | Optional | If your CRM export has it. Enables the deal arc. |
| Company docs | Optional | PDF / XLSX / PPT / text. Fold your own collateral into the company context. |

Only transcripts are mandatory. Everything else is asked for but never blocks a run; the report
degrades cleanly (no CRM means craft-only scoring, no funnel, no MEDDIC trust check).

## How to run

In your agentic CLI, invoke the skill and point it at a folder:

```
/call-craft ./my-team-calls
```

It will: research the company off the web (and any docs you drop in) to build a grounded context,
ask for whatever optional inputs you have, normalize them, infer each rep's role, score every call,
write deal post-mortems, run an independent adherence check and the council, and render one
self-contained `report.html` you can open in any browser.

## Engine options

- **Default — host agents (no key):** scoring and research run as subagents in whatever CLI you are
  using, with that tool's model.
- **Optional — bring your own API:** for large corpora you can point it at an OpenAI-compatible
  endpoint (DeepSeek, OpenAI, Anthropic, local) by setting keys in a local `.env`. See `engine/`.

## Privacy

Your transcripts, CRM data, and the generated report never leave your machine (host-agent mode keeps
everything in your CLI session; API mode only sends transcripts to the endpoint you configure). The
skill ships no secrets, and `.gitignore` blocks `.env` and any work data from being committed.

New here? Open `docs/guide.html` in a browser for a plain-language overview with diagrams.

See `SKILL.md` for the method and `RUNBOOK.md` for the step-by-step procedure.
