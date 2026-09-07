# api/ — FastAPI backend

## Run
```powershell
pip install -r ..\requirements.txt
uvicorn api.main:app --reload --port 8000
```

## Endpoints (skeleton — real logic lands Day 2–4)
- `GET /health`
- `GET /automations` — list all
- `GET /automations/{id}` — full record + genome + capabilities + fragility
- `GET /fragility` — ranked list with score breakdown
- `GET /blast-radius/{node_type}/{node_value}` — `app | component | selector_app`
- `GET /similarity/{id}?min_score=0.3` — dedupe candidates
- `GET /sop/{id}?reverse=false` — Living or Reverse SOP
