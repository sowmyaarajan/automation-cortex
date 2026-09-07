# Handoff: Automation Cortex — Frontend Redesign

## Overview
Automation Cortex is a **data-heavy internal tool** that reads a company's library of UiPath bots (folders of `.xaml` files) and provides a design-review layer over the automation estate. It has five capabilities exposed as five tabs, plus an "Add project" upload flow.

- **Advisor** — user describes a bot idea; the app returns an "adversarial" argument (already exists / better approach / reusable parts / effort estimate).
- **Genome** — inventory of every indexed bot: profile, fragility score, skills, duplicates.
- **Blast Radius** (formerly "Impact Map") — interactive Obsidian-style graph: select an application (SAP, Excel, …) and see which bots break if it changes.
- **Playbooks** — auto-generated Markdown: "Bot Playbook" and "Human Fallback SOP" per bot.
- **Studio** (formerly "Studio Preview") — roadmap mock of the tool embedded as a side-panel inside UiPath Studio.

Audience: RPA Center-of-Excellence leads & Automation Architects (primary), RPA developers (Advisor), Ops/production support (Blast Radius + Playbooks).

## About the Design Files
The file in this bundle (`index.html`) is a **design reference created in HTML** — a working prototype showing the intended look and behavior. It is **not** production code to copy directly.

The prototype is intentionally a single self-contained `index.html` using **Tailwind (CDN), Alpine.js, cytoscape.js, and marked.js** — this was a hard constraint of the original brief ("single index.html, no build step, ready to drop into `api/static/`"). It talks to a set of backend endpoints (documented below) and falls back to bundled mock data when they are unreachable, so it also runs standalone as a demo.

Your task: **recreate this design in the target codebase's environment.** If the goal is still a zero-build static file served from `api/static/`, the prototype can be used almost as-is. If it is being folded into a component framework (React/Vue/etc.), recreate the UI with the codebase's existing patterns while preserving the exact visual spec, interactions, and — critically — the **backend API contracts**, which must not change.

## Fidelity
**High-fidelity (hifi).** Final colors, typography, spacing, iconography and interactions are all specified. Recreate the UI pixel-perfectly. All hex values, font sizes, and animation timings below are the source of truth.

---

## Design Tokens

### Colors
| Token | Hex | Use |
|---|---|---|
| ink-900 | `#111113` | Primary text, dark buttons, logo mark |
| ink-700 | `#37373c` | Body text, button hover |
| ink-500 | `#6f6f78` | Secondary text, labels (AA on white) |
| ink-400 | `#8b8b94` | (avoid for text — decorative only) |
| ink-300 | `#b4b4bc` | Disabled / faint bars |
| line | `#e7e7ea` | Hairline borders, dividers |
| paper | `#fafafa` | App background, chip fills |
| accent | `#5b5bd6` | Primary indigo accent |
| accent-soft | `#eeeefc` | Accent chip/background wash |
| accent-dark | `#4747b8` | Accent text on light |
| graph-bg | `#1c1c22` | Blast Radius canvas background (dark slate) |
| graph-panel | `#242430` | Floating panels on the graph |
| graph-line | `#2a2a32` | Graph panel borders |

**Risk / fragility color ramp** (applied to dots, bars, numbers):
- score ≥ 30 → red (`bg-red-500` `#ef4444` / `text-red-600`)
- score ≥ 25 → orange (`bg-orange-400` `#fb923c` / `text-orange-500`)
- score ≥ 18 → amber (`bg-amber-400` `#fbbf24` / `text-amber-500`)
- score < 18 → emerald (`bg-emerald-500` `#22c55e` / `text-emerald-600`)
- Soft variants for tiles: red-50/border-red-200, orange-50/orange-200, amber-50/amber-200, emerald-50/emerald-200.
- Risk labels: ≥30 "High fragility", ≥25 "Elevated", ≥18 "Moderate", else "Stable".

**Ember (graph highlight)**: `#e0684b` — the ONLY color used inside the dark graph; applied to impacted nodes/edges on selection.

