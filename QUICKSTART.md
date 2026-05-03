# Herbert Swarm — Quickstart

## TL;DR

```bash
# Installation (einmalig)
git clone https://github.com/DavidSchuchert/herbert-swarm ~/.hermes/skills/herbert-swarm

# Alias setzen (optional, bequemer)
alias swarm="python3 ~/.hermes/skills/herbert-swarm/scripts/swarm_cli.py"

# Projekt bauen
swarm init  --project ~/Documents/MeinProjekt --name MeinProjekt
swarm plan  --project ~/Documents/MeinProjekt
swarm run   --project ~/Documents/MeinProjekt --parallel 3
swarm status
```

## Was ist das?

Herbert Swarm ist ein Multi-Agent-Orchestrierungssystem für Hermes/MiniMax. Es startet echte Hermes-Agents (`AIAgent` aus dem Hermes-Core) parallel, die gemeinsam ein Full-Stack-Projekt aus einer `SPEC.md` bauen.

**Wie es funktioniert:**
1. `plan` liest deine `SPEC.md` und erstellt einen Task-Plan (Phasen + Dependencies)
2. `run` startet für jeden Task einen echten `AIAgent` mit MiniMax
3. Alle Agents teilen ein **Shared Brain** (`~/.local/share/herbert-swarm/brain.json`)
4. Phasen werden nacheinander ausgeführt, Tasks innerhalb einer Phase parallel

## Voraussetzungen

- Hermes installiert (`~/.hermes/hermes-agent/run_agent.py` vorhanden)
- MiniMax API Key in `~/.hermes/auth.json` (wird automatisch gelesen)
- Python 3.10+

## Workflow

### 1. SPEC.md erstellen

```markdown
# MeinProjekt

FastAPI Backend mit SQLAlchemy async. React + Vite + Tailwind Frontend.
Docker Compose. Pytest Tests.
```

Hermes erkennt automatisch: Backend (FastAPI), Frontend (React), Docker, Tests.

### 2. Init + Plan

```bash
swarm init --project ~/Documents/MeinProjekt
swarm plan --project ~/Documents/MeinProjekt
swarm brain --show   # zeigt was geplant wurde
swarm status         # zeigt Phasen + Task-Status
```

### 3. Dry-Run (testen ohne API-Calls)

```bash
swarm run --project ~/Documents/MeinProjekt --dry-run
```

### 4. Echte Ausführung

```bash
swarm run --project ~/Documents/MeinProjekt --parallel 3
```

`--parallel 3` = max 3 Agents gleichzeitig. Bei Rate-Limits auf 2 reduzieren.

## Projekt-Struktur nach dem Run

```
~/Documents/MeinProjekt/
├── backend/
│   ├── requirements.txt
│   ├── config.py
│   ├── core/database.py
│   ├── core/scraper.py
│   ├── models/
│   └── api/
├── frontend/
│   ├── package.json
│   ├── src/pages/
│   └── src/components/
├── docker/
│   └── docker-compose.yml
└── tests/
```

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| „No API key found" | `export MINIMAX_API_KEY=sk-cp-...` |
| Phase hängt | `swarm reset` dann `plan` + `run` |
| Rate Limit | `--parallel 2` statt 3 |
| Falsches Verzeichnis | `--project` als absoluten Pfad angeben |

## Hermes-Skill direkt aufrufen

In Hermes einfach schreiben:

> „starte herbert swarm für ~/Documents/MeinProjekt"

Hermes erkennt den Skill über die Triggers in `SKILL.md` und führt ihn aus.
