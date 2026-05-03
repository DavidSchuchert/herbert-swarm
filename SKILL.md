---
name: herbert-swarm
description: Herbert Swarm 2.0 — Intelligent Multi-Agent Orchestration mit Shared Brain, Planner und Coordinator. Nutze delegate_task für echte parallele Agents.
triggers: [herbert swarm, swarm 2.0, intelligent swarm, shared brain, planner, coordinator, multi-agent mit gedächtnis]
version: 2.0
category: agent-orchestration
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

## CLI Usage

```bash
cd ~/Documents/HerbertSwarm

# 1. Swarm initialisieren
python3 swarm_cli.py init --project ~/Documents/EasyROM --name EasyROM

# 2. SPEC.md analysieren und Plan erstellen
python3 swarm_cli.py plan --project ~/Documents/EasyROM

# 3. Brain anzeigen (was wurde geplant)
python3 swarm_cli.py brain --show

# 4. Swarm ausführen (intelligent, phase für phase)
python3 swarm_cli.py run --project ~/Documents/EasyROM --parallel 3

# 5. Status checken
python3 swarm_cli.py status

# 6. Reset (wenn was schief geht)
python3 swarm_cli.py reset
```

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

Wenn du einen Agent via delegate_task spawnst, gibt ihm Zugriff aufs Brain:

```python
delegate_task(
    tasks=[{
        "goal": f"""You are Agent-001 (CODER) for project EasyROM.

## YOUR TASK
Create the FastAPI ROM endpoints.

## READ FROM BRAIN
- Check /tmp/herbert-swarm/brain.json for:
  - What files already exist
  - What tasks are complete
  - What design decisions were made

## YOUR FILES
- backend/api/roms.py

## WRITE TO BRAIN
When done, write your findings:
- Files you created
- Design decisions made
- API contract you established
- Any issues encountered

## LOG FORMAT
[BRAIN] Sharing knowledge: <what you learned>
[AGENT-001] Created: <file>
[STATUS] Complete: <task-id>
""",
        "context": "Project: /Users/davidwork/Documents/EasyROM\nBrain file: /tmp/herbert-swarm/brain.json",
        "role": "leaf",
        "toolsets": ["terminal", "file"]
    }]
)
```

## Brain File Structure

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

- `swarm_brain.py` — Core Brain, Planner, Coordinator Klassen
- `swarm_cli.py` — CLI Interface
- `swarm_master.py` — Legacy v1 Master (kompatibel)
- `run_swarm.py` — Legacy v1 Executor (kompatibel)
- `SPEC.md` — Architektur-Doku

## Repository

https://github.com/DavidSchuchert/herbert-swarm

## Changelog

- **v2.0**: Komplett-Rewrite mit Shared Brain, Planner, Coordinator
  - Brain als Shared Memory zwischen allen Agents
  - Intelligente Dependency-Auflösung
  - Phase-Tracking im Coordinator
  - Fact-Sharing zwischen Agents