### Typography
- **Sans**: `Geist` (Google Fonts, weights 400/500/600/700). Fallback `system-ui, sans-serif`.
- **Mono**: `Geist Mono` (weights 400/500/600). Used for bot/app names, metrics, uppercase labels, code.
- `font-feature-settings: "cv11","ss01"` on `html`.
- Uppercase micro-labels: mono, 10.5–11px, `tracking-widest` (0.1em), color ink-500.
- Section headings in cards: same micro-label style.
- Hero H1: 38px / weight 600 / tracking-tight / line-height 1.05.
- Card titles: 15–16px / 600.
- Body: 13–15.5px / 400 / line-height 1.5–1.7.

### Spacing / radius / shadow
- Page max width: `1400px`, horizontal padding `32px` (px-8).
- Header height: `60px`; tab bar height: `40px`.
- Radius: chips/pills `6–8px` (rounded-md/lg), cards `12px` (rounded-xl), modal `16px` (rounded-2xl), full pills `9999px`.
- Card border: `1px solid #e7e7ea` on white.
- Card shadow (subtle): `0 1px 2px rgba(0,0,0,0.04)` and `0 1px 3px rgba(0,0,0,0.05)`.
- Modal shadow: `shadow-2xl`; Studio window: `0 24px 60px -12px rgba(17,17,19,0.25)`.
- Focus ring: `2px solid #5b5bd6`, offset 2px, on all interactive elements.

### Icons
All icons are **inline SVG**, 1.3px stroke, `stroke-linecap/linejoin round`, sized 12–18px. No icon fonts, no emoji. Tab icons: advisor (lightbulb), genome (double-helix), impact (constellation of dots), playbooks (open book), studio (window). App/bot node glyphs are baked SVG data-URIs (see Blast Radius).

---

## Screens / Views

### Global chrome (header + tabs)
- **Header** (white, bottom border `line`, 60px): left = 26px rounded-square logo mark (ink-900 bg, white constellation SVG) + "Automation Cortex" (15px/600) + mono "estate intelligence" caption. Right (from `/analytics`) = estate vitals row: `automations_indexed` bots · `dedupe_candidate_pairs` duplicate pairs · avg fragility number + a 56px mini bar colored by the risk ramp · **"+ Add project"** button (32px tall, ink-900 bg, white, radius 8px).
- **Tab bar**: 5 tabs, each 40px tall, 13px/500. Active tab = ink-900 text + 2px ink-900 bottom border; inactive = ink-500, hover ink-700. "Studio" tab carries a mono "soon" badge (accent-soft bg, accent text). `role="tablist"`, `aria-selected` on each.

### 1. Advisor (landing)
- **Purpose**: pre-build gut-check; get pushback from the estate.
- **Layout**: centered column, `max-width: 780px`, vertically centered in the viewport (`min-height: calc(100vh - 101px)`, flex column justify-center). Once a verdict exists, the column top-aligns (`self-start`).
- **Hero**: brand lockup (36px rounded mark + "Automation " + accent "Cortex" at 26px/600) · mono "adversarial review" eyebrow with a 4px accent dot · H1 "The estate argues back." (38px/600) · subhead 15.5px ink-500, max 520px.
- **Input card**: white, border line, radius 12px, padding 6px. Contains a 2-row auto-expanding `<textarea>` (15px, transparent bg, placeholder ink-500). Footer row: mono "⌘↵ to submit" (ink-500) left; **"Challenge it"** button right (ink-900, 32px, disabled at 40% opacity when empty/loading; loading = spinner + "Consulting estate…"). Card border darkens to ink-300 on focus-within.
- **Suggestion chips** (shown until first verdict): pill buttons, 28px tall, border line, 12.5px ink-500, hover ink-900 + border ink-300. Clicking fills the textarea and submits.
- **Verdict** (after `POST /consultant`), stacked with 16px gaps:
  1. **Adversarial paragraph card**: white card, inner content has a `3px` accent left-border, `px-6 py-5`. Header row: mono accent "the pushback" + a pill (`modality`, e.g. "EXTEND, DON'T BUILD", ink-900 bg white text). Body: 15px ink-700, relaxed leading.
  2. **Two-column grid** (gap 16px):
     - *"Already in the estate"* card: for each `similar_automations` entry — mono name (hover accent, click → Genome for that bot) + right-aligned percent + a 3px accent progress bar at `score×100%`.
     - Right card: *"Effort if you build anyway"* — big 26px number split from `effort_estimate` + trailing text; *"Reusable today"* — `reusable_components` as accent-soft mono chips.
  3. *"Reasons not to build"* card: numbered list (`01`, `02`… mono ink-400), 13.5px ink-700.

