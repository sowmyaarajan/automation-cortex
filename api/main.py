"""
Automation Cortex — FastAPI backend.

Skeleton with placeholder endpoints matching the Day 2–5 build plan.
Real query logic lands Day 3 (genome + fragility) and Day 4 (blast-radius + sops).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import io
import re
import zipfile

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api.consultant import plan as consultant_plan

DB_PATH = Path(__file__).parent.parent / "db" / "cortex.sqlite"

app = FastAPI(title="Automation Cortex API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev
    allow_methods=["*"],
    allow_headers=["*"],
)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@app.get("/health")
def health():
    return {"status": "ok", "db_exists": DB_PATH.exists()}


@app.get("/automations")
def list_automations():
    with db() as conn:
        rows = conn.execute(
            "SELECT id, project_name, intent, retry_blocks, hitl_nodes, activity_count FROM Automation ORDER BY project_name"
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/automations/{automation_id}")
def get_automation(automation_id: str):
    with db() as conn:
        row = conn.execute("SELECT * FROM Automation WHERE id = ?", (automation_id,)).fetchone()
        if not row:
            raise HTTPException(404, "automation not found")
        data = dict(row)
        data["genome"] = json.loads(data.pop("genome_json"))
        data["capabilities"] = [r["tag"] for r in conn.execute(
            "SELECT tag FROM Capability WHERE automation_id = ?", (automation_id,)).fetchall()]
        data["applications"] = [r["app_name"] for r in conn.execute(
            "SELECT app_name FROM Application WHERE automation_id = ?", (automation_id,)).fetchall()]
        frag_row = conn.execute(
            "SELECT * FROM FragilitySignal WHERE automation_id = ?", (automation_id,)).fetchone()
        frag = dict(frag_row) if frag_row else {}
        # Scale 0..1 sub-signals to 0..100 for the frontend; score is already 0..100
        for k in ("selector_volatility", "retry_density", "exception_surface",
                  "cross_app_coupling", "hitl_coverage"):
            if k in frag and frag[k] is not None:
                frag[k] = round(frag[k] * 100, 1)
        data["fragility"] = frag
    return data


@app.get("/fragility")
def fragility_ranking():
    """Day 3: ranked list with score breakdown."""
    with db() as conn:
        rows = conn.execute("""
            SELECT a.id, a.project_name, f.score, f.selector_volatility, f.retry_density,
                   f.exception_surface, f.cross_app_coupling, f.hitl_coverage
            FROM Automation a
            LEFT JOIN FragilitySignal f ON f.automation_id = a.id
            ORDER BY COALESCE(f.score, 0) DESC
        """).fetchall()
    return [dict(r) for r in rows]


@app.get("/blast-radius/{node_type}/{node_value}")
def blast_radius(node_type: str, node_value: str):
    """Day 4: given an app or selector, which automations break?"""
    if node_type not in {"app", "component", "selector_app"}:
        raise HTTPException(400, "node_type must be app | component | selector_app")
    with db() as conn:
        if node_type == "app":
            rows = conn.execute("""
                SELECT DISTINCT a.id, a.project_name, 'uses ' || ? AS reason
                FROM Automation a JOIN Application app ON app.automation_id = a.id
                WHERE app.app_name = ?
            """, (node_value, node_value)).fetchall()
        elif node_type == "component":
            rows = conn.execute("""
                SELECT DISTINCT a.id, a.project_name, 'invokes ' || ? AS reason
                FROM Automation a JOIN Component c ON c.automation_id = a.id
                WHERE c.invoked_path LIKE ? OR c.resolved_project = ?
            """, (node_value, f"%{node_value}%", node_value)).fetchall()
        else:  # selector_app
            rows = conn.execute("""
                SELECT DISTINCT a.id, a.project_name, 'has ' || COUNT(s.id) || ' ' || ? || ' selectors' AS reason
                FROM Automation a JOIN Selector s ON s.automation_id = a.id
                WHERE s.app_hint = ?
                GROUP BY a.id
            """, (node_value, node_value)).fetchall()
    return {"node_type": node_type, "node_value": node_value, "impacted": [dict(r) for r in rows]}


@app.get("/similarity/{automation_id}")
def similar_to(automation_id: str, min_score: float = 0.3):
    """Day 3: dedupe candidates."""
    with db() as conn:
        rows = conn.execute("""
            SELECT s.dst_id, a.project_name, s.score, s.method
            FROM Similarity s JOIN Automation a ON a.id = s.dst_id
            WHERE s.src_id = ? AND s.score >= ?
            ORDER BY s.score DESC
        """, (automation_id, min_score)).fetchall()
    return [dict(r) for r in rows]


@app.get("/sop/{automation_id}")
def get_sop(automation_id: str, reverse: bool = False):
    """Living SOP or Reverse SOP."""
    folder = Path(__file__).parent.parent / ("reverse_sops" if reverse else "sops")
    project_name = automation_id.split("::")[0]
    md_path = folder / f"{project_name}.md"
    if not md_path.exists():
        raise HTTPException(404, f"SOP not yet generated for {project_name}")
    return {"automation_id": automation_id, "reverse": reverse, "markdown": md_path.read_text(encoding="utf-8")}


# ---- Consultant ----

class ConsultantRequest(BaseModel):
    spec: str


@app.post("/consultant")
def consultant(req: ConsultantRequest):
    if not req.spec.strip():
        raise HTTPException(400, "spec is required")
    return consultant_plan(req.spec)


# ---- Experience + Analytics tiles ----

@app.get("/experience")
def experience():
    with db() as conn:
        rows = conn.execute("""
            SELECT i.id, i.automation_id, i.occurred_at, i.kind, i.summary,
                   f.remediation, f.applies_to_app, f.success_count, f.last_applied
            FROM Incident i LEFT JOIN Fix f ON f.id = i.fix_id
            ORDER BY i.occurred_at DESC
        """).fetchall()
    return [dict(r) for r in rows]


@app.get("/analytics")
def analytics():
    with db() as conn:
        dupe_pairs = conn.execute(
            "SELECT COUNT(*) FROM Similarity WHERE score >= 0.4 AND src_id < dst_id").fetchone()[0]
        automations = conn.execute("SELECT COUNT(*) FROM Automation").fetchone()[0]
        avg_frag = conn.execute("SELECT AVG(score) FROM FragilitySignal").fetchone()[0] or 0
        top_frag = conn.execute("""
            SELECT a.project_name, f.score
            FROM Automation a JOIN FragilitySignal f ON f.automation_id = a.id
            ORDER BY f.score DESC LIMIT 3
        """).fetchall()
        sop_count = len(list((Path(__file__).parent.parent / "sops").glob("*.md")))
    return {
        "dedupe_candidate_pairs": dupe_pairs,
        "automations_indexed": automations,
        "average_fragility": round(avg_frag, 2),
        "top_fragile": [dict(r) for r in top_frag],
        "sops_generated": sop_count,
    }


# ---- Knowledge Graph (Iteration 4) ----

@app.get("/knowledge-graph")
def knowledge_graph():
    """Full estate as a graph: bots + apps + incidents + people + LLM prompts, plus all edges."""
    with db() as conn:
        # Nodes
        nodes: list[dict] = []
        for r in conn.execute("SELECT a.id, a.project_name, a.intent, COALESCE(f.score,0) AS risk "
                              "FROM Automation a LEFT JOIN FragilitySignal f ON f.automation_id = a.id"):
            nodes.append({"id": f"bot:{r['id']}", "kind": "bot", "label": r["project_name"],
                          "intent": r["intent"], "risk": round(r["risk"], 1)})
        app_counts: dict[str, int] = {}
        for r in conn.execute("SELECT app_name, COUNT(DISTINCT automation_id) AS c FROM Application GROUP BY app_name"):
            app_counts[r["app_name"]] = r["c"]
            nodes.append({"id": f"app:{r['app_name']}", "kind": "app", "label": r["app_name"], "count": r["c"]})
        for r in conn.execute("SELECT id, occurred_at, kind, summary, automation_id FROM Incident"):
            nodes.append({"id": f"incident:{r['id']}", "kind": "incident",
                          "label": r["summary"][:60] + ("…" if len(r["summary"] or "") > 60 else ""),
                          "date": r["occurred_at"], "severity": r["kind"], "bot_id": r["automation_id"]})
        for r in conn.execute("SELECT id, name, role, team FROM Person"):
            nodes.append({"id": f"person:{r['id']}", "kind": "person", "label": r["name"],
                          "role": r["role"], "team": r["team"]})
        for r in conn.execute("SELECT id, title, when_to_use FROM LLMPrompt"):
            nodes.append({"id": f"prompt:{r['id']}", "kind": "prompt", "label": r["title"],
                          "when_to_use": r["when_to_use"]})

        # Edges
        edges: list[dict] = []
        for r in conn.execute("SELECT automation_id, app_name FROM Application"):
            edges.append({"src": f"bot:{r['automation_id']}", "dst": f"app:{r['app_name']}", "kind": "uses"})
        for r in conn.execute("SELECT id, automation_id, resolved_by, prompt_id FROM Incident"):
            edges.append({"src": f"bot:{r['automation_id']}", "dst": f"incident:{r['id']}", "kind": "had"})
            if r["resolved_by"]:
                edges.append({"src": f"incident:{r['id']}", "dst": f"person:{r['resolved_by']}", "kind": "resolved_by"})
            if r["prompt_id"]:
                edges.append({"src": f"incident:{r['id']}", "dst": f"prompt:{r['prompt_id']}", "kind": "used"})
                # prompt → updated bot (the loop closes)
                edges.append({"src": f"prompt:{r['prompt_id']}", "dst": f"bot:{r['automation_id']}", "kind": "updated"})
        # Similarity (bot ↔ bot)
        seen = set()
        for r in conn.execute("SELECT src_id, dst_id, score FROM Similarity WHERE score >= 0.4"):
            key = tuple(sorted((r["src_id"], r["dst_id"])))
            if key in seen:
                continue
            seen.add(key)
            edges.append({"src": f"bot:{r['src_id']}", "dst": f"bot:{r['dst_id']}",
                          "kind": "similar_to", "score": round(r["score"], 2)})

    return {"nodes": nodes, "edges": edges}


@app.get("/search")
def graph_search(q: str = ""):
    """Case-insensitive keyword search across all knowledge-graph node kinds."""
    q = (q or "").strip().lower()
    if not q:
        return {"query": q, "matched_node_ids": []}
    like = f"%{q}%"
    matched: list[str] = []
    with db() as conn:
        for r in conn.execute("SELECT id FROM Automation WHERE lower(project_name) LIKE ? OR lower(COALESCE(intent,'')) LIKE ?", (like, like)):
            matched.append(f"bot:{r['id']}")
        for r in conn.execute("SELECT DISTINCT app_name FROM Application WHERE lower(app_name) LIKE ?", (like,)):
            matched.append(f"app:{r['app_name']}")
        for r in conn.execute("SELECT id FROM Incident WHERE lower(COALESCE(summary,'')) LIKE ? OR lower(kind) LIKE ?", (like, like)):
            matched.append(f"incident:{r['id']}")
        for r in conn.execute("SELECT id FROM Person WHERE lower(name) LIKE ? OR lower(COALESCE(role,'')) LIKE ?", (like, like)):
            matched.append(f"person:{r['id']}")
        for r in conn.execute("SELECT id FROM LLMPrompt WHERE lower(title) LIKE ? OR lower(COALESCE(when_to_use,'')) LIKE ?", (like, like)):
            matched.append(f"prompt:{r['id']}")
    return {"query": q, "matched_node_ids": matched}


# ---- Upload ----

CORPUS_DIR = Path(__file__).parent.parent / "demo" / "corpus"
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def _slug(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", stem)
    return stem[:64] or "uploaded"


@app.post("/upload")
async def upload_project(file: UploadFile = File(...)):
    """Accept a .zip of a UiPath project. Extract into demo/corpus, run the full rebuild."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "please upload a .zip file")

    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(413, "file too large (max 50MB)")

    slug = _slug(file.filename)
    target = CORPUS_DIR / slug
    # Wipe existing target with same name so re-uploads work
    if target.exists():
        import shutil
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            # Zip-slip guard
            for member in zf.namelist():
                if member.startswith("/") or ".." in Path(member).parts:
                    raise HTTPException(400, f"unsafe path in zip: {member}")
            zf.extractall(target)
    except zipfile.BadZipFile:
        raise HTTPException(400, "not a valid zip file")

    # Find project.json — could be nested inside a top-level folder
    project_jsons = list(target.rglob("project.json"))
    if not project_jsons:
        import shutil
        shutil.rmtree(target)
        raise HTTPException(400, "no project.json found in zip — is this a UiPath project?")

    # If the zip had a single top-level folder, flatten it so the corpus is clean
    top_level = [p for p in target.iterdir() if p.is_dir()]
    if len(top_level) == 1 and not (target / "project.json").exists():
        import shutil
        inner = top_level[0]
        for item in inner.iterdir():
            shutil.move(str(item), str(target / item.name))
        inner.rmdir()

    # Rebuild the whole pipeline
    try:
        from rebuild import rebuild
        summary = rebuild()
    except Exception as e:
        raise HTTPException(500, f"rebuild failed: {e}")

    return {"ok": True, "uploaded_as": slug, **summary}


# ---- Static UI ----

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    idx = STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(idx)
    return {"message": "UI not built yet. See api/static/index.html."}
