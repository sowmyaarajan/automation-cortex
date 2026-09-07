"""
Deterministic enrichment rules — the offline replacement for LLM tagging.

Given a parsed Genome dict, produce:
  - capabilities: list[str]
  - intent: str
"""
from __future__ import annotations

import json

# Rule format: (predicate, tag). Predicate takes the Genome dict.
CAPABILITY_RULES = [
    # Document Understanding / AI extraction
    (lambda g: "MachineLearningExtractor" in g["raw_activities"]
              or "DataExtractionScope" in g["raw_activities"], "document_extraction"),
    (lambda g: "DocumentUnderstandingScope" in g["raw_activities"], "document_understanding"),
    (lambda g: "PresentValidationStation" in g["raw_activities"], "hitl_validation"),
    (lambda g: "ClassifyDocumentScope" in g["raw_activities"], "document_classification"),

    # Queues
    (lambda g: "AddQueueItem" in g["raw_activities"], "queue_producer"),
    (lambda g: "GetTransactionItem" in g["raw_activities"], "queue_consumer"),

    # SAP
    (lambda g: "SAP" in g["applications"] and (
        "FB60" in json.dumps(g.get("workflow_sequences", {})) or "invoice" in g["project_name"].lower()),
     "sap_posting"),
    (lambda g: "SAP" in g["applications"] and (
        "XK02" in json.dumps(g.get("workflow_sequences", {})) or "vendor" in g["project_name"].lower()),
     "sap_vendor_master"),
    (lambda g: "SAP" in g["applications"], "sap_ui_automation"),

    # Excel
    (lambda g: "Excel" in g["applications"] and "ReadRange" in g["raw_activities"], "excel_ingest"),
    (lambda g: "Excel" in g["applications"] and "WriteRange" in g["raw_activities"], "excel_output"),

    # Email
    (lambda g: any(a in g["raw_activities"] for a in ["SendOutlookMail"]), "email_send"),
    (lambda g: any(a in g["raw_activities"] for a in ["GetOutlookMailMessages"]), "email_ingest"),

    # HITL
    (lambda g: "CreateFormTask" in g["raw_activities"], "hitl_form_task"),
    (lambda g: "WaitForFormTaskAndResume" in g["raw_activities"], "hitl_approval_gate"),

    # Browser / API
    (lambda g: "Browser" in g["applications"], "browser_automation"),
    (lambda g: "ActiveDirectory" in g["applications"], "ad_provisioning"),

    # Library (name-based only to avoid false positives)
    (lambda g: "Shared" in g["project_name"] or "Utilities" in g["project_name"], "library"),

    # Retry / resilience
    (lambda g: g["retry_blocks"] >= 2, "resilient_retry"),
    (lambda g: len(g["exceptions_caught"]) >= 2, "multi_exception_handling"),
]


VERB_MAP = {
    ("SAP",): "posts to and updates",
    ("Excel", "Outlook"): "reads Excel and emails",
    ("Excel",): "processes Excel data for",
    ("Outlook",): "handles email for",
    ("Browser",): "operates a browser workflow for",
    ("ActiveDirectory",): "provisions Active Directory accounts for",
}


def _all_steps(g):
    for _, steps in (g.get("workflow_sequences") or {}).items():
        for s in steps:
            yield s


def derive_capabilities(genome: dict) -> list[str]:
    tags = []
    for pred, tag in CAPABILITY_RULES:
        try:
            if pred(genome):
                tags.append(tag)
        except Exception:
            continue
    # de-dupe preserving order
    seen = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _template_intent(genome: dict, capabilities: list[str]) -> str:
    apps = genome.get("applications", [])
    project = genome.get("project_name", "")
    # Pick verb from app combination
    verb = "operates on"
    for key, v in VERB_MAP.items():
        if all(a in apps for a in key):
            verb = v
            break
    domain_hint = ""
    if any("invoice" in c.lower() or "sap_posting" in c for c in capabilities):
        domain_hint = "invoices"
    elif "sap_vendor_master" in capabilities:
        domain_hint = "vendor master records"
    elif "ad_provisioning" in capabilities:
        domain_hint = "new-hire accounts"
    elif "email_ingest" in capabilities and "document_extraction" in capabilities:
        domain_hint = "inbound documents"
    elif "excel_ingest" in capabilities:
        domain_hint = "financial data"
    else:
        domain_hint = project.replace("_", " ").lower()

    apps_str = ", ".join(apps) if apps else "no external apps"
    retries = genome.get("retry_blocks", 0)
    hitl = genome.get("hitl_nodes", 0)
    suffix = []
    if retries:
        suffix.append(f"{retries} retry block{'s' if retries != 1 else ''}")
    if hitl:
        suffix.append(f"{hitl} human-in-the-loop step{'s' if hitl != 1 else ''}")
    suffix_str = f" ({'; '.join(suffix)})" if suffix else ""

    return f"{project} {verb} {domain_hint} via {apps_str}{suffix_str}."


def derive_intent(genome: dict, capabilities: list[str]) -> str:
    """Try LLM first; on failure or missing key, use the template."""
    template = _template_intent(genome, capabilities)
    try:
        from llm.client import call, is_available
        from llm.prompts import INTENT_SYSTEM, INTENT_USER_TMPL
        if not is_available():
            return template
        # first few concrete steps to give the model something real to work with
        first_steps = []
        for _, seq in (genome.get("workflow_sequences") or {}).items():
            for s in seq[:6]:
                label = s.get("display_name") or s.get("value") or s["activity"]
                first_steps.append(f"- {s['activity']}: {label}")
            if first_steps:
                break
        prompt = INTENT_USER_TMPL.format(
            project_name=genome.get("project_name", ""),
            apps=", ".join(genome.get("applications", [])) or "none",
            caps=", ".join(capabilities) or "none",
            retries=genome.get("retry_blocks", 0),
            hitl=genome.get("hitl_nodes", 0),
            excs=", ".join(genome.get("exceptions_caught", [])) or "none",
            first_steps="\n".join(first_steps) or "(no steps recorded)",
        )
        return call(prompt, system=INTENT_SYSTEM, fallback=template, max_tokens=100, temperature=0.3)
    except Exception:
        return template
