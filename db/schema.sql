-- Automation Cortex — SQLite schema
-- Central knowledge store: automations + capabilities + apps + selectors + components
-- + fragility signals + incidents + fixes + similarity edges.

PRAGMA foreign_keys = ON;

-- Every parsed UiPath project
CREATE TABLE IF NOT EXISTS Automation (
    id TEXT PRIMARY KEY,              -- <project>::<main_workflow>
    project_name TEXT NOT NULL UNIQUE,
    project_root TEXT NOT NULL,
    main_workflow TEXT,
    intent TEXT,                       -- LLM-derived
    modality_signals_json TEXT,        -- JSON blob
    retry_blocks INTEGER DEFAULT 0,
    hitl_nodes INTEGER DEFAULT 0,
    activity_count INTEGER DEFAULT 0,
    genome_json TEXT NOT NULL          -- full Genome JSON for round-trip
);

-- LLM-derived capability tags per automation
CREATE TABLE IF NOT EXISTS Capability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automation_id TEXT NOT NULL REFERENCES Automation(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    UNIQUE(automation_id, tag)
);
CREATE INDEX IF NOT EXISTS idx_capability_tag ON Capability(tag);

-- Applications touched (SAP, Excel, Outlook, Browser, ActiveDirectory, ...)
CREATE TABLE IF NOT EXISTS Application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automation_id TEXT NOT NULL REFERENCES Automation(id) ON DELETE CASCADE,
    app_name TEXT NOT NULL,
    UNIQUE(automation_id, app_name)
);
CREATE INDEX IF NOT EXISTS idx_application_app ON Application(app_name);

-- Every unique selector observed
CREATE TABLE IF NOT EXISTS Selector (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automation_id TEXT NOT NULL REFERENCES Automation(id) ON DELETE CASCADE,
    raw TEXT NOT NULL,
    app_hint TEXT,
    workflow TEXT
);
CREATE INDEX IF NOT EXISTS idx_selector_app ON Selector(app_hint);

-- Reusable components / invoked workflow edges
CREATE TABLE IF NOT EXISTS Component (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automation_id TEXT NOT NULL REFERENCES Automation(id) ON DELETE CASCADE,
    invoked_path TEXT NOT NULL,       -- as written in the XAML
    resolved_project TEXT,             -- resolved cross-project reference, if any
    UNIQUE(automation_id, invoked_path)
);

-- Exception surface
CREATE TABLE IF NOT EXISTS ExceptionCaught (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automation_id TEXT NOT NULL REFERENCES Automation(id) ON DELETE CASCADE,
    exception_type TEXT NOT NULL,
    UNIQUE(automation_id, exception_type)
);

-- Per-automation fragility inputs (computed on ingest)
CREATE TABLE IF NOT EXISTS FragilitySignal (
    automation_id TEXT PRIMARY KEY REFERENCES Automation(id) ON DELETE CASCADE,
    selector_volatility REAL DEFAULT 0,     -- from synthetic run log
    retry_density REAL DEFAULT 0,           -- retries / activity_count
    exception_surface REAL DEFAULT 0,       -- # distinct exception types
    cross_app_coupling REAL DEFAULT 0,      -- # distinct apps touched
    hitl_coverage REAL DEFAULT 0,           -- hitl / activity_count
    score REAL DEFAULT 0,                   -- final weighted score
    computed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_fragility_score ON FragilitySignal(score);

-- People — humans who resolved incidents (Iteration 4)
CREATE TABLE IF NOT EXISTS Person (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    team TEXT
);

-- LLM prompts — reasoning artifacts reused across fixes (Iteration 4)
CREATE TABLE IF NOT EXISTS LLMPrompt (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    when_to_use TEXT,
    prompt_text TEXT,
    model TEXT
);

-- Synthetic run-log-derived incidents (seeded Day 2, extended Iteration 4)
CREATE TABLE IF NOT EXISTS Incident (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automation_id TEXT NOT NULL REFERENCES Automation(id) ON DELETE CASCADE,
    occurred_at TEXT NOT NULL,
    kind TEXT NOT NULL,                -- selector_change | exception | timeout | data_quality
    summary TEXT,
    fix_id INTEGER REFERENCES Fix(id),
    resolved_by TEXT REFERENCES Person(id),
    prompt_id TEXT REFERENCES LLMPrompt(id)
);

-- Fixes learned (which remediation worked for which incident kind)
CREATE TABLE IF NOT EXISTS Fix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_kind TEXT NOT NULL,
    applies_to_app TEXT,               -- SAP, Excel, ...
    remediation TEXT NOT NULL,
    success_count INTEGER DEFAULT 1,
    last_applied TEXT
);

-- Similarity edges between automations (populated Day 3)
CREATE TABLE IF NOT EXISTS Similarity (
    src_id TEXT NOT NULL REFERENCES Automation(id) ON DELETE CASCADE,
    dst_id TEXT NOT NULL REFERENCES Automation(id) ON DELETE CASCADE,
    score REAL NOT NULL,
    method TEXT,                       -- jaccard | embedding
    PRIMARY KEY (src_id, dst_id)
);
CREATE INDEX IF NOT EXISTS idx_similarity_score ON Similarity(score);
