#!/usr/bin/env python3
"""Per-call scoring driver. Deterministic task-prep (which calls, which reps, their responsible dims, the
deal arc, the stage) is shared; only the model call differs by engine.

  python3 scripts/score_calls.py --workdir <dir> --emit-tasks   # HOST-AGENT mode: write filled prompts to
                                                                 # analysis/tasks/score/, no model call.
                                                                 # The host then runs one subagent per task
                                                                 # and writes each result to analysis/call_out/.
  python3 scripts/score_calls.py --workdir <dir>                 # API mode: fill + call engine/llm.py + write
                                                                 # analysis/call_out/ directly. Resume-safe.

Either way it reads prompts/call_score.md so the prompt has ONE source of truth. One task per in-scope
presale call (the read-every-call invariant).
"""
import os, re, sys, glob, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)        # scripts/  -> lib
sys.path.insert(0, SKILL)       # skill root -> engine
from lib import audit as A
from lib import scoring

PER_CALL_CAP = 22000


def load_template(name):
    t = open(os.path.join(SKILL, "prompts", name), encoding="utf-8").read()
    return re.sub(r"^<!--.*?-->\s*", "", t, flags=re.S)  # drop the usage comment header


def fill(t, **kw):
    for k, v in kw.items():
        t = t.replace("{{" + k + "}}", str(v))
    return t


def build_call_ctx(cid, unit, cc, calls, deals, roles, rubric, cfg):
    archs = rubric["role_archetypes"]
    info = cc.get(cid, {}); c = calls.get(cid)
    if not c:
        return None
    rep_set = {}
    for nm0 in set(info.get("org_participants") or []):
        if A.excluded_rep(nm0, cfg):
            continue
        r = roles.get(A.norm_name(nm0))
        if not r or not r.get("is_org_rep") or r.get("archetype") == "partner-external":
            continue
        a = archs.get(r["archetype"], {})
        if a.get("excluded_from_scoring"):
            continue
        cn = A.canonical_rep_name(r.get("name", nm0), cfg); k = A.norm_name(cn)
        rep_set[k] = {"key": k, "name": cn, "archetype": r["archetype"], "label": a.get("label"),
                      "responsible_dims": a.get("responsible_dims", []), "responsibility": a.get("responsible_for", "")}
    if not rep_set:
        return None
    deal_objs = [deals[d] for d in (unit.get("deal_ids") or []) if d in deals]
    stage = ", ".join(s for s in (d.get("stage") for d in deal_objs) if s) or None
    arc = []
    for pc in unit.get("in_scope_call_ids", []):
        if pc == cid:
            continue
        pcc = calls.get(pc); pi = cc.get(pc, {})
        if pcc and (pcc.get("date") or "") < (c.get("date") or ""):
            arc.append({"date": pcc.get("date"), "one_line": (pi.get("one_line") or pcc.get("title") or "")[:160]})
    arc.sort(key=lambda x: x["date"] or "")
    return {"call_id": cid, "account": unit.get("account"), "unit_index": unit["unit_index"],
            "date": c.get("date"), "title": c.get("title"), "recording_url": c.get("recording_url"),
            "stage": stage, "arc": arc, "reps": list(rep_set.values()),
            "transcripts": A.transcript_text(c, max_chars=PER_CALL_CAP)}


