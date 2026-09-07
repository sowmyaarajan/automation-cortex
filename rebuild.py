"""
One-command rebuild of the whole Cortex pipeline against a corpus folder.

Usage:
    python rebuild.py                          # default: demo/corpus
    python rebuild.py C:\\path\\to\\projects   # any folder holding UiPath projects

Callable as a module too (used by the /upload endpoint):
    from rebuild import rebuild
    rebuild()
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def _run(cmd: list[str]) -> None:
    """Run a subprocess and print output. Raises on failure."""
    print(f"$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, flush=True)
        raise RuntimeError(f"command failed with exit {result.returncode}: {' '.join(cmd)}")


def rebuild(corpus_dir: str | Path = None) -> dict:
    """Run the full pipeline. Returns a summary dict."""
    corpus = Path(corpus_dir) if corpus_dir else ROOT / "demo" / "corpus"
    if not corpus.exists():
        raise FileNotFoundError(f"corpus not found: {corpus}")

    py = sys.executable

    _run([py, "parser/parse_project.py", "--all", str(corpus), "--out", "genome"])
    _run([py, "-m", "enrichment.enrich"])
    _run([py, "db/init_db.py"])
    _run([py, "db/ingest.py"])
    _run([py, "-m", "analysis.similarity"])
    _run([py, "db/seed_experience.py"])
    _run([py, "-m", "analysis.fragility"])
    _run([py, "-m", "generators.sop"])

    # Count outputs
    genome_count = len(list((ROOT / "genome").glob("*.json")))
    sop_count = len(list((ROOT / "sops").glob("*.md")))
    return {"corpus": str(corpus), "bots": genome_count, "sops": sop_count}


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    summary = rebuild(arg)
    print(f"\n[done] {summary}")
