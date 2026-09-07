"""
Adversarial Consultant — deterministic rules engine.

Given a free-text spec, returns a structured plan that always includes:
  - similar_automations  (from Cortex graph)
  - modality             (RPA | AI | API | HITL, ranked)
  - reusable_components  (existing library workflows to invoke)
  - effort_estimate      (dev-days + AI-vs-human split)
  - reasons_not_to_build (dedupe / fragility / modality-mismatch)
  - adversarial_paragraph  (single canned rebuttal paragraph populated with the facts)
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

DB = Path(__file__).parent.parent / "db" / "cortex.sqlite"

# Keyword -> capability tags this spec resembles
KEYWORD_TO_CAPS = {
    "sap": ["sap_ui_automation", "sap_posting", "sap_vendor_master"],
    "invoice": ["sap_posting", "document_extraction", "queue_producer"],
    "vendor": ["sap_vendor_master"],
    "excel": ["excel_ingest", "excel_output"],
    "email": ["email_ingest", "email_send"],
    "outlook": ["email_ingest", "email_send"],
    "document": ["document_extraction", "document_understanding"],
    "extract": ["document_extraction"],
    "onboard": ["ad_provisioning", "hitl_approval_gate"],
    "hire": ["ad_provisioning"],
    "approval": ["hitl_form_task", "hitl_approval_gate"],
    "reconcil": ["excel_ingest", "excel_output"],
    "browser": ["browser_automation"],
    "web": ["browser_automation"],
    "api": [],  # handled separately for modality
    "queue": ["queue_producer", "queue_consumer"],
}

# Modality signals
MODALITY_TRIGGERS = {
    "AI (Document Understanding)": ["document", "extract", "invoice", "pdf", "receipt", "unstructured"],
    "API Workflow": ["api", "rest", "json", "webhook", "service"],
    "RPA (UI Automation)": ["sap", "excel", "outlook", "portal", "click", "type", "gui", "screen"],
    "Human-in-the-loop": ["approve", "approval", "review", "validate", "sign-off", "manual"],
    "Agent": ["decide", "reason", "chat", "nl", "natural language", "unstructured request"],
}


def _db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _spec_capabilities(spec: str) -> set[str]:
    spec_l = spec.lower()
    caps: set[str] = set()
    for kw, cap_list in KEYWORD_TO_CAPS.items():
        if kw in spec_l:
            caps.update(cap_list)
    return caps


def _recommend_modality(spec: str) -> list[dict]:
    spec_l = spec.lower()
    hits: list[dict] = []
    for modality, triggers in MODALITY_TRIGGERS.items():
        matched = [t for t in triggers if t in spec_l]
        if matched:
            hits.append({"modality": modality, "signals": matched,
                         "confidence": min(1.0, 0.25 * len(matched))})
    hits.sort(key=lambda x: -x["confidence"])
    if not hits:
        hits = [{"modality": "RPA (UI Automation)", "signals": ["default"], "confidence": 0.2}]
    return hits


def _find_similar(spec: str, spec_caps: set[str]) -> list[dict]:
    """Match spec capabilities against the Cortex; return top automations by cap overlap + name/intent keywords."""
    conn = _db()
    autos = conn.execute("""
        SELECT a.id, a.project_name, a.intent,
               (SELECT GROUP_CONCAT(tag, ',') FROM Capability WHERE automation_id = a.id) AS caps,
               (SELECT GROUP_CONCAT(app_name, ',') FROM Application WHERE automation_id = a.id) AS apps,
               COALESCE(f.score, 0) AS fragility
        FROM Automation a LEFT JOIN FragilitySignal f ON f.automation_id = a.id
    """).fetchall()
    conn.close()

    spec_tokens = set(re.findall(r"[a-z]+", spec.lower()))
    ranked = []
    for r in autos:
        caps = set((r["caps"] or "").split(",")) if r["caps"] else set()
        cap_overlap = len(caps & spec_caps)
        name_hit = sum(1 for t in spec_tokens if t and t in r["project_name"].lower())
        intent_hit = sum(1 for t in spec_tokens if t and t in (r["intent"] or "").lower())
        score = cap_overlap * 2 + name_hit * 3 + intent_hit
        if score > 0:
            ranked.append({
                "id": r["id"],
                "project_name": r["project_name"],
                "intent": r["intent"],
                "capabilities": sorted(caps),
                "match_score": score,
                "fragility": round(r["fragility"], 2),
            })
    ranked.sort(key=lambda x: -x["match_score"])
    return ranked[:3]


def _reusable_components(spec_caps: set[str]) -> list[dict]:
    """Find library components that overlap with the requested capabilities."""
    conn = _db()
    rows = conn.execute("""
        SELECT DISTINCT a.project_name, c.invoked_path, a.id
        FROM Automation a
        JOIN Capability cap ON cap.automation_id = a.id AND cap.tag = 'library'
        LEFT JOIN Component c ON c.resolved_project = a.project_name
    """).fetchall()

    # Also list workflow files of library projects directly
    libs = conn.execute("""
        SELECT a.id, a.project_name, a.genome_json
        FROM Automation a
        JOIN Capability cap ON cap.automation_id = a.id AND cap.tag = 'library'
    """).fetchall()
    conn.close()

    import json as _json
    out: list[dict] = []
    for lib in libs:
        g = _json.loads(lib["genome_json"])
        for wf in g.get("workflows", []):
            out.append({
                "library": lib["project_name"],
                "workflow": wf["file"],
                "why": f"Reuse from {lib['project_name']} instead of duplicating.",
            })
    return out


def _effort_estimate(spec: str, spec_caps: set[str], similar: list[dict], reusable: list[dict]) -> dict:
    """Very simple analog: base days + per-capability + apply reuse discount."""
    base = 2.0
    per_cap = 0.8 * len(spec_caps)
    reuse_discount = 0.5 if reusable else 0.0
    similar_discount = 0.5 if similar else 0.0
    total = max(1.0, base + per_cap - reuse_discount - similar_discount)
    ai_pct = 40  # generous baseline
    if any("document" in c or "extract" in c for c in spec_caps):
        ai_pct = 70
    return {
        "dev_days": round(total, 1),
        "ai_assist_percent": ai_pct,
        "human_percent": 100 - ai_pct,
        "assumptions": [
            f"base {base} + {round(per_cap,1)} for {len(spec_caps)} capabilities",
            f"reuse discount {'applied' if reusable else 'not applied'}",
            f"similar-automation discount {'applied' if similar else 'not applied'}",
        ],
    }


def _reasons_not_to_build(similar: list[dict], reusable: list[dict], modality_ranked: list[dict]) -> list[str]:
    reasons: list[str] = []
    if similar:
        top = similar[0]
        reasons.append(f"An automation with strong overlap already exists: **{top['project_name']}** (fragility {top['fragility']}). Extend it instead of duplicating.")
    high_frag = [s for s in similar if s["fragility"] >= 28]
    if high_frag:
        reasons.append(f"Existing overlapping automations show elevated fragility ({', '.join(s['project_name'] for s in high_frag)}). Building another SAP GUI bot risks the same failure modes.")
    if reusable:
        reasons.append(f"{len(reusable)} reusable library workflow(s) are ignored by the current draft — using them removes ~30–50% of the implementation.")
    if modality_ranked and modality_ranked[0]["modality"] != "RPA (UI Automation)":
        reasons.append(f"Modality analysis suggests **{modality_ranked[0]['modality']}** may be a better fit than RPA — consider before committing to UI automation.")
    if not reasons:
        reasons.append("No strong reason detected against building; proceed with the recommended modality.")
    return reasons


def _template_adversarial_paragraph(spec: str, similar: list[dict], reusable: list[dict],
                                    modality: list[dict], effort: dict, reasons: list[str]) -> str:
    """Deterministic rebuttal — used as fallback when LLM is unavailable."""
    parts = ["Before we write a single .xaml — a few objections."]
    if similar:
        top = similar[0]
        parts.append(f"You're describing something the estate already does: **{top['project_name']}** ({top['intent']}) has fragility {top['fragility']}/100 and answers the same intent.")
    else:
        parts.append("Nothing in the estate matches this closely, so at least we're not duplicating.")
    if modality:
        m = modality[0]
        if m["modality"] != "RPA (UI Automation)":
            parts.append(f"Second: this reads more like a **{m['modality']}** problem than an RPA one (signals: {', '.join(m['signals'])}). RPA is the expensive path — pick it only if the alternative is truly blocked.")
        else:
            parts.append(f"RPA is the right modality here ({', '.join(m['signals'])}), but that comes with the fragility tax you can see across our SAP estate.")
    if reusable:
        parts.append(f"Third: there are **{len(reusable)}** reusable workflows in `Shared_Utilities` you should invoke — not re-implement. Every duplication becomes a maintenance chore next quarter.")
    parts.append(f"If you still want to proceed, the estimate is **{effort['dev_days']} dev-days** at ~{effort['ai_assist_percent']}% AI-assisted. But the honest recommendation is: extend, don't rebuild.")
    return " ".join(parts)


def _adversarial_paragraph(spec: str, similar: list[dict], reusable: list[dict],
                           modality: list[dict], effort: dict, reasons: list[str]) -> str:
    """LLM-authored rebuttal grounded in the computed facts; falls back to template on failure."""
    template = _template_adversarial_paragraph(spec, similar, reusable, modality, effort, reasons)
    try:
        from llm.client import call, is_available
        from llm.prompts import CONSULTANT_SYSTEM, CONSULTANT_USER_TMPL
        if not is_available():
            return template
        similar_str = "; ".join(
            f"{s['project_name']} (fragility {s['fragility']}, intent: {s['intent']})"
            for s in similar[:3]
        ) or "none"
        reusable_str = "; ".join(
            f"{r['library']}::{r['workflow']}" for r in reusable[:5]
        ) or "none"
        modality_str = "; ".join(
            f"{m['modality']} (signals: {', '.join(m['signals'])}, conf {m['confidence']:.2f})"
            for m in modality[:3]
        ) or "none"
        reasons_str = " | ".join(reasons)
        prompt = CONSULTANT_USER_TMPL.format(
            spec=spec,
            similar=similar_str,
            reusable=reusable_str,
            modality=modality_str,
            effort_days=effort["dev_days"],
            ai_pct=effort["ai_assist_percent"],
            reasons=reasons_str,
        )
        return call(prompt, system=CONSULTANT_SYSTEM, fallback=template,
                    max_tokens=400, temperature=0.7)
    except Exception:
        return template


def _modality_headline(modality: list[dict], similar: list[dict], reusable: list[dict]) -> str:
    """One-line modality verdict for the design's pill badge."""
    if similar and similar[0].get("match_score", 0) >= 15:
        return "EXTEND, DON'T BUILD"
    top = modality[0]["modality"] if modality else "RPA (UI AUTOMATION)"
    if top.startswith("RPA"):
        return "RPA — VALIDATE FIRST"
    if top.startswith("AI"):
        return "USE AI EXTRACTION"
    if top.startswith("API"):
        return "USE API WORKFLOW"
    if "Human" in top:
        return "USE HUMAN-IN-THE-LOOP"
    return top.upper()


