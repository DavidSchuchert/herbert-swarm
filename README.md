# Herbert Swarm 2.0

Ein intelligentes Multi-Agent-Orchestrierungssystem für Hermes. Lässt mehrere MiniMax-Agents parallel an einem Projekt arbeiten — mit geteiltem Brain, Planer und Coordinator.

## Installation als Hermes-Skill

```bash
hermes skill install https://github.com/DavidSchuchert/herbert-swarm
```

Oder manuell:

```bash
git clone https://github.com/DavidSchuchert/herbert-swarm ~/.hermes/skills/herbert-swarm
```

Danach in Hermes einfach schreiben: **„starte herbert swarm"** oder **„swarm 2.0"** — Hermes erkennt den Skill automatisch.

## Was macht es?

Herbert Swarm liest deine `SPEC.md`, zerlegt das Projekt in Tasks, und lässt mehrere Hermes-Agents (über `AIAgent` aus dem Hermes-Core) parallel daran arbeiten — phasenweise, mit Dependency-Tracking.

```
PHASE 1: INFRA        → Dockerfiles, package.json, configs
PHASE 2: BACKEND CORE → Database, Models, Core-Logik
PHASE 3: BACKEND API  → FastAPI Endpoints
PHASE 4: FRONTEND     → React Components & Pages
PHASE 5: TESTING      → pytest, Integration Tests
```

Alle Agents teilen sich ein **Shared Brain** (`~/.local/share/herbert-swarm/brain.json`) — was Agent 1 baut, weiß Agent 2 sofort.

## Voraussetzungen

- Hermes installiert (`~/.hermes/hermes-agent/run_agent.py` vorhanden)
- MiniMax API Key in `~/.hermes/auth.json` oder `MINIMAX_API_KEY` env var
- Python 3.10+

## Schnellstart

```bash
# 1. Projekt-Verzeichnis anlegen + SPEC.md schreiben
mkdir ~/Documents/MeinProjekt
cat > ~/Documents/MeinProjekt/SPEC.md << 'EOF'
# MeinProjekt
FastAPI Backend mit SQLAlchemy, React Frontend mit Vite und Tailwind.
Docker Compose. Pytest Tests.
EOF

# 2. Swarm initialisieren
python3 ~/.hermes/skills/herbert-swarm/scripts/swarm_cli.py init \
  --project ~/Documents/MeinProjekt --name MeinProjekt

# 3. Plan erstellen (liest SPEC.md, erstellt Tasks)
python3 ~/.hermes/skills/herbert-swarm/scripts/swarm_cli.py plan \
  --project ~/Documents/MeinProjekt

# 4. Plan prüfen
python3 ~/.hermes/skills/herbert-swarm/scripts/swarm_cli.py brain --show
python3 ~/.hermes/skills/herbert-swarm/scripts/swarm_cli.py status

# 5. Agents starten (3 parallel)
python3 ~/.hermes/skills/herbert-swarm/scripts/swarm_cli.py run \
  --project ~/Documents/MeinProjekt --parallel 3

# Erst trocken testen (kein API-Call):
python3 ... run --project ~/Documents/MeinProjekt --dry-run
```

## CLI Referenz

```
swarm_cli.py init   --project <pfad> [--name <name>]   Swarm initialisieren
swarm_cli.py plan   --project <pfad>                    SPEC.md analysieren, Tasks erstellen
swarm_cli.py run    --project <pfad> [--parallel N]     Agents starten
                                     [--dry-run]         Nur Plan anzeigen, keine Agents
swarm_cli.py brain  --show                               Brain-Zustand anzeigen
swarm_cli.py status                                      Task-Status anzeigen
swarm_cli.py reset                                       Brain zurücksetzen
```

## Shared Brain

Alle Agents lesen und schreiben in `~/.local/share/herbert-swarm/brain.json`:

```json
{
  "project_name": "MeinProjekt",
  "facts": { "api_base": { "value": "/api/v1", "source_agent": "task-001" } },
  "files": { "backend/main.py": { "agent": "task-002", "status": "created" } },
  "tasks": { "task-001": { "status": "done", "phase": 1 } },
  "current_phase": 3
}
```

## Dateien

```
scripts/swarm_cli.py   — CLI (init, plan, run, brain, status, reset)
swarm_brain.py         — Brain, Planner, Coordinator Klassen
SKILL.md               — Hermes Skill-Manifest
SPEC.md                — Architektur-Dokumentation
QUICKSTART.md          — Kurzanleitung
```

## Troubleshooting

**„No API key found"** → MiniMax Key in `~/.hermes/auth.json` oder `export MINIMAX_API_KEY=sk-...`

**Agent schreibt in falsches Verzeichnis** → Im Prompt steht `project_path` als absoluter Pfad — prüfe ob `--project` korrekt angegeben

**Rate Limit** → `--parallel 2` statt 3, oder kurz warten

**Phase bleibt hängen** → `swarm_cli.py reset` und nochmal `plan` + `run`
