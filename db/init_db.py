"""Create db/cortex.sqlite from schema.sql. Idempotent."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "cortex.sqlite"
SCHEMA = Path(__file__).parent / "schema.sql"


def init():
    # Drop old DB so schema changes (new columns, new tables) apply cleanly.
    # Everything is re-ingested from JSON, so no user data is lost.
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    conn.close()
    print(f"Initialized {DB_PATH}")
    print("Tables:", tables)


if __name__ == "__main__":
    init()
