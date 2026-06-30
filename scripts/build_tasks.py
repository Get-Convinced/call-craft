#!/usr/bin/env python3
"""Deterministic task-prep for the post-mortem and adherence phases (the scoring phase has its own
driver, score_calls.py). Emits filled prompts to analysis/tasks/<phase>/ so the host can run one
subagent per task (host-agent mode), or so an API driver can loop them. Pure plumbing: no model calls.

  python3 scripts/build_tasks.py postmortem --workdir <dir>
  python3 scripts/build_tasks.py adherence  --workdir <dir> [--sample 24]

Each task file is {key, out_path, prompt}. The host runs the prompt and writes the JSON to out_path.
"""
import os, re, sys, glob, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from lib import audit as A

PER_CALL = 8000
TOTAL = 24000
TXT_CAP = 16000


def load_template(name):
    t = open(os.path.join(SKILL, "prompts", name), encoding="utf-8").read()
    return re.sub(r"^<!--.*?-->\s*", "", t, flags=re.S)


def fill(t, **kw):
    for k, v in kw.items():
        t = t.replace("{{" + k + "}}", str(v))
    return t


def naming_tasks(wd, cfg):
    """One naming task per substantive call (from link.py's naming_worklist, or all calls if absent).
    The host runs each and writes the record to analysis/naming_out/<call_id>.json; merge_scores.py then
    collects them into analysis/call_company.json."""
    calls = {c["call_id"]: c for c in A.read_json(os.path.join(wd, "canonical", "transcripts.json"))}
    wl_path = os.path.join(wd, "analysis", "naming_worklist.json")
    targets = A.read_json(wl_path) if os.path.exists(wl_path) else list(calls)
    org = cfg.get("org_name"); oneliner = cfg.get("product_oneliner", "")
    domains = ", ".join(cfg.get("org_domains", [])) or "(none provided)"
    kbp = os.path.join(wd, "company_context.md")
    kb = open(kbp, encoding="utf-8").read()[:4000] if os.path.exists(kbp) else ""
    tmpl = load_template("account_naming.md")
    out = os.path.join(wd, "analysis", "tasks", "naming"); os.makedirs(out, exist_ok=True)
    n = 0
    for cid in targets:
        c = calls.get(cid)
        if not c:
            continue
        prompt = fill(tmpl, ORG=org, ONELINER=oneliner, ORG_DOMAINS=domains, COMPANY_CONTEXT=kb,
                      CALL_ID=cid, TRANSCRIPT=A.transcript_text(c, max_chars=TXT_CAP))
        A.write_json(os.path.join(out, f"{cid}.json"),
                     {"call_id": cid, "title": c.get("title"),
                      "out_path": f"analysis/naming_out/{cid}.json", "prompt": prompt})
        n += 1
    print(f"== emitted {n} naming tasks -> {out}")
    print(f"   run one subagent per task, write each record to its out_path, then merge_scores.py collects them.")


