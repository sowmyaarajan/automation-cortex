"""
Deterministic similarity between automations.

Feature bag per automation:
  { "cap:<tag>", "app:<name>", "sel:<normalized_selector>" }

normalized_selector = strip whitespace, lowercase, keep only wnd/app/cls/webctrl attribute skeleton.

Jaccard similarity = |A ∩ B| / |A ∪ B|. Stored bidirectionally.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "cortex.sqlite"


def normalize_selector(raw: str) -> str:
    # keep tag skeleton, drop text values, lowercase
    skel = re.sub(r"'[^']*'", "'*'", raw)
    skel = re.sub(r'"[^"]*"', '"*"', skel)
    skel = re.sub(r"\s+", " ", skel).strip().lower()
    return skel


def features_for(conn: sqlite3.Connection, aid: str) -> set[str]:
    feats: set[str] = set()
    for r in conn.execute("SELECT tag FROM Capability WHERE automation_id = ?", (aid,)):
        feats.add(f"cap:{r[0]}")
    for r in conn.execute("SELECT app_name FROM Application WHERE automation_id = ?", (aid,)):
        feats.add(f"app:{r[0]}")
    for r in conn.execute("SELECT raw FROM Selector WHERE automation_id = ?", (aid,)):
        feats.add(f"sel:{normalize_selector(r[0])}")
    return feats


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def compute():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ids = [r["id"] for r in conn.execute("SELECT id FROM Automation ORDER BY project_name")]
    feats = {aid: features_for(conn, aid) for aid in ids}

    conn.execute("DELETE FROM Similarity")
    for i, a in enumerate(ids):
        for j, b in enumerate(ids):
            if i == j:
                continue
            score = jaccard(feats[a], feats[b])
            if score > 0:
                conn.execute("INSERT OR REPLACE INTO Similarity (src_id, dst_id, score, method) VALUES (?, ?, ?, ?)",
                             (a, b, score, "jaccard"))
    conn.commit()

    print("Top similarity pairs (score >= 0.30):")
    for r in conn.execute("""
        SELECT s.src_id, s.dst_id, s.score
        FROM Similarity s
        WHERE s.score >= 0.30 AND s.src_id < s.dst_id
        ORDER BY s.score DESC
    """):
        print(f"  {r[0]}  <->  {r[1]}   {r[2]:.3f}")
    conn.close()


if __name__ == "__main__":
    compute()
