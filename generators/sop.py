"""
Generate Living SOP Markdown per automation, walking the recorded activity sequence.
Also generates the Reverse SOP (human-fallback) using a verb map.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

GENOME = Path(__file__).parent.parent / "genome"
SOPS = Path(__file__).parent.parent / "sops"
REV = Path(__file__).parent.parent / "reverse_sops"
SEED = Path(__file__).parent.parent / "db" / "seed" / "run_log.json"

SKIP_ACTIVITIES = {"RetryScope"}  # container-ish, don't emit as a step

# Bot step -> human step
HUMAN_VERB = {
    "GetTransactionItem": "Pick the next item from the {value} queue",
    "AddQueueItem": "Push the result into the {value} queue",
    "InvokeWorkflowFile": "Perform the sub-procedure documented in {value}",
    "SendOutlookMail": "Compose and send an email (subject: {value})",
    "GetOutlookMailMessages": "Open Outlook and review new messages in {value}",
    "SaveAttachments": "Save any email attachments to {value}",
    "MarkAsRead": "Mark the email as read",
    "TypeInto": "Type the value into the field labelled: {display}",
    "Click": "Click: {display}",
    "OpenApplication": "Launch {value}",
    "OpenBrowser": "Open a browser and navigate to {value}",
    "ExcelApplicationScope": "Open the Excel workbook: {value}",
    "ReadRange": "Read the sheet: {value}",
    "WriteRange": "Write results to the sheet: {value}",
    "CreateFormTask": "Wait for human input: {value}",
    "WaitForFormTaskAndResume": "Continue once the human task is completed",
    "PresentValidationStation": "Open Validation Station and confirm the extracted fields",
    "DocumentUnderstandingScope": "Run document understanding on the attachment",
    "DigitizeDocument": "Digitize the document (OCR)",
    "ClassifyDocumentScope": "Classify the document type",
    "DataExtractionScope": "Extract fields from the document",
    "MachineLearningExtractor": "Apply the ML extractor: {value}",
    "LogMessage": "Note in the log: {value}",
    "SetTransactionStatus": "Mark the current queue item as failed with a business exception",
    "ForEach": "Repeat the following steps for each item",
    "ForEachRow": "Repeat the following steps for each row of data",
    "If": "Decide based on the condition",
    "InvokeCode": "Run the embedded VB.NET calculation",
}


def _last_run_ref() -> str:
    try:
        rl = json.loads(SEED.read_text(encoding="utf-8"))
        gen = rl.get("generated_at", datetime.utcnow().isoformat())
    except Exception:
        gen = datetime.utcnow().isoformat()
    return f"run window ending {gen}"


def _step_line(step: dict, mode: str) -> str | None:
    act = step["activity"]
    if act in SKIP_ACTIVITIES:
        return None
    display = step.get("display_name") or ""
    value = step.get("value") or ""
    if mode == "human":
        template = HUMAN_VERB.get(act)
        if not template:
            return f"({act}) {display or value}".strip()
        try:
            return template.format(display=display or "the target", value=value or "the referenced item")
        except Exception:
            return f"({act}) {display or value}".strip()
    # bot mode
    label = display or value or act
    return f"`{act}` — {label}"


def _llm_overview(genome: dict, mode: str) -> str:
    """Try LLM prose overview; empty string on failure."""
    try:
        from llm.client import call, is_available
        from llm.prompts import (SOP_PROSE_SYSTEM, SOP_PROSE_USER_TMPL,
                                 REVERSE_SOP_SYSTEM, REVERSE_SOP_USER_TMPL)
        if not is_available():
            return ""
        # Flatten sequence to a short list for the prompt
        seq_lines = []
        for wf, seq in (genome.get("workflow_sequences") or {}).items():
            seq_lines.append(f"[{wf}]")
            for s in seq[:15]:
                label = s.get("display_name") or s.get("value") or ""
                seq_lines.append(f"  - {s['activity']}: {label}")
        seq_text = "\n".join(seq_lines) or "(no steps)"

        if mode == "human":
            return call(
                REVERSE_SOP_USER_TMPL.format(
                    project_name=genome.get("project_name", ""),
                    apps=", ".join(genome.get("applications", [])) or "none",
                    sequence=seq_text,
                ),
                system=REVERSE_SOP_SYSTEM,
                fallback="",
                max_tokens=250,
            )
        else:
            return call(
                SOP_PROSE_USER_TMPL.format(
                    project_name=genome.get("project_name", ""),
                    apps=", ".join(genome.get("applications", [])) or "none",
                    excs=", ".join(genome.get("exceptions_caught", [])) or "none",
                    sequence=seq_text,
                ),
                system=SOP_PROSE_SYSTEM,
                fallback="",
                max_tokens=250,
            )
    except Exception:
        return ""


def render_sop(genome: dict, mode: str) -> str:
    """mode: 'bot' (Living SOP) or 'human' (Reverse SOP)."""
    lines: list[str] = []
    kind = "Reverse SOP (Human Fallback)" if mode == "human" else "Living SOP"
    lines.append(f"# {kind}: {genome['project_name']}")
    lines.append("")
    lines.append(f"**Intent.** {genome.get('intent') or '(not yet enriched)'}")
    lines.append("")
    lines.append(f"**Applications touched.** {', '.join(genome.get('applications') or []) or '_none_'}")
    lines.append(f"**Capability tags.** {', '.join(genome.get('capabilities') or [])}")
    if genome.get("exceptions_caught"):
        lines.append(f"**Failure modes handled.** {', '.join(genome['exceptions_caught'])}")
    if genome.get("hitl_nodes"):
        lines.append(f"**Human-in-the-loop touchpoints.** {genome['hitl_nodes']}")
    lines.append("")

    if mode == "human":
        lines.append("> ⚠️ Use this procedure if the bot is unavailable. Steps are written for a human operator.")
    else:
        lines.append("> This SOP is generated from the automation's actual XAML and refreshes on every run.")
    lines.append("")

    # LLM-authored overview paragraph (falls back to nothing if key missing)
    overview = _llm_overview(genome, mode)
    if overview:
        heading = "## Overview (for the human operator)" if mode == "human" else "## What this bot does"
        lines.append(heading)
        lines.append("")
        lines.append(overview)
        lines.append("")
        lines.append("---")
        lines.append("")

    for wf_file, sequence in (genome.get("workflow_sequences") or {}).items():
        lines.append(f"## Workflow: `{wf_file}`")
        step_num = 1
        for step in sequence:
            line = _step_line(step, mode)
            if not line:
                continue
            lines.append(f"{step_num}. {line}")
            step_num += 1
        lines.append("")

    lines.append("---")
    lines.append(f"_Last updated from {_last_run_ref()}._")
    return "\n".join(lines)


def main():
    SOPS.mkdir(parents=True, exist_ok=True)
    REV.mkdir(parents=True, exist_ok=True)
    for f in sorted(GENOME.glob("*.json")):
        g = json.loads(f.read_text(encoding="utf-8"))
        (SOPS / f"{g['project_name']}.md").write_text(render_sop(g, "bot"), encoding="utf-8")
        (REV / f"{g['project_name']}.md").write_text(render_sop(g, "human"), encoding="utf-8")
        print(f"[sop] {g['project_name']}: bot + reverse generated")


if __name__ == "__main__":
    main()
