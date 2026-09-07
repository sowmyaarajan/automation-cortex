"""Ingest enriched genome/*.json into cortex.sqlite."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "cortex.sqlite"
GENOME_DIR = Path(__file__).parent.parent / "genome"


def resolve_project(invoked_path: str, all_project_names: set[str]) -> str | None:
    """Resolve cross-project invocation like '..\\Shared_Utilities\\ExcelReader.xaml' -> 'Shared_Utilities'."""
    normalized = invoked_path.replace("\\", "/")
    m = re.search(r"\.\./([^/]+)/", normalized)
    if m and m.group(1) in all_project_names:
        return m.group(1)
    return None


def ingest():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    # Clean slate for ingestion (idempotent)
    for tbl in ["Similarity", "FragilitySignal", "ExceptionCaught", "Component",
                "Selector", "Application", "Capability", "Automation"]:
        conn.execute(f"DELETE FROM {tbl}")

    genome_files = sorted(GENOME_DIR.glob("*.json"))
    project_names = {json.loads(f.read_text(encoding="utf-8"))["project_name"] for f in genome_files}

    for f in genome_files:
        g = json.loads(f.read_text(encoding="utf-8"))
        aid = g["id"]

        conn.execute("""
            INSERT INTO Automation (id, project_name, project_root, main_workflow, intent,
                                    modality_signals_json, retry_blocks, hitl_nodes, activity_count, genome_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            aid, g["project_name"], g["project_root"], g.get("main_workflow"),
            g.get("intent", ""), json.dumps(g.get("modality_signals", {})),
            g.get("retry_blocks", 0), g.get("hitl_nodes", 0),
            sum(g.get("raw_activities", {}).values()),
            json.dumps(g),
        ))

        for tag in g.get("capabilities", []):
            conn.execute("INSERT OR IGNORE INTO Capability (automation_id, tag) VALUES (?, ?)", (aid, tag))
        for app in g.get("applications", []):
            conn.execute("INSERT OR IGNORE INTO Application (automation_id, app_name) VALUES (?, ?)", (aid, app))
        for sel in g.get("selectors", []):
            conn.execute("INSERT INTO Selector (automation_id, raw, app_hint, workflow) VALUES (?, ?, ?, ?)",
                         (aid, sel["raw"], sel.get("app_hint"), sel.get("workflow")))
        for inv in g.get("invoked_workflows", []):
            resolved = resolve_project(inv, project_names)
            conn.execute("INSERT OR IGNORE INTO Component (automation_id, invoked_path, resolved_project) VALUES (?, ?, ?)",
                         (aid, inv, resolved))
        for exc in g.get("exceptions_caught", []):
            conn.execute("INSERT OR IGNORE INTO ExceptionCaught (automation_id, exception_type) VALUES (?, ?)",
                         (aid, exc))

    conn.commit()

    # Sanity print
    print("Ingested:")
    for row in conn.execute("SELECT project_name, (SELECT COUNT(*) FROM Capability WHERE automation_id=Automation.id) c, "
                            "(SELECT COUNT(*) FROM Selector WHERE automation_id=Automation.id) s, "
                            "(SELECT COUNT(*) FROM Component WHERE automation_id=Automation.id) i "
                            "FROM Automation ORDER BY project_name"):
        print(f"  {row[0]}: {row[1]} caps, {row[2]} selectors, {row[3]} invocations")
    conn.close()


if __name__ == "__main__":
    ingest()