def plan(spec: str) -> dict[str, Any]:
    spec_caps = _spec_capabilities(spec)
    similar = _find_similar(spec, spec_caps)
    reusable = _reusable_components(spec_caps)
    modality = _recommend_modality(spec)
    effort = _effort_estimate(spec, spec_caps, similar, reusable)
    reasons = _reasons_not_to_build(similar, reusable, modality)
    para = _adversarial_paragraph(spec, similar, reusable, modality, effort, reasons)

    # ── Reshape to match the design's expected consultant contract ──
    # similar_automations: {dst_id, project_name, score:0-1, method}
    max_ms = max((s.get("match_score", 0) for s in similar), default=1) or 1
    similar_design = [
        {
            "dst_id": s["id"],
            "project_name": s["project_name"],
            "score": min(1.0, max(0.1, s.get("match_score", 0) / max(max_ms, 15))),
            "method": "capability_overlap",
        }
        for s in similar
    ]
    # reusable_components: array of workflow filenames (strings)
    reusable_design = []
    seen = set()
    for r in reusable:
        name = r.get("workflow", "").split("/")[-1].split("\\")[-1]
        if name and name not in seen:
            seen.add(name)
            reusable_design.append(name)
    # effort_estimate: single string, first word = the big number
    effort_str = f"{effort['dev_days']} days · ~{effort['ai_assist_percent']}% AI-assisted"
    # modality: single string headline
    modality_str = _modality_headline(modality, similar, reusable)

    return {
        "spec": spec,
        "adversarial_paragraph": para,
        "modality": modality_str,
        "similar_automations": similar_design,
        "reusable_components": reusable_design,
        "effort_estimate": effort_str,
        "reasons_not_to_build": reasons,
    }


if __name__ == "__main__":
    import json as _json
    result = plan("I want to build an SAP invoice bot that reads emails and posts invoices")
    print(_json.dumps(result, indent=2))