### 2. Genome
- **Purpose**: read the whole estate state in under 5 seconds.
- **Layout**: full-width. Top = 4-column estate strip; below = flex row of a table (flex-1) + a 360px detail drawer (appears when a bot is selected).
- **Estate strip** (4 tiles, hairline-separated, radius 12px overall): (1) *Indexed* — bot count (28px/600) "automations"; (2) *Risk spread* — a row of vertical bars, one per bot sorted by fragility desc, each colored by the risk ramp, height ∝ score; (3) *Duplication* — `dedupe_candidate_pairs` big number "candidate pairs to merge"; (4) *Most fragile* — top bot's mono name + a dot + "score N.N".
- **Table**: sticky-styled header row (mono 10.5px uppercase ink-400): columns `Automation | Fragility | (bar) | Applications | Activities | HITL`, grid template `minmax(220px,1.4fr) 80px minmax(140px,1fr) minmax(160px,1fr) 70px 70px`, 16px gaps. Each row is a button:
  - Automation cell: risk dot (7px, ramp color) + mono name (13px/500) + intent one-liner (12px ink-500) indented under it.
  - Fragility: mono number colored by ramp.
  - Bar: 4px track, fill = `min(100, score×2)%`, ramp color.
  - Applications: small mono chips (paper bg, border line).
  - Activities: mono ink-500 right-aligned.
  - HITL: `N ✓` (ink-700) if hitl_nodes>0 else `—` (ink-300).
  - Hover: bg paper. Selected: `bg-accent-soft/50`.
- **Detail drawer** (360px, sticky top-6, closable ×):
  - Mono title (break-all) + intent (13px ink-500).
  - 52px rounded risk tile (soft bg by ramp) with the score, next to risk label + "composite fragility".
  - *Fragility anatomy*: 5 rows (Selector volatility, Retry density, Exception surface, Cross-app coupling, HITL coverage), each `130px label | bar | value`; bar red ≥60 / orange ≥35 / ink-300 else.
  - *Skills*: `capabilities[]` as paper/border mono chips.
  - *Likely duplicates*: from `/similarity/{id}` — mono name + accent bar + percent.
  - Footer button "Open playbook →" → Playbooks tab for that bot.

### 3. Blast Radius (the signature "one strong personality moment")
- **Purpose**: pick an application, see the blast radius of a change.
- **Layout**: one dark rounded panel filling `height: calc(100vh - 180px)` (min 560px), border graph-line, bg graph-bg. A cytoscape `<div id="cy">` fills it absolutely. Floating UI sits on top.
- **Aesthetic = Obsidian graph view**: flat dark-slate canvas, small monochrome dots, hairline edges, **airy** (nodes never fill the frame). No glow, no stars, no pulsing.
  - **Nodes**: light-grey discs (`#9a9aa6` bots, `#b9b9c6` apps) with a **dark baked-in glyph** (`#2c2c34`/`#33333c`) at 58% and the label in Geist 9px below (`#8a8a95`). Size by degree via `mapData(deg,1,6,…)`: bots 15→34px, apps 22→46px.
  - **App glyphs**: SAP=database stack, Excel=grid, Outlook=envelope, Browser=globe, ActiveDirectory=users.
  - **Bot glyphs** (chosen by name regex): onboarding/hr→people, invoice/vendor/sap/posting→receipt, excel/recon/report→bar-chart, email/intake→envelope, util/shared/library→stacked blocks, else→generic bot.
  - **Edges**: 1px, `#ffffff` at opacity 0.12 (`uses`), dashed opacity 0.08 (`sim` = similarity links).
  - **Zoom is capped airy**: after layout, `fit(80px padding)` then if zoom > 1.15 force zoom 1.0 + center. minZoom 0.3, maxZoom 2.2.
