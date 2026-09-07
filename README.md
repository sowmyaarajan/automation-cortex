# Automation Cortex

Living intelligence layer over a UiPath automation estate. Extracts a **Genome** per automation, scores **Fragility**, computes **Blast Radius**, generates **Living SOPs** (and Reverse SOPs for human fallback), and answers design questions via an **Adversarial Consultant** (real UiPath Coded Agent).

Hackweek build. Submission: **Mon 2026-07-13**.

## Layout
```
parser/    Static UiPath parser (.xaml + project.json → Genome JSON)
genome/    Per-project Genome JSON outputs
db/        SQLite schema + init script
api/       FastAPI backend serving the UI
web/       Next.js dashboard (scaffolded Day 2)
agent/     UiPath Coded Agent — Consultant (scaffolded Day 5)
sops/      Generated Living SOPs (Markdown)
reverse_sops/  Generated Reverse SOPs (Markdown)
demo/corpus/   6 synthetic UiPath projects for the demo
```

## Day 1 status (done)
- [x] Parser handles all 6 synthetic projects
- [x] Genome JSON validates against schema
- [x] SQLite DB initialized
- [x] FastAPI skeleton with placeholder endpoints
- [x] All directories laid out

## Quick verification
```powershell
python parser/parse_project.py --all demo/corpus --out genome
python db/init_db.py
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
# then GET http://localhost:8000/health
```

## Plan
See `C:\Users\Sowmya.Rajan\.claude\plans\givw-me-plan-of-elegant-emerson.md`.
