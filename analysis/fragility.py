"""
Fragility scoring — deterministic weighted formula.

Signals (all normalized to 0..1 across the corpus except selector_volatility which comes from the seeded run log):
  - selector_volatility     (higher = more selector-change incidents observed)
  - retry_density           (retry_blocks / activity_count)
  - exception_surface       (distinct exception types)
  - cross_app_coupling      (distinct applications touched)
  - hitl_coverage           (hitl_nodes / activity_count) — NEGATIVE weight

Score = w_sel*vol + w_ret*ret + w_exc*exc + w_app*app - w_hitl*hitl,
then rescaled to 0..100.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "cortex.sqlite"

W_SEL = 0.35
W_RET = 0.20
W_EXC = 0.15
W_APP = 0.20
W_HITL = 0.15


def compute():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    autos = conn.execute("""
        SELECT a.id, a.activity_count, a.retry_blocks, a.hitl_nodes,
               (SELECT COUNT(*) FROM ExceptionCaught WHERE automation_id = a.id) AS exc_count,
               (SELECT COUNT(*) FROM Application WHERE automation_id = a.id) AS app_count
        FROM Automation a
    """).fetchall()

    # Read selector_volatility already stored (seeded) if any
    vol_map = {r["automation_id"]: r["selector_volatility"] or 0
               for r in conn.execute("SELECT automation_id, selector_volatility FROM FragilitySignal")}

    # Normalizers (max across corpus)
    max_exc = max((r["exc_count"] for r in autos), default=1) or 1
    max_app = max((r["app_count"] for r in autos), default=1) or 1

    now = datetime.now(timezone.utc).isoformat()
    for r in autos:
        aid = r["id"]
        activity = max(r["activity_count"], 1)
        retry_density = r["retry_blocks"] / activity
        exception_surface = r["exc_count"] / max_exc
        cross_app_coupling = r["app_count"] / max_app
        hitl_coverage = r["hitl_nodes"] / activity
        selector_volatility = vol_map.get(aid, 0)

        raw = (W_SEL * selector_volatility
               + W_RET * retry_density
               + W_EXC * exception_surface
               + W_APP * cross_app_coupling
               - W_HITL * hitl_coverage)
        # rescale to 0..100 (raw is roughly bounded 0..1 in this corpus)
        score = max(0.0, min(100.0, raw * 100))

        conn.execute("""
            INSERT INTO FragilitySignal (automation_id, selector_volatility, retry_density,
                                         exception_surface, cross_app_coupling, hitl_coverage,
                                         score, computed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(automation_id) DO UPDATE SET
                selector_volatility = excluded.selector_volatility,
                retry_density = excluded.retry_density,
                exception_surface = excluded.exception_surface,
                cross_app_coupling = excluded.cross_app_coupling,
                hitl_coverage = excluded.hitl_coverage,
                score = excluded.score,
                computed_at = excluded.computed_at
        """, (aid, selector_volatility, retry_density, exception_surface,
              cross_app_coupling, hitl_coverage, score, now))

    conn.commit()
    print("Fragility scores:")
    for r in conn.execute("""SELECT a.project_name, f.score, f.selector_volatility, f.retry_density,
                                    f.exception_surface, f.cross_app_coupling, f.hitl_coverage
                             FROM Automation a JOIN FragilitySignal f ON a.id = f.automation_id
                             ORDER BY f.score DESC"""):
        print(f"  {r[0]:<32} score={r[1]:6.2f}  vol={r[2]:.2f} ret={r[3]:.2f} exc={r[4]:.2f} app={r[5]:.2f} hitl={r[6]:.2f}")
    conn.close()


if __name__ == "__main__":
    compute()