- **Interactions**:
  - **On open**: physics layout (`cose`) re-runs animated (`animationDuration:1100`, ease-out, `randomize:true`) so the map visibly re-settles, then fits airy.
  - **Hover a node**: dim all (opacity 0.14 / edges 0.04), light up its closed neighborhood (class `near`).
  - **Tap an app node OR a left-panel row**: selects that app — dims everything, app node → `hotcenter` (light disc), impacted bots → `hot` (ember `#e0684b`), their edges → ember; then **animated pan/zoom** to that subset (700ms ease-in-out-cubic, target zoom capped at 1.5).
  - **Tap a bot node**: focus + zoom into its neighborhood (600ms).
  - **Tap empty canvas / "Clear selection"**: animated zoom back out to the full airy view (650ms).
  - **Resize**: ResizeObserver → `cy.resize()` + re-fit (airy) or re-zoom to current selection.
- **Floating control panel** (top-left, 248px, graph-panel/90 + backdrop-blur, radius 8px, shadow `0 8px 24px rgba(0,0,0,.4)`): mono "IF THIS CHANGES…" header; list of apps (dot + name + bot-count, active row bg white/7%); when an app is selected, a divider then "N bots break" (ember) + scrollable list of impacted `project_name` + `reason` (white/65 for AA) + "Clear selection".
- **Legend** (bottom-left pill) and **hint** (bottom-right pill): graph-panel/90, white/60 text. Legend: application / bot / impacted / similarity(dashed).

### 4. Playbooks
- **Purpose**: the only long-form Markdown surface.
- **Layout**: 260px left list + flex-1 document.
- **Left**: search input (filters by name) + bot rows (risk dot + mono name; active row = white card w/ border).
- **Right**: breadcrumb (mono "PLAYBOOK / <bot>") + a segmented toggle **"Bot playbook" / "Human fallback"** (p-0.5 track bg line/60, active = white card + shadow). Below, a **paper document**: white card, `px-12 py-10`, max 880px, subtle shadow. Meta row of mono chips ("LIVING SOP" or "HUMAN FALLBACK SOP" · "generated from XAML" · "refreshes every run"). Then rendered Markdown (from `/sop/{id}?reverse=bool`, parsed with marked.js) using the `.doc` typography (see CSS in file): H1 22px, H2 with top divider, mono inline code with chip styling, styled tables, accent blockquote, mono ordered-list markers.

### 5. Studio (roadmap)
- **Purpose**: vision slide — Cortex as a side-panel inside UiPath Studio.
- **Layout**: eyebrow + H1 "Same brain, inside Studio." + subhead, then a **dark window mock** (radius 12px, big soft shadow): traffic-light title bar (`UiPath Studio — SAP_InvoicePosting / Main.xaml`), then a 2-col grid `1fr 380px`:
  - Left: syntax-highlighted XAML `<pre>` (line numbers, colored tokens `#7d8bd4`/`#9aa5b8`/`#a3be8c`), with inline pills: ember "duplicate" on line 3, amber "volatile" on line 8.
  - Right ("CORTEX PANEL", border-left): fragility bar (58%, amber, "29.0") · ember-left-border "Duplicate detected" card w/ "Replace with reference" button · "8 UI changes last month" card · "Reusable components" chips.
  - All dark-panel text uses white/60–85 for AA.

### Upload modal ("Add project")
- Fixed overlay, `bg-ink-900/40` + blur, centered 440px white card (radius 16px). Title + description. Dashed drop zone (border line, hover ink-300, drag-over accent + accent-soft wash) accepting `.zip` — shows filename + size once chosen. On success (`POST /upload`) shows an accent-soft banner "Indexed N bots · generated N playbooks". Cancel / "Upload & index" buttons. **Keyboard**: `Escape` closes; focus is trapped (`x-trap`), Alpine focus plugin.

---