def postmortem_tasks(wd, cfg):
    org = cfg.get("org_name")
    calls = {c["call_id"]: c for c in A.read_json(os.path.join(wd, "canonical", "transcripts.json"))}
    deals = {d["deal_id"]: d for d in A.read_json(os.path.join(wd, "canonical", "deals.json"))} if os.path.exists(os.path.join(wd, "canonical", "deals.json")) else {}
    hist = A.read_json(os.path.join(wd, "canonical", "stage_history.json")) if os.path.exists(os.path.join(wd, "canonical", "stage_history.json")) else {}
    notes = A.read_json(os.path.join(wd, "canonical", "notes.json")) if os.path.exists(os.path.join(wd, "canonical", "notes.json")) else {}
    callout = {}
    for fp in glob.glob(os.path.join(wd, "analysis", "call_out", "call_*.json")):
        co = A.read_json(fp); callout[co["call_id"]] = co
    opp = A.read_json(os.path.join(wd, "analysis", "opp_index.json"))
    tmpl = load_template("postmortem.md")
    out = os.path.join(wd, "analysis", "tasks", "postmortem"); os.makedirs(out, exist_ok=True)
    n = 0
    for u in opp:
        cids = sorted(u.get("in_scope_call_ids", []), key=lambda c: calls.get(c, {}).get("date") or "")
        if not cids:
            continue
        blocks, used, findings = [], 0, []
        for cid in cids:
            c = calls.get(cid)
            if not c:
                continue
            t = A.transcript_text(c, max_chars=PER_CALL)
            if used + len(t) > TOTAL:
                t = t[:max(0, TOTAL - used)]
            blocks.append(f"\n== CALL {c.get('date')} | {c.get('title')} ==\n{t}"); used += len(t)
            co = callout.get(cid)
            if co:
                for r in co.get("reps", []):
                    for fp in (r.get("failure_points") or [])[:2]:
                        findings.append(f"{c.get('date')} {r.get('rep_name')}: {fp.get('label')} ({(fp.get('why') or '')[:80]})")
            if used >= TOTAL:
                break
        deal_objs = [deals[d] for d in u.get("deal_ids", []) if d in deals]
        sh = []
        for d in deal_objs:
            for r in (hist.get(d["deal_id"]) or hist.get(d.get("deal_name")) or []):
                if r.get("modified_time") and r.get("moved_to"):
                    sh.append(f"{r.get('from_stage')}->{r['moved_to']} ({(r.get('modified_time') or '')[:10]})")
        nt = []
        for d in deal_objs:
            for nn in (notes.get(d["deal_id"]) or notes.get(d.get("deal_name")) or []):
                nt.append(f"[{(nn.get('created') or '')[:10]}] {(nn.get('content') or '')[:240]}")
        meddic = {}
        for d in deal_objs:
            for k, v in (d.get("meddic") or {}).items():
                if v and not meddic.get(k):
                    meddic[k] = str(v)[:200]
        stage = ", ".join(s for s in (d.get("stage") for d in deal_objs) if s) or "unknown"
        prompt = fill(tmpl, ORG=org, ACCOUNT=u.get("account"), STAGE=stage,
                      CRM_MEDDIC=(" | ".join(f"{k}: {v}" for k, v in meddic.items()) or "(CRM MEDDIC empty)"),
                      STAGE_HISTORY=(" ; ".join(sh[-12:]) or "none"),
                      NOTES=(" ; ".join(nt[:14]) or "none"),
                      FINDINGS=(" ; ".join(findings[:14]) or "none"),
                      TRANSCRIPTS="".join(blocks))
        A.write_json(os.path.join(out, f"{u['unit_index']:03d}.json"),
                     {"unit_index": u["unit_index"], "account": u.get("account"),
                      "out_path": f"analysis/postmortem/deal_{u['unit_index']:03d}.json", "prompt": prompt})
        n += 1
    print(f"== emitted {n} post-mortem tasks -> {out}")


def adherence_tasks(wd, cfg, sample):
    org = cfg.get("org_name")
    calls = {c["call_id"]: c for c in A.read_json(os.path.join(wd, "canonical", "transcripts.json"))}
    cos = [A.read_json(f) for f in sorted(glob.glob(os.path.join(wd, "analysis", "call_out", "call_*.json")))]
    cos = [c for c in cos if c.get("reps")]
    if sample and len(cos) > sample:
        step = max(1, len(cos) // sample)
        cos = cos[::step][:sample]
    tmpl = load_template("adherence_check.md")
    out = os.path.join(wd, "analysis", "tasks", "adherence"); os.makedirs(out, exist_ok=True)
    for co in cos:
        c = calls.get(co["call_id"])
        if not c:
            continue
        maker = [{"rep_name": r.get("rep_name"), "archetype": r.get("archetype"),
                  "scores": {d: {"score": (v or {}).get("score"), "why": (v or {}).get("why"), "quote": (v or {}).get("quote")}
                             for d, v in (r.get("scores") or {}).items() if isinstance(v, dict)},
                  "failure_points": r.get("failure_points") or []} for r in co.get("reps", [])]
        prompt = fill(tmpl, ORG=org, ACCOUNT=co.get("account"), DATE=co.get("date"),
                      MAKER_OUTPUT=json.dumps(maker, ensure_ascii=False, indent=1),
                      TRANSCRIPT=A.transcript_text(c, max_chars=TXT_CAP))
        A.write_json(os.path.join(out, f"{co['call_id']}.json"),
                     {"call_id": co["call_id"], "account": co.get("account"),
                      "out_path": f"analysis/adherence_calls/check_{co['call_id']}.json", "prompt": prompt})
    print(f"== emitted {len(cos)} adherence tasks -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["naming", "postmortem", "adherence"])
    ap.add_argument("--workdir", default=os.environ.get("AUDIT_WORKDIR", ""))
    ap.add_argument("--sample", type=int, default=24)
    args = ap.parse_args()
    wd = args.workdir or A.workdir()
    cfg = A.load_config(wd)
    if args.phase == "naming":
        naming_tasks(wd, cfg)
    elif args.phase == "postmortem":
        postmortem_tasks(wd, cfg)
    else:
        adherence_tasks(wd, cfg, args.sample)


if __name__ == "__main__":
    main()
