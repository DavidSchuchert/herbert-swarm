---
name: herbert-swarm
description: Herbert Swarm 2.0 — Intelligent Multi-Agent Orchestration mit Shared Brain, Planner und Coordinator. Startet echte parallele Hermes-Agents (AIAgent/MiniMax) die phasenweise ein Full-Stack-Projekt bauen.
triggers: [herbert swarm, swarm 2.0, intelligent swarm, shared brain, planner, coordinator, multi-agent mit gedächtnis, swarm starten, projekt automatisiert bauen, parallele agents, hermes swarm]
version: 2.1
category: agent-orchestration
install: git clone https://github.com/DavidSchuchert/herbert-swarm ~/.hermes/skills/herbert-swarm
---

# Herbert Swarm 2.0 — Intelligent Swarm Orchestration

## Overview

Herbert Swarm 2.0 ist ein intelligentes Multi-Agent-System mit **Shared Brain**, **Planner** und **Coordinator**.

**Was es anders macht als v1:**
- **Shared Brain**: Alle Agents teilen sich Wissen (Facts, Files, Findings)
- **Intelligenter Planner**: Analysiert SPEC.md, erstellt Dependency-Graph
- **Coordinator**: Orchestriert mit Dependency-Awareness, nicht blind parallel
- **Jeder Agent liest + schreibt ins Brain**: Wissen bleibt erhalten
- **Phase-Tracking**: Coordinator weiß welche Phase läuft

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  COORDINATOR                                                  │
│  - Welche Phase läuft?                                        │
│  - Welche Tasks sind ready (Deps erfüllt)?                    │
│  - Wer macht was wann?                                        │
└──────────────────────────────────────────────────────────────┘
                              ↑
                              │
┌──────────────────────────────────────────────────────────────┐
│  SHARED BRAIN (brain.json auf Disk)                          │
│  - Facts: {key: value, source_agent, timestamp, tags}       │
│  - Files: {path: {agent, size, verified}}                     │
│  - Tasks: {id: {status, deps, phase, assigned}}              │
│  - Agents: {id: {role, status, capabilities}}                │
└──────────────────────────────────────────────────────────────┘
                              ↑
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │ Agent 1 │          │ Agent 2 │          │ Agent 3 │
   │ (PLANNER)│          │ (CODER) │          │(REVIEWER)│
   │ Reads:    │   ←──   │Reads:   │   ←──   │Reads:    │
   │  Brain    │   Wissen│  Brain  │   Wissen│  Brain   │
   │ Writes:   │  ──→   │Writes:  │   ──→   │Writes:   │
   │ Plans,    │         │ Code,   │         │ Reviews, │
   │ Analysis │         │ Files   │         │ Facts   │
   └──────────┘          └─────────┘          └─────────┘
```

## Key Concepts

### Shared Brain
```python
# Jeder Agent kann:
brain.add_fact("api_endpoints", ["GET /roms", "POST /roms"], "agent-001")
brain.get_fact("api_endpoints")  # → ["GET /roms", "POST /roms"]
brain.query_facts(tag="design")   # Alle Facts mit Tag "design"
```

### Task Dependencies
```python
task = Task(
    id="backend-api-1",
    description="Create FastAPI endpoints",
    files=["backend/api/roms.py"],
    dependencies=["backend-core-1", "infra-1"],  # Wartet auf diese
    phase=3
)
```

### Phase-Based Execution
```python
# Coordinator weiß:
# - Phase 1 (INFRA): keine Deps → parallel
# - Phase 2 (CORE): depends on INFRA → sequentiell inner phase
# - Phase 3 (API): depends on CORE → nach CORE
# usw.
```

## Installation

```bash
hermes skill install https://github.com/DavidSchuchert/herbert-swarm
# oder manuell:
git clone https://github.com/DavidSchuchert/herbert-swarm ~/.hermes/skills/herbert-swarm
```

## CLI Usage

```bash
SKILL=~/.hermes/skills/herbert-swarm/scripts/swarm_cli.py

# 1. Swarm initialisieren
python3 $SKILL init --project ~/Documents/EasyROM --name EasyROM

# 2. SPEC.md analysieren und Plan erstellen
python3 $SKILL plan --project ~/Documents/EasyROM

# 3. Brain anzeigen (was wurde geplant)
python3 $SKILL brain --show

# 4. Erst Dry-Run (kein API-Call)
python3 $SKILL run --project ~/Documents/EasyROM --dry-run

# 5. Echte Ausführung (3 parallele Hermes-Agents)
python3 $SKILL run --project ~/Documents/EasyROM --parallel 3

# 6. Status checken
python3 $SKILL status

# 7. Reset (wenn was schief geht)
python3 $SKILL reset
```

## Wie Agents gespawnt werden

Jeder Task wird als eigener `AIAgent` aus dem Hermes-Core gestartet:

```python
from run_agent import AIAgent  # aus ~/.hermes/hermes-agent/

agent = AIAgent(
    base_url="https://api.minimax.io/anthropic",  # aus ~/.hermes/config.yaml
    api_key="sk-cp-...",                           # aus ~/.hermes/auth.json
    model="MiniMax-M2.7",
    enabled_toolsets=["terminal", "file"],
)
result = agent.run_conversation(task_prompt, task_id=tid)
```

API-Key und Base-URL werden automatisch aus `~/.hermes/auth.json` geladen — keine manuelle Konfiguration nötig.

## Programmatic Usage

```python
from swarm_brain import HerbertSwarm, SwarmBrain, SwarmPlanner, SwarmCoordinator

