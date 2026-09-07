"""
Load synthetic run log + incidents + fixes into SQLite,
and push the derived selector_volatility numbers into FragilitySignal.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "cortex.sqlite"
SEED = Path(__file__).parent / "seed"


def load():
    run_log = json.loads((SEED / "run_log.json").read_text(encoding="utf-8"))
    incidents = json.loads((SEED / "incidents.json").read_text(encoding="utf-8"))
    fixes = json.loads((SEED / "fixes.json").read_text(encoding="utf-8"))
    people = json.loads((SEED / "people.json").read_text(encoding="utf-8")) if (SEED / "people.json").exists() else []
    prompts = json.loads((SEED / "llm_prompts.json").read_text(encoding="utf-8")) if (SEED / "llm_prompts.json").exists() else []

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("DELETE FROM Incident")
    conn.execute("DELETE FROM Fix")
    conn.execute("DELETE FROM Person")
    conn.execute("DELETE FROM LLMPrompt")

    # People
    for p in people:
        conn.execute("INSERT INTO Person (id, name, role, team) VALUES (?, ?, ?, ?)",
                     (p["id"], p["name"], p.get("role"), p.get("team")))

    # Prompts
    for pr in prompts:
        conn.execute("""
            INSERT INTO LLMPrompt (id, title, when_to_use, prompt_text, model)
            VALUES (?, ?, ?, ?, ?)
        """, (pr["id"], pr["title"], pr.get("when_to_use"), pr.get("prompt_text"), pr.get("model")))

    # Fixes first so we have IDs
    ref_to_id: dict[str, int] = {}
    for fx in fixes:
        cur = conn.execute("""
            INSERT INTO Fix (incident_kind, applies_to_app, remediation, success_count, last_applied)
            VALUES (?, ?, ?, ?, ?)
        """, (fx["incident_kind"], fx["applies_to_app"], fx["remediation"],
              fx["success_count"], fx["last_applied"]))
        ref_to_id[fx["ref"]] = cur.lastrowid

    for inc in incidents:
        fx_id = ref_to_id.get(inc.get("fix_ref"))
        conn.execute("""
            INSERT INTO Incident (automation_id, occurred_at, kind, summary, fix_id, resolved_by, prompt_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (inc["automation"], inc["occurred_at"], inc["kind"], inc["summary"], fx_id,
              inc.get("resolved_by"), inc.get("prompt_id")))

    # Update selector_volatility on FragilitySignal from run_log
    # volatility = selector_change_events / total_runs (clamped to 0..1)
    for r in run_log["runs"]:
        total = max(r["total"], 1)
        vol = min(1.0, r["selector_change_events"] / total)
        conn.execute("""
            INSERT INTO FragilitySignal (automation_id, selector_volatility)
            VALUES (?, ?)
            ON CONFLICT(automation_id) DO UPDATE SET selector_volatility = excluded.selector_volatility
        """, (r["automation"], vol))

    conn.commit()

    print("Seeded experience:")
    for r in conn.execute("SELECT COUNT(*) FROM Incident"):
        print(f"  incidents: {r[0]}")
    for r in conn.execute("SELECT COUNT(*) FROM Fix"):
        print(f"  fixes: {r[0]}")
    for r in conn.execute("SELECT COUNT(*) FROM Person"):
        print(f"  people: {r[0]}")
    for r in conn.execute("SELECT COUNT(*) FROM LLMPrompt"):
        print(f"  prompts: {r[0]}")
    print("Selector volatility after seed:")
    for r in conn.execute("SELECT automation_id, selector_volatility FROM FragilitySignal ORDER BY selector_volatility DESC"):
        print(f"  {r[0]}: {r[1]:.4f}")
    conn.close()


if __name__ == "__main__":
    load()
