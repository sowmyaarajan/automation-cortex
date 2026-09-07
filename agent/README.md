# agent/ — UiPath Coded Agent: Adversarial Consultant (scaffolded Day 5)

## Planned scaffold (Day 5, via `uipath:uipath-agents` skill)
- LangGraph or OpenAI Agents flavor
- Tools: `search_genome`, `get_fragility`, `list_reusable_components`, `estimate_effort`, `recommend_modality`
- System prompt lives in `prompts/adversarial_system.md`

## Contract
Given a spec like *"I want to build an SAP invoice bot"* the agent MUST return:
1. Name of at least one similar existing automation (via `search_genome`).
2. At least one non-RPA alternative (API workflow / agent / IxP / HITL).
3. Effort estimate with AI-vs-human split.
4. At least one reason not to build.

If it cannot satisfy all four, it must say so explicitly rather than fabricate.

## Fallback (if `uip` tooling blocks on Day 5)
Implement as a plain FastAPI endpoint calling Claude directly. Lose the "real Coded Agent" claim, keep the feature.
