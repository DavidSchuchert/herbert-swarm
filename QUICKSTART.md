# Herbert Swarm — Quickstart

## TL;DR

```bash
# Setup (einmalig)
mkdir -p ~/Documents/HerbertSwarm
cp -r ~/.hermes/skills/swarm-orchestration/herbert-swarm/scripts/* ~/Documents/HerbertSwarm/

# Projekt bauen
cd ~/Documents/HerbertSwarm
python3 swarm_master.py init --project ~/Documents/MeinProjekt --agents 15
python3 run_swarm.py --project ~/Documents/MeinProjekt --agents 15 --parallel 3
python3 swarm_master.py report
```

## Was ist das?

Herbert Swarm ist ein Multi-Agent-Orchestrierungssystem. Es lässt 15 MiniMax Agents parallel arbeiten, die gemeinsam ein full-stack App bauen — in ~5-10 Minuten.

## Voraussetzungen

- Python 3.10+
- MiniMax/Herbert (läuft already)
- Keine额外 Installation nötig

## Projekt-Struktur

```
~/Documents/HerbertSwarm/
├── swarm_master.py    # CLI: init, status, report
├── execute_swarm.py   # Batch-Executor
├── run_swarm.py       # Phase-Orchestrator
└── SPEC.md           # Doku

~/Documents/MeinProjekt/   # Dein Projekt
├── backend/
├── frontend/
├── configs/
└── tests/
```

## Workflow

1. **SPEC.md erstellen** im Projekt (was soll gebaut werden)
2. **Swarm init** — erstellt tasks.json
3. **Swarm run** — startet 15 Agents in 5 Phasen
4. **Report** — zeigt was erstellt wurde

## Troubleshooting

- **Agent in falsches Verzeichnis geschrieben?** → Immer absolute Paths im Prompt
- **Rate-Limit?** → `--parallel 3` statt 5
- **Dependencies nicht erfüllt?** → Phase-Reihenfolge prüfen

## Eigenes Projekt

Um ein eigenes Projekt zu bauen:

1. SPEC.md im Projektverzeichnis erstellen
2. Init: `python3 swarm_master.py init --project /path/to/project --agents 15`
3. Run: `python3 run_swarm.py --project /path/to/project --agents 15 --parallel 3`

Die Agents folgen den Tasks in `tasks.json` — einfach anpassbar.