# Init
swarm = HerbertSwarm("EasyROM", "/path/to/project")

# Initialize with SPEC
swarm.initialize(spec_content)

# Run
result = swarm.run()

# Report
swarm.print_report()

# Direct Brain access
brain = swarm.get_brain()
facts = brain.query_facts(tag="analysis")
```

## Agent Prompt Template

Jeder Agent bekommt diesen Prompt (automatisch generiert von `swarm_cli.py`):

```
You are a coder agent in the Herbert Swarm.
Working directory: /Users/davidwork/Documents/EasyROM

PROJECT SPEC (summary):
# EasyROM — FastAPI Backend, React Frontend ...

TASK: Create FastAPI endpoints (ROMs CRUD, Platforms, Scrape)

Files to create/modify:
  - backend/api/roms.py
  - backend/api/platforms.py
  - backend/main.py

Implement the task completely. Create all listed files with production-ready code.
Use best practices for the detected stack. Do not leave TODOs or placeholders.
```

Der Agent hat Zugriff auf `terminal` und `file` Toolsets — er kann Dateien schreiben und Shell-Befehle ausführen.

## Brain File Structure

Brain wird persistent gespeichert in `~/.local/share/herbert-swarm/brain.json` (überlebt Reboots).

```json
{
  "project_name": "EasyROM",
  "project_path": "/path/to/project",
  "spec_summary": "...",
  "facts": {
    "api_endpoints": {
      "key": "api_endpoints",
      "value": ["GET /roms", "POST /roms"],
      "source_agent": "agent-001",
      "timestamp": "2026-05-03T...",
      "tags": ["api", "backend"]
    }
  },
  "files": {
    "backend/api/roms.py": {
      "path": "backend/api/roms.py",
      "agent": "agent-001",
      "size": 4500,
      "lines": 150,
      "status": "created",
      "verified": true
    }
  },
  "tasks": {
    "task-001": {
      "id": "task-001",
      "description": "Create FastAPI endpoints",
      "agent_role": "coder",
      "files": ["backend/api/roms.py"],
      "dependencies": [],
      "status": "done",
      "phase": 3,
      "assigned_to": "agent-001"
    }
  },
  "phases": ["INFRA", "BACKEND_CORE", "BACKEND_API", "FRONTEND", "TESTING"],
  "current_phase": 3
}
```

## Phase Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: INFRA                                              │
│ - Tasks: package.json, Dockerfile, docker-compose          │
│ - Dependencies: NONE → alle parallel                        │
│ - Agents: 1-3 Coder Agents                                  │
│ - Output: Config files created                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: BACKEND_CORE                                        │
│ - Tasks: database.py, models, scraper, hasher               │
│ - Dependencies: PHASE 1 done                                │
│ - Parallel: innerhalb phase, aber nach INFRA                │
│ - Output: Core backend modules                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: BACKEND_API                                         │
│ - Tasks: api/roms.py, api/platforms.py, main.py            │
│ - Dependencies: BACKEND_CORE done                           │
│ - Output: FastAPI app mit allen Endpoints                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: FRONTEND                                            │
│ - Tasks: Pages, Components, Hooks                           │
│ - Dependencies: PHASE 1 (für configs)                       │
│ - Output: React App fertig                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: TESTING                                             │
│ - Tasks: pytest tests, Docker integration                    │
│ - Dependencies: Alle vorherigen                              │
│ - Output: Test suite, Docker ready                          │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

1. **Brain first**: Jeder Agent liest Brain BEVOR er anfängt
2. **Facts teilen**: Was ein Agent lernt, wissen alle
3. **Dependencies respektieren**: Coordinator lässt nichts parallel laufen was Deps verletzt
4. **Phase-weise**: Frühe Phasen ermöglichen spätere
5. **Verification**: Agent markiert seine Files als "verified"

## Files

- `scripts/swarm_cli.py` — Haupt-CLI (init, plan, run, brain, status, reset)
- `swarm_brain.py` — Core Brain, Planner, Coordinator Klassen
- `SKILL.md` — Dieses Dokument (Hermes Skill-Manifest)
- `SPEC.md` — Architektur-Dokumentation
- `QUICKSTART.md` — Kurzanleitung
- `README.md` — GitHub README

## Repository

https://github.com/DavidSchuchert/herbert-swarm

## Changelog

- **v2.1**: AIAgent-Integration (echte Hermes-Agents statt Placeholders)
  - `_run_task` nutzt `AIAgent` aus `~/.hermes/hermes-agent/run_agent.py`
  - API-Key automatisch aus `~/.hermes/auth.json` geladen
  - `--dry-run` Flag für Tests ohne API-Calls
  - Brain persistiert in `~/.local/share/herbert-swarm/` statt `/tmp/`
  - `List`/`Dict` Import-Bug gefixt
  - Echter Threading für parallele Task-Ausführung

- **v2.0**: Komplett-Rewrite mit Shared Brain, Planner, Coordinator
  - Brain als Shared Memory zwischen allen Agents
  - Intelligente Dependency-Auflösung
  - Phase-Tracking im Coordinator
  - Fact-Sharing zwischen Agents
