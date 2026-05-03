---
name: herbert-swarm
description: Herbert Swarm — Multi-Agent Orchestration für MiniMax/Herbert. Spawn 15+ parallel Agents die gemeinsam ein full-stack Projekt bauen. Inspired by ruflo but for MiniMax.
triggers: [herbert swarm, multi-agent, 30 agents, viele agenten, parallel build, swarm build]
version: 1.0
author: Herbert/MiniMax
category: agent-orchestration
tags: [multi-agent, parallel, swarm, orchestration, mini-max]
---

# Herbert Swarm — Multi-Agent Orchestration

## Overview

Herbert Swarm ist ein Multi-Agent-Orchestrierungssystem für MiniMax/Herbert. Es spawnt parallele Agents die gemeinsam ein full-stack Projekt bauen — ähnlich wie ruflo, aber für MiniMax statt Claude Code.

**Was es macht:**
- 15+ Agents parallel arbeiten lassen
- Phasen-basiert mit Dependency-Resolution
- Jeder Agent hat klare Aufgabe + Files-to-create
- Ergebnisse landen direkt im Projekt-Filesystem

## Quick Start

```bash
# 1. Swarm Scripts installieren
mkdir -p ~/Documents/HerbertSwarm
# Scripts kommen aus ~/Documents/HerbertSwarm/

# 2. Projekt initialisieren
cd ~/Documents/HerbertSwarm
python3 swarm_master.py init --project ~/Documents/EasyROM --agents 15

# 3. Agents spawnen und ausführen
python3 run_swarm.py --project ~/Documents/EasyROM --agents 15 --parallel 3
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Herbert Swarm Master (ICH / MiniMax)                    │
│  - Task Definition (tasks.json)                          │
│  - Phase Orchestration                                   │
│  - Dependency Resolution                                 │
└─────────────────────────────────────────────────────────┘
        │
        ├── Phase 1: INFRA (3 Agents parallel)
        │   └── Agent-001: Configs, Package.json, vite.config
        │   └── Agent-002: Backend Core (database, models)
        │   └── Agent-003: Backend Scraper (scraper.py, hasher.py)
        │
        ├── Phase 2: BACKEND_API (3 Agents parallel)
        │   └── Agent-004: API Endpoints (roms.py, platforms.py)
        │   └── Agent-005: API (scrape.py, emulator.py, stats.py)
        │   └── Agent-006: API Router + Settings
        │
        ├── Phase 3: FRONTEND (3 Agents parallel)
        │   └── Agent-007: Entry Points (main.tsx, App.tsx, api.ts)
        │   └── Agent-008: Pages (Dashboard, Library)
        │   └── Agent-009: Pages (PlatformView, ROMDetail)
        │
        ├── Phase 4: FRONTEND_COMPONENTS (3 Agents parallel)
        │   └── Agent-010: Components (ROMCard, FilterSidebar)
        │   └── Agent-011: Components (UploadZone, SearchBar, Toast)
        │   └── Agent-012: Hooks (useROMs, usePlatforms, etc.)
        │
        └── Phase 5: TESTING (3 Agents parallel)
            └── Agent-013: Configs + Scripts
            └── Agent-014: Tests (pytest)
            └── Agent-015: Emulator Detection + Init Files
```

## Task Definition Format

Tasks werden in `tasks.json` definiert:

```json
{
  "project": "MyProject",
  "project_path": "/path/to/project",
  "tasks": [
    {
      "id": "backend-api-1",
      "role": "BACKEND_API",
      "agent": "agent-005",
      "description": "Create FastAPI endpoints for ROM CRUD",
      "files": [
        "backend/api/roms.py",
        "backend/api/platforms.py"
      ],
      "priority": 1,
      "status": "pending",
      "dependencies": ["backend-core-1"]
    }
  ]
}
```

## Agent Roles

| Role | Count | Purpose |
|------|-------|---------|
| INFRA | 2 | Configs, package.json, build setup |
| BACKEND_CORE | 2 | Database, models, scraper, hasher |
| BACKEND_API | 3 | API endpoints |
| FRONTEND | 3 | Pages, components, hooks |
| TESTER | 1 | Unit tests, integration tests |

## Dependency System

Tasks mit Dependencies warten bis alle Dependencies `done` sind:
```json
"dependencies": ["backend-core-1", "infra-1"]
```

## CLI Commands

```bash
# Init Swarm + Tasks erstellen
python3 swarm_master.py init --project <path> --agents <count>

# Status aller Tasks anzeigen
python3 swarm_master.py status

# Swarm ausführen ( phases + parallel )
python3 run_swarm.py --project <path> --agents 15 --parallel 3

# Ergebnisse einsammeln
python3 swarm_master.py collect --output <path>

# Final Report
python3 swarm_master.py report
```

## Integration mit MiniMax/Herbert

### delegate_task nutzen (empfohlen)

```python
# Phase 1 parallel starten
delegate_task(
    tasks=[
        {"goal": "Create configs...", "role": "leaf", "toolsets": ["terminal","file"]},
        {"goal": "Create database...", "role": "leaf", "toolsets": ["terminal","file"]},
        {"goal": "Create scraper...", "role": "leaf", "toolsets": ["terminal","file"]},
    ]
)
```

### Wichtig für Agent-Prompts

Jeder Agent braucht:
1. **Exakte Files-Liste** — was er erstellen soll
2. **Projekt-Path** — wohin schreiben
3. **Design System** — Farben, Fonts, etc.
4. **SPEC.md Kontext** — lesen und befolgen
5. **Logging** — [AGENT-N] Created: <filename> pro File

## Troubleshooting

### Agents schreiben in falsches Verzeichnis
→ Agent-Prompt MUSS explizit sagen: `Write files to EXACTLY /path/to/project/`

### Fehlende __init__.py Files
→ Extra Agent für Phase 5 der alle `__init__.py` erstellt

### Batch-Size zu groß
→ `--parallel 3` statt `--parallel 5` bei Rate-Limits

## Workflow für neues Projekt

1. SPEC.md erstellen mit vollständiger Spec
2. `mkdir -p ~/Documents/HerbertSwarm`
3. Scripts in das Verzeichnis kopieren
4. `python3 swarm_master.py init --project /path/to/project --agents 15`
5. `python3 run_swarm.py --project /path/to/project --agents 15 --parallel 3`
6. Ergebnisse prüfen, Fehler manuell fixen
7. `python3 swarm_master.py report`

## Performance

- 15 Agents = ~5-10 min für full-stack App
- Batch-Size 3 = guter Trade-off zwischen Speed und Rate-Limits
- Phasen=5: INFRA → CORE → API → FRONTEND → TESTING

## Deployment / Sharing

Um das System zu teilen:
1. `~/Documents/HerbertSwarm/` als ZIP exportieren
2. Empfänger entpackt in `~/Documents/HerbertSwarm/`
3. Fertig — keine Installation nötig, nur Python 3.10+

## Files

- `swarm_master.py` — CLI für Init, Status, Report
- `execute_swarm.py` — Subprocess-basierter Batch-Executor
- `run_swarm.py` — Phase-based Orchestrator (nutzt delegate_task)
- `SPEC.md` — Diese Doku

## Lizenz / Credits

Herbert Swarm — gebaut für David Schuchert's EasyROM Projekt.
Inspiriert von ruflo, aber für MiniMax/Herbert.
