# web/ — Next.js dashboard (scaffolded Day 2 morning)

## Planned scaffold (Day 2)
```powershell
npx create-next-app@latest . --typescript --tailwind --app --eslint --src-dir --import-alias "@/*"
npx shadcn@latest init
npx shadcn@latest add button card table tabs dialog badge sheet
npm install reactflow
```

## Tabs
1. **Genome Explorer** — clusters + dedupe suggestions
2. **Fragility Dashboard** — ranked list + Experience panel
3. **Blast Radius** — reactflow graph, pick node → downstream highlighted
4. **Consultant Chat** — talks to UiPath Coded Agent
5. **Living SOP Viewer** — Markdown + Reverse SOP tab

Backend: `http://localhost:8000` (see `../api/`).