def render_prompt(ctx, tmpl, org, oneliner, kb, anchors):
    reps = "\n".join(f"  - {r['name']} [{r['key']}] = {r['archetype']} ({r['label']}); RESPONSIBLE DIMS: "
                     f"{', '.join(r['responsible_dims'])}. {r['responsibility']}" for r in ctx["reps"])
    arc = "\n".join(f"  - {a['date']}: {a['one_line']}" for a in ctx["arc"]) or "  (this is the first recorded call on the deal)"
    return fill(tmpl, ORG=org, ONELINER=oneliner, COMPANY_CONTEXT=kb[:6500], ACCOUNT=ctx["account"],
                STAGE=ctx["stage"] or "unknown", ARC=arc, REPS=reps, RUBRIC_ANCHORS=anchors,
                TRANSCRIPT=ctx["transcripts"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=os.environ.get("AUDIT_WORKDIR", ""))
    ap.add_argument("--emit-tasks", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    wd = args.workdir or A.workdir()
    cfg = A.load_config(wd)
    rubric = A.load_rubric(SKILL, cfg)
    anchors = scoring.rubric_anchors(rubric)
    tmpl = load_template("call_score.md")
    kbp = os.path.join(wd, "company_context.md")
    kb = open(kbp, encoding="utf-8").read()[:7000] if os.path.exists(kbp) else ""
    org = cfg.get("org_name"); oneliner = cfg.get("product_oneliner", "")
    calls = {c["call_id"]: c for c in A.read_json(os.path.join(wd, "canonical", "transcripts.json"))}
    deals = {d["deal_id"]: d for d in A.read_json(os.path.join(wd, "canonical", "deals.json"))} if os.path.exists(os.path.join(wd, "canonical", "deals.json")) else {}
    cc = A.load_call_company(wd, cfg)
    roles = A.read_json(os.path.join(wd, "analysis", "roles.json"))
    opp = A.read_json(os.path.join(wd, "analysis", "opp_index.json"))
    call2unit = {}
    for u in opp:
        for cid in u.get("in_scope_call_ids", []):
            call2unit[cid] = u
    targets = [cid for cid in call2unit if cc.get(cid, {}).get("call_phase") not in ("postsale", "internal")]

    outdir = os.path.join(wd, "analysis", "call_out"); os.makedirs(outdir, exist_ok=True)
    taskdir = os.path.join(wd, "analysis", "tasks", "score"); os.makedirs(taskdir, exist_ok=True)
    if not args.force:
        done = {os.path.basename(f)[5:-5] for f in glob.glob(outdir + "/call_*.json")}
        targets = [cid for cid in targets if cid not in done]
    if args.limit:
        targets = targets[:args.limit]

    if args.emit_tasks:
        n = 0
        for cid in targets:
            ctx = build_call_ctx(cid, call2unit[cid], cc, calls, deals, roles, rubric, cfg)
            if not ctx:
                continue
            A.write_json(os.path.join(taskdir, f"{cid}.json"), {
                "call_id": cid, "account": ctx["account"], "unit_index": ctx["unit_index"],
                "out_path": f"analysis/call_out/call_{cid}.json",
                "reps": [{"key": r["key"], "name": r["name"], "archetype": r["archetype"]} for r in ctx["reps"]],
                "prompt": render_prompt(ctx, tmpl, org, oneliner, kb, anchors)})
            n += 1
        print(f"== emitted {n} scoring tasks -> {taskdir}")
        print(f"   HOST-AGENT: run one subagent per task file; have it return the JSON from prompts/call_score.md")
        print(f"   and write it to the task's out_path. Then run merge_scores.py + aggregate.py.")
        return

    # API mode
    from engine import llm
    print(f"== score_calls (API {llm.PROVIDER}/{llm.MODEL_REASONER}): {len(targets)} calls, workers={args.workers}")

    def run(cid):
        ctx = build_call_ctx(cid, call2unit[cid], cc, calls, deals, roles, rubric, cfg)
        if not ctx:
            return {"call_id": cid, "_skip": "no scoreable reps"}
        r = llm.chat_json([{"role": "user", "content": render_prompt(ctx, tmpl, org, oneliner, kb, anchors)}],
                          model=llm.MODEL_REASONER, max_tokens=14000, temperature=0.0)
        auth = {x["key"]: x for x in ctx["reps"]}
        reps = []
        for rep in (r.get("reps") or []):
            nr = scoring.normalize_rep(rep)
            k = A.norm_name(A.canonical_rep_name(nr.get("rep_name", ""), cfg))
            a = auth.get(k) or auth.get(A.norm_name(nr.get("rep_key", "")))
            if not a:
                continue
            nr.update({"rep_key": a["key"], "rep_name": a["name"], "archetype": a["archetype"]})
            for f in ("failure_points", "signature", "buyer_reaction"):
                nr[f] = rep.get(f)
            reps.append(nr)
        return {"call_id": cid, "unit_index": ctx["unit_index"], "account": ctx["account"], "date": ctx["date"],
                "title": ctx["title"], "recording_url": ctx["recording_url"], "stage": ctx["stage"], "reps": reps}

    def on_done(i, res):
        if res and not res.get("_skip") and not res.get("_error"):
            A.write_json(os.path.join(outdir, f"call_{res['call_id']}.json"), res)
    results = llm.map_concurrent(targets, run, workers=args.workers, label="score", on_done=on_done)
    ok = sum(1 for r in results if r and not r.get("_skip") and not r.get("_error"))
    print(f"== scored {ok}/{len(targets)} calls -> {outdir}")


if __name__ == "__main__":
    main()
