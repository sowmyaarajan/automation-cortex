"""
Automation Cortex — Static UiPath project parser.

Reads a UiPath project folder (project.json + *.xaml files) and produces a
Genome JSON document conforming to parser/genome_schema.json.

Usage:
    python parser/parse_project.py demo/corpus/SAP_InvoicePosting
    python parser/parse_project.py --all demo/corpus --out genome/

The LLM-derived fields (intent, capabilities, modality_signals) are left
empty here and filled by the Day 2 extractor.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

UI_NS = "http://schemas.uipath.com/workflow/activities"
WF_NS = "http://schemas.microsoft.com/netfx/2009/xaml/activities"

HITL_ACTIVITY_TYPES = {
    "CreateFormTask",
    "WaitForFormTaskAndResume",
    "PresentValidationStation",
    "PresentClassificationStation",
    "AssignTask",
    "CompleteTask",
}

APP_HINT_RULES = [
    (re.compile(r"saplogon\.exe|SAP_Frame", re.I), "SAP"),
    (re.compile(r"outlook|SendOutlookMail|GetOutlookMailMessages", re.I), "Outlook"),
    (re.compile(r"excel|ExcelApplicationScope|ReadRange|WriteRange", re.I), "Excel"),
    (re.compile(r"webctrl|OpenBrowser|chrome|firefox|edge", re.I), "Browser"),
    (re.compile(r"ad\.contoso|ActiveDirectory", re.I), "ActiveDirectory"),
    (re.compile(r"workday", re.I), "Workday"),
]

MODALITY_KEYS = {
    "has_ui_automation": re.compile(r"Click|TypeInto|Selector|OpenBrowser|OpenApplication"),
    "has_ai_extraction": re.compile(r"DocumentUnderstanding|MachineLearningExtractor|DataExtractionScope|Digitize"),
    "has_api_calls": re.compile(r"HttpClient|InvokeRest|WebRequest"),
    "has_hitl": re.compile(r"CreateFormTask|WaitForFormTask|PresentValidationStation"),
}


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find_xamls(project_root: Path) -> list[Path]:
    return sorted(project_root.rglob("*.xaml"))


CONTAINER_TAGS = {"Activity", "Sequence", "TryCatch", "TryCatch.Try", "TryCatch.Catches", "Catch",
                  "If", "If.Then", "If.Else", "ForEach", "ForEachRow", "While", "DoWhile"}


def parse_xaml(xaml_path: Path) -> dict:
    """Extract activities (ordered), selectors, invoked workflows, exceptions, retry blocks from one .xaml."""
    text = xaml_path.read_text(encoding="utf-8", errors="replace")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return {"error": f"parse_error: {e}", "file": str(xaml_path)}

    activity_counter: Counter[str] = Counter()
    selectors: list[dict] = []
    invoked: list[str] = []
    exceptions: list[str] = []
    retry_blocks = 0
    hitl_nodes = 0
    sequence: list[dict] = []  # ordered leaf-ish activity list for SOP walker

    for elem in root.iter():
        tag = strip_ns(elem.tag)
        activity_counter[tag] += 1

        if tag not in CONTAINER_TAGS:
            display = None
            selector = None
            text_val = None
            for attr_name, attr_val in elem.attrib.items():
                al = strip_ns(attr_name)
                if al == "DisplayName":
                    display = attr_val
                elif al == "Selector":
                    selector = attr_val
                elif al in {"Text", "Message", "Subject", "To", "WorkflowFileName", "QueueName",
                            "FileName", "WorkbookPath", "SheetName", "FormTitle", "Url"}:
                    text_val = attr_val if text_val is None else text_val
            sequence.append({
                "activity": tag,
                "display_name": display,
                "selector": selector,
                "value": text_val,
            })

        if tag in HITL_ACTIVITY_TYPES:
            hitl_nodes += 1

        if tag == "RetryScope":
            retry_blocks += 1

        # Selectors live on attributes named Selector
        for attr_name, attr_val in elem.attrib.items():
            attr_local = strip_ns(attr_name)
            if attr_local == "Selector" and attr_val:
                app_hint = _guess_app(attr_val)
                selectors.append({
                    "raw": attr_val,
                    "app_hint": app_hint,
                    "workflow": xaml_path.name,
                })
            if attr_local == "WorkflowFileName" and attr_val:
                invoked.append(attr_val)

        # TryCatch — collect caught exception types
        if tag == "Catch":
            for attr_name, attr_val in elem.attrib.items():
                if strip_ns(attr_name) == "TypeArguments":
                    exceptions.append(attr_val)

    return {
        "file": str(xaml_path),
        "display_name": xaml_path.stem,
        "activity_count": sum(activity_counter.values()),
        "activities": dict(activity_counter),
        "selectors": selectors,
        "invoked": invoked,
        "exceptions": exceptions,
        "retry_blocks": retry_blocks,
        "hitl_nodes": hitl_nodes,
        "sequence": sequence,
    }


def _guess_app(text: str) -> str:
    for rx, name in APP_HINT_RULES:
        if rx.search(text):
            return name
    return "Unknown"


def _detect_apps(all_text: str) -> list[str]:
    apps: set[str] = set()
    for rx, name in APP_HINT_RULES:
        if rx.search(all_text):
            apps.add(name)
    return sorted(apps)


def _detect_modality(all_text: str) -> dict:
    return {k: bool(rx.search(all_text)) for k, rx in MODALITY_KEYS.items()}


def parse_project(project_root: Path) -> dict:
    project_root = project_root.resolve()
    project_json_path = project_root / "project.json"
    if not project_json_path.exists():
        raise FileNotFoundError(f"No project.json in {project_root}")

    project_meta = json.loads(project_json_path.read_text(encoding="utf-8"))
    project_name = project_meta.get("name", project_root.name)
    main_workflow = project_meta.get("main", "Main.xaml")

    xamls = find_xamls(project_root)
    parsed_workflows = [parse_xaml(x) for x in xamls]

    # Aggregate
    workflows_out = []
    all_selectors = []
    all_invoked = []
    all_exceptions = []
    activities_total: Counter[str] = Counter()
    retry_total = 0
    hitl_total = 0
    raw_text_blob_parts = []
    workflow_sequences: dict[str, list[dict]] = {}

    for pw in parsed_workflows:
        if "error" in pw:
            workflows_out.append({"file": pw["file"], "display_name": "PARSE_ERROR"})
            continue
        rel_file = Path(pw["file"]).relative_to(project_root).as_posix()
        workflows_out.append({
            "file": rel_file,
            "display_name": pw["display_name"],
            "activity_count": pw["activity_count"],
        })
        all_selectors.extend(pw["selectors"])
        all_invoked.extend(pw["invoked"])
        all_exceptions.extend(pw["exceptions"])
        for k, v in pw["activities"].items():
            activities_total[k] += v
        retry_total += pw["retry_blocks"]
        hitl_total += pw["hitl_nodes"]
        raw_text_blob_parts.append(Path(pw["file"]).read_text(encoding="utf-8", errors="replace"))
        workflow_sequences[rel_file] = pw["sequence"]

    all_text = "\n".join(raw_text_blob_parts)

    # Dedupe selectors on raw text, keep first occurrence
    seen: set[str] = set()
    unique_selectors = []
    for s in all_selectors:
        if s["raw"] not in seen:
            seen.add(s["raw"])
            unique_selectors.append(s)

    genome = {
        "id": f"{project_name}::{main_workflow}",
        "project_name": project_name,
        "project_root": str(project_root),
        "main_workflow": main_workflow,
        "workflows": workflows_out,
        "capabilities": [],  # LLM populates Day 2
        "applications": _detect_apps(all_text),
        "selectors": unique_selectors,
        "invoked_workflows": sorted(set(all_invoked)),
        "exceptions_caught": sorted(set(all_exceptions)),
        "retry_blocks": retry_total,
        "hitl_nodes": hitl_total,
        "raw_activities": dict(activities_total),
        "intent": "",  # populated by enrichment step
        "modality_signals": _detect_modality(all_text),
        "workflow_sequences": workflow_sequences,
    }
    return genome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Project folder OR (with --all) parent folder of projects")
    ap.add_argument("--all", action="store_true", help="Parse every subfolder that contains a project.json")
    ap.add_argument("--out", default="genome", help="Output directory for genome JSON files")
    args = ap.parse_args()

    root = Path(args.path)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.all:
        projects = [p.parent for p in root.rglob("project.json")]
    else:
        projects = [root]

    if not projects:
        print(f"No projects found under {root}", file=sys.stderr)
        sys.exit(1)

    for proj in projects:
        try:
            genome = parse_project(proj)
        except Exception as e:
            print(f"[error] {proj}: {e}", file=sys.stderr)
            continue
        out_file = out_dir / f"{genome['project_name']}.json"
        out_file.write_text(json.dumps(genome, indent=2), encoding="utf-8")
        print(f"[ok] {genome['project_name']} -> {out_file}  "
              f"({len(genome['selectors'])} selectors, {len(genome['invoked_workflows'])} invocations, "
              f"{genome['retry_blocks']} retries, {genome['hitl_nodes']} hitl)")


if __name__ == "__main__":
    main()
