# Herbert Swarm — Multi-Agent Orchestration für MiniMax/Herbert

## Konzept

Herbert Swarm ist ein lightweight Multi-Agent-Orchestrierungssystem das wie ruflo funktioniert, aber MiniMax/Herbert Agents statt Claude Code nutzt.

**Kernidee:** Koordinierte parallel arbeitende MiniMax Agents mit klarer Aufgabenverteilung, die Ergebnisse ins Filesystem schreiben.

## Architektur

```
Herbert Swarm Master (ICH)
├── Task Queue (JSON File)
├── Agent Pool (subagent Prozesse)
│   ├── agent-001: Backend API Dev
│   ├── agent-002: Backend Core Dev
│   ├── agent-003: Frontend Dev
│   ├── ...
│   └── agent-N: Quality/Review
├── Result Collector
└── Status Tracker
```

## Agent Rollen

| Role | Count | Purpose |
|------|-------|---------|
| COORDINATOR | 1 | Orchestriert alle Tasks, verteilt Arbeit |
| BACKEND_API | 3 | FastAPI Endpoints, CRUD, Router |
| BACKEND_CORE | 2 | Database, Scraper, Hasher, Emulator |
| FRONTEND | 4 | React Components, Pages, Hooks |
| INFRA | 2 | Configs, Scripts, Build Setup |
| TESTER | 2 | Unit Tests, Integration Tests |
| REVIEWER | 1 | Code Review, Quality Gate |

**Total: 15 Agents** (skalierbar)

## Workflow

### Phase 1: Init
```bash
# 1. Swarm init
cd ~/Documents/HerbertSwarm
mkdir -p swarm/{tasks,results,logs,agents}

# 2. Task Definition erstellen (SPEC.md lesen, aufgaben aufteilen)
python3 swarm_master.py init --project ~/Documents/EasyROM --agents 15

# 3. Agents spawnen
python3 swarm_master.py spawn --count 15 --role <role>
```

### Phase 2: Execute
```bash
# 4. Alle Agents parallel starten
python3 swarm_master.py execute --all

# 5. Monitor
python3 swarm_master.py status
python3 swarm_master.py watch
```

### Phase 3: Collect
```bash
# 6. Ergebnisse einsammeln
python3 swarm_master.py collect --output ~/Documents/EasyROM
```

## Command Interface

```
swarm_master.py init      — Projekt initialisieren, Tasks erstellen
swarm_master.py spawn      — Agents spawnen (subagent processes)
swarm_master.py execute    — Alle oder einzelne Agents starten
swarm_master.py status     — Status aller Agents
swarm_master.py watch      — Live Output watching
swarm_master.py collect    — Ergebnisse einsammeln
swarm_master.py report     — Final Report generieren
```

## Task Definition Format

tasks.json:
```json
{
  "project": "EasyROM",
  "spec": "/path/to/SPEC.md",
  "tasks": [
    {
      "id": "backend-api-1",
      "role": "BACKEND_API",
      "agent": "agent-001",
      "description": "Create FastAPI endpoints for ROM CRUD",
      "files": ["backend/api/roms.py", "backend/api/platforms.py"],
      "priority": 1,
      "status": "pending",
      "dependencies": []
    }
  ]
}
```

## Agent Output Convention

Jeder Agent schreibt in:
```
swarm/results/{agent-id}/
├── output/        # Erstellte Files
├── logs/          # Activity logs
├── status.json    # Fertig/Fehler/Working
└── summary.md     # Was wurde gemacht
```

## Status Codes

- `pending` — Wartet auf Ausführung
- `running` — Arbeitet gerade
- `done` — Fertig, Erfolg
- `error` — Fehlgeschlagen
- `blocked` — Wartet auf Dependency

## Scalability

- **15 Agents** = Baseline (Full-Stack App)
- **30+ Agents** = Für große Projekte (Enterprise)
- **5 Agents** = Schneller Prototyp

## Integration mit Herbert/MiniMax

Statt Claude Code subprocesses nutzen wir:
1. **subagent via terminal** — jeder Agent ist ein `execute_code` call
2. **parallel terminal calls** — alle Agents gleichzeitig starten
3. **Filesystem** — Ergebnisse über shared filesystem austauschen
4. **JSON Queue** — Tasks/Status via JSON files koordinieren

## Beispiel: EasyROM mit 15 Agents

```
agent-001 (BACKEND_API): backend/api/roms.py
agent-002 (BACKEND_API): backend/api/platforms.py, scrape.py
agent-003 (BACKEND_API): backend/api/emulator.py, settings.py
agent-004 (BACKEND_CORE): backend/core/database.py
agent-005 (BACKEND_CORE): backend/core/scraper.py
agent-006 (BACKEND_CORE): backend/core/hasher.py, emulator.py
agent-007 (FRONTEND): frontend/src/pages/Dashboard.jsx, Library.jsx
agent-008 (FRONTEND): frontend/src/pages/PlatformView.jsx, ROMDetail.jsx
agent-009 (FRONTEND): frontend/src/components/ROMCard.jsx, FilterSidebar.jsx
agent-010 (FRONTEND): frontend/src/components/UploadZone.jsx, SearchBar.jsx
agent-011 (INFRA): frontend/vite.config.ts, tailwind.config.js
agent-012 (INFRA): configs/platforms.json, scripts/generate_rom_data.py
agent-013 (TESTER): backend/tests/test_api.py
agent-014 (TESTER): frontend/tests/
agent-015 (REVIEWER): Code Review, Quality Gate
```

## Priority System

1. FIRST: Infrastructure (configs, package.json, vite.config)
2. SECOND: Backend Core (database, models)
3. THIRD: Backend API (endpoints)
4. FOURTH: Frontend (components, pages)
5. FIFTH: Testing & Review

Dependencies werden automatisch aufgelöst.