## Interactions & Behavior
- **Tab switching**: Alpine `tab` state; entering Blast Radius lazily inits/animates the cytoscape graph on `$nextTick`.
- **Advisor submit**: `⌘/Ctrl + Enter` or button; shows spinner; on failure falls back to mock after ~700ms.
- **Genome row → drawer**; drawer "Open playbook" → Playbooks tab preloaded.
- **Blast Radius**: full animation spec above (open re-settle 1100ms; select 700ms; bot focus 600ms; clear 650ms; hover instant with 160ms transitions).
- **Playbooks toggle** re-fetches SOP with `reverse` flag.
- **Upload**: drag/drop or browse; Escape to close; focus trap; success banner; refreshes estate afterward.
- **All transitions** use ease-in-out-cubic for viewport moves; 160ms for node style transitions; standard Tailwind `transition-colors` (150ms) for chrome.

## State Management
Single Alpine `app()` component. Key state:
- `tab` (active tab id), `analytics`, `bots[]` (each enriched with detail: capabilities, applications, fragility, `fragility_score`), `apps[]` (name + count, derived from bots).
- Advisor: `spec`, `asking`, `verdict`, `suggestions`.
- Genome: `selectedBot`, `selectedDupes`.
- Blast Radius: `impactApp`, `impacted[]`, `cy` (cytoscape instance).
- Playbooks: `playbookBot`, `playbookSearch`, `sopReverse`, `sopHtml`, `sopLoading`.
- Upload: `uploadOpen`, `uploadFile`, `uploading`, `uploadResult`, `dragOver`.
- **Init**: `Promise.all` of `/analytics` + `/automations`, then per-bot `/automations/{id}` to enrich, then derive `apps`, preload first playbook.
- **Mock fallback**: every fetch is wrapped so the UI still works offline (see `MOCK` object in the file). In production the mocks are dead code you can delete.

## Backend API contracts (DO NOT CHANGE THESE SHAPES)
```
GET  /automations             → [{id, project_name, intent, retry_blocks, hitl_nodes, activity_count}]
GET  /automations/{id}        → {..., capabilities:[str], applications:[str],
                                  fragility:{score, selector_volatility, retry_density,
                                  exception_surface, cross_app_coupling, hitl_coverage}}
GET  /fragility               → same rows as /automations, sorted by score desc
GET  /similarity/{id}?min_score=0.3  → [{dst_id, project_name, score, method}]
GET  /blast-radius/app/{name} → {node_type, node_value, impacted:[{id, project_name, reason}]}
GET  /sop/{id}?reverse=bool   → {markdown}
POST /consultant   body {spec} → {adversarial_paragraph, similar_automations, modality,
                                  reusable_components, effort_estimate, reasons_not_to_build}
GET  /experience              → [{automation_id, occurred_at, kind, summary, remediation}]
GET  /analytics               → {automations_indexed, dedupe_candidate_pairs, average_fragility,
                                  top_fragile, sops_generated}
POST /upload   multipart .zip → {ok, uploaded_as, bots, sops}
```
Note: `/experience` is defined by the backend but not yet surfaced in the UI — a natural future addition (a timeline/incident feed).

## Naming note
Renamed **"Impact Map" → "Blast Radius"** (what an architect actually asks: "what's the blast radius of this change?") and **"Studio Preview" → "Studio"** with a "soon" badge. Endpoint names unchanged.

## Assets
- **Fonts**: Geist + Geist Mono via Google Fonts (`fonts.googleapis.com`). Swap for locally-hosted if the codebase self-hosts fonts.
- **Icons & node glyphs**: all inline SVG defined in the file (`svgIcon`, `appIconURI`, `botIconURI`). No external icon library, no image files.
- **Libraries (CDN in the prototype)**: Tailwind, Alpine.js 3.13.5 + `@alpinejs/focus`, cytoscape 3.28.1, marked. Replace CDNs with the codebase's bundler/package equivalents.

## Files
- `index.html` — the complete prototype (all five tabs, Alpine state, all fetch calls, cytoscape graph, upload modal, and offline mocks). ~1000 lines; the `MOCK` object and `apiGet` fallback are the only parts intended to be dropped in production.
