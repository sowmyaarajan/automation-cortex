"""Enrich all genome JSON files with deterministic intent + capabilities."""
from __future__ import annotations

import json
from pathlib import Path

from enrichment.rules import derive_capabilities, derive_intent

GENOME_DIR = Path(__file__).parent.parent / "genome"


def enrich_file(path: Path) -> None:
    genome = json.loads(path.read_text(encoding="utf-8"))
    caps = derive_capabilities(genome)
    intent = derive_intent(genome, caps)
    genome["capabilities"] = caps
    genome["intent"] = intent
    path.write_text(json.dumps(genome, indent=2), encoding="utf-8")
    print(f"[enriched] {path.name}")
    print(f"  intent: {intent}")
    print(f"  capabilities: {caps}")


def main():
    for f in sorted(GENOME_DIR.glob("*.json")):
        enrich_file(f)


if __name__ == "__main__":
    main()
