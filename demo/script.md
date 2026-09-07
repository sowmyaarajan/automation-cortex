# Automation Cortex — 2-Minute Elevator Pitch

## Setup (once, before recording)
```powershell
python -m uvicorn api.main:app --port 8000
```
Open **http://localhost:8000** — you land on **🧠 Advisor**.

---

## Cold open (10 seconds)

> "Every UiPath team ships bots on top of bots. Nobody remembers what's already built, what's about to break, or whether they should even build the thing they're about to build. **Cortex answers all three — before you write a single .xaml.**"

---

## 🧠 Advisor — the hook (50 seconds)

Click the sample chip **"I want to build an SAP invoice bot"**. Hit Enter. Let it load.

Read the argument card aloud, verbatim.

> "This is Cortex arguing with me. Not agreeing — arguing.
> It found the bot I'm about to duplicate. It told me RPA is the wrong approach. It named the reusable components I was ignoring. Effort estimated in dev-days.
> **Every AI copilot says 'great idea'. This one says 'wait.'**"

Point at the four cards below:
> "Already exists. Recommended approach. Reuse these. Effort.
> A design review from a senior engineer — in one second."

---

## 🧬 Genome — proof it's real (30 seconds)

Switch tabs. Click any bot in the list — the risk-color dot tells you which are risky.

Point at the risk sub-tab bars:
> "Every bot gets a **risk score from 0 to 100** — predictive, not reactive. Five signals: UI drift, retry rate, error variety, app count, minus the human safety net.
> UiPath tells you what failed yesterday. Cortex tells you what's failing tomorrow."

Click the Duplicates sub-tab:
> "This bot's login logic is duplicated in the Shared_Utilities library. Delete one, save maintenance forever."

---

## 💥 Impact Map — the crescendo (25 seconds)

Switch tabs. Click **SAP** in the left panel.

> "SAP is patching next Tuesday. What breaks? — three bots, right there, in red. Non-impacted bots fade to grey.
> Click ActiveDirectory. Different bots. Different answer.
> No Confluence page. No emails to the team. The answer, live."

---

## 📖 Playbooks — the safety net (15 seconds)

Switch tabs. Pick a bot. Toggle **Human Playbook**.

> "Every bot ships with two playbooks — one the bot follows, one a human can follow if the bot dies at month-end.
> Auto-written from the code. Never goes stale."

---

## 🚀 Studio Preview — the vision (15 seconds)

Switch tabs.

> "Today Cortex is a web app. Tomorrow — same brain, right inside Studio.
> Developer opens a bot: risk score, duplicates, reusable components, all in the side panel.
> **The argument happens where the code is written.**"

---

## Close (5 seconds)

> "Reads your estate. Argues before you build. Shows you what breaks.
> **Automation Cortex.**"

---

## Total: ~2 minutes 30 seconds
Deliver at pace — silence between sections, not filler.

## What the audience remembers
- **"The AI that argues."** One phrase. Repeat it in the close if time.
- **Predictive risk, not reactive.**
- **Studio extension is next.**

## Fallback if something breaks
- Advisor slow → hit a different sample chip while the first loads.
- Impact Map graph doesn't render → the app filter card still shows counts and the impacted list still populates below.
- LLM down → the argument card fills with the deterministic template. Don't apologize; the app never breaks.

## What backs each moment
| Moment | Files |
|---|---|
| Advisor | `api/consultant.py` + `llm/prompts.py:CONSULTANT_*` |
| Risk bars | `analysis/fragility.py` (5-signal formula) |
| Duplicates | `analysis/similarity.py` (Jaccard on skills + selectors) |
| Impact Map | `api/main.py:/blast-radius` + cytoscape.js |
| Playbooks | `generators/sop.py` + `llm/prompts.py:SOP_*` |
| Studio Preview | `api/static/index.html` (mock, honestly labelled) |

## Who it's for
- **Buyer**: RPA Center-of-Excellence leads / Automation Architects at enterprises with 20+ bots
- **Heavy user**: RPA developers about to build a new bot (Advisor + Studio extension)
- **Occasional user**: Ops / production support (Impact Map + Playbooks)
