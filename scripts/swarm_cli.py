#!/usr/bin/env python3
"""
Herbert Swarm 2.0 — Intelligent Swarm CLI

Usage:
    python3 swarm_cli.py init --project <path> --name <name>
    python3 swarm_cli.py plan --project <path>     # Analyze SPEC and create plan
    python3 swarm_cli.py run --project <path>      # Execute with intelligent coordination
    python3 swarm_cli.py brain --show              # Show current brain state
    python3 swarm_cli.py status                   # Show task status
    python3 swarm_cli.py reset                    # Reset brain/state
"""

from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

# Constants — use ~/.local/share so brain survives reboot
SWARM_HOME = Path.home() / ".local" / "share" / "herbert-swarm"
BRAIN_FILE = SWARM_HOME / "brain.json"
STATE_FILE = SWARM_HOME / "state.json"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log(msg: str, color: str = "") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{RESET}", flush=True)


def _load_brain() -> dict:
    if not BRAIN_FILE.exists():
        log("ERROR: No swarm initialized. Run 'init' first.", RED)
        sys.exit(1)
    try:
        return json.loads(BRAIN_FILE.read_text())
    except json.JSONDecodeError as e:
        log(f"ERROR: brain.json corrupt: {e}", RED)
        sys.exit(1)


def _save_brain(brain: dict) -> None:
    SWARM_HOME.mkdir(parents=True, exist_ok=True)
    BRAIN_FILE.write_text(json.dumps(brain, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def cmd_init(args) -> None:
    project_path = Path(args.project).resolve()
    project_name = args.name or project_path.name

    log(f"{BOLD}Initializing Herbert Swarm 2.0 for '{project_name}'...{RESET}", BLUE)

    project_path.mkdir(parents=True, exist_ok=True)

    brain: dict = {
        "project_name": project_name,
        "project_path": str(project_path),
        "spec_summary": "",
        "facts": {},
        "files": {},
        "tasks": {},
        "phases": [],
        "created_at": datetime.now().isoformat(),
        "current_phase": 0,
    }

    _save_brain(brain)
    log(f"Swarm brain saved to {BRAIN_FILE}", GREEN)
    log(f"Project: {project_name} ({project_path})", CYAN)


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------

def cmd_plan(args) -> None:
    project_path = Path(args.project).resolve()
    brain = _load_brain()

    spec_path = project_path / "SPEC.md"
    if not spec_path.exists():
        log(f"WARNING: No SPEC.md found at {spec_path}", YELLOW)
        spec_content = ""
    else:
        spec_content = spec_path.read_text(encoding="utf-8")
        brain["spec_summary"] = spec_content[:2000]

    tasks = _analyze_and_plan(spec_content, project_path)

    brain["tasks"] = tasks
    if not brain.get("phases"):
        brain["phases"] = ["INFRA", "BACKEND_CORE", "BACKEND_API", "FRONTEND", "TESTING"]

    _save_brain(brain)

    log(f"Plan created: {len(tasks)} tasks", GREEN)
    for phase_num, phase_name in enumerate(brain["phases"], 1):
        phase_tasks = [t for t in tasks.values() if t["phase"] == phase_num]
        log(f"  Phase {phase_num}: {phase_name} ({len(phase_tasks)} tasks)")


def _analyze_and_plan(spec_content: str, project_path: Path) -> dict:
    """Analyze SPEC.md and create intelligent task plan."""
    lower = spec_content.lower()

    has_backend  = any(k in lower for k in ["fastapi", "backend", "python", "api"])
    has_frontend = any(k in lower for k in ["react", "frontend", "vite", "typescript", "tailwind"])
    has_docker   = any(k in lower for k in ["docker", "container"])
    has_tests    = any(k in lower for k in ["test", "pytest", "unittest"])

    tasks: dict = {}
    task_id = 1

    def make_task(desc: str, role: str, files: list[str], deps: list[str], phase: int, priority: int) -> dict:
        return {
            "id": f"task-{task_id:03d}",
            "description": desc,
            "agent_role": role,
            "files": files,
            "dependencies": deps,
            "status": "pending",
            "priority": priority,
            "phase": phase,
            "created_by": "planner",
        }

    # Phase 1: Infrastructure
    infra_files: list[str] = []
    if has_docker:
        infra_files += [
            "docker/docker-compose.yml",
            "docker/docker-compose.dev.yml",
            "docker/backend/Dockerfile",
            "docker/frontend/Dockerfile",
            "docker/.env.example",
        ]
    if has_backend:
        infra_files += ["backend/requirements.txt", "backend/config.py"]
    if has_frontend:
        infra_files += ["frontend/package.json", "frontend/vite.config.ts", "frontend/tailwind.config.js"]

    infra_id = None
    if infra_files:
        infra_id = f"task-{task_id:03d}"
        tasks[infra_id] = make_task("Create infrastructure and configuration files", "coder", infra_files, [], 1, 1)
        task_id += 1

    # Phase 2: Backend Core
    db_id = None
    if has_backend:
        db_id = f"task-{task_id:03d}"
        tasks[db_id] = make_task(
            "Create database models and connection layer (SQLAlchemy async)",
            "coder",
            ["backend/core/database.py", "backend/models/rom.py"],
            [infra_id] if infra_id else [],
            2, 2,
        )
        task_id += 1

        tasks[f"task-{task_id:03d}"] = make_task(
            "Create scraper (ScreenScraper API) and file hasher (SHA1)",
            "coder",
            ["backend/core/scraper.py", "backend/core/hasher.py"],
            [infra_id] if infra_id else [],
            2, 2,
        )
        task_id += 1

    # Phase 3: Backend API
    api_id = None
    if has_backend:
        api_id = f"task-{task_id:03d}"
        tasks[api_id] = make_task(
            "Create FastAPI endpoints (ROMs CRUD, Platforms, Scrape)",
            "coder",
            ["backend/api/roms.py", "backend/api/platforms.py", "backend/api/scrape.py", "backend/main.py"],
            [db_id] if db_id else [],
            3, 3,
        )
        task_id += 1

    # Phase 4: Frontend
    if has_frontend:
        tasks[f"task-{task_id:03d}"] = make_task(
            "Create React pages (Dashboard, Library with grid view)",
            "coder",
            ["frontend/src/pages/Dashboard.tsx", "frontend/src/pages/Library.tsx"],
            [infra_id] if infra_id else [],
            4, 4,
        )
        task_id += 1

        tasks[f"task-{task_id:03d}"] = make_task(
            "Create React components (ROMCard, FilterSidebar, UploadZone)",
            "coder",
            ["frontend/src/components/ROMCard.tsx", "frontend/src/components/FilterSidebar.tsx", "frontend/src/components/UploadZone.tsx"],
            [infra_id] if infra_id else [],
            4, 4,
        )
        task_id += 1

    # Phase 5: Testing
    if has_tests:
        tasks[f"task-{task_id:03d}"] = make_task(
            "Create pytest tests for API and scraper",
            "reviewer",
            ["tests/test_api.py", "tests/test_scraper.py", "tests/conftest.py"],
            [api_id] if api_id else [],
            5, 5,
        )

    return tasks


# ---------------------------------------------------------------------------
# run  — actually delegates to claude CLI
# ---------------------------------------------------------------------------

def _build_agent_prompt(task: dict, brain: dict) -> str:
    """Build the prompt sent to the claude agent for a task."""
    project_path = brain.get("project_path", ".")
    spec_summary = brain.get("spec_summary", "")
    files = "\n".join(f"  - {f}" for f in task["files"])

    context = ""
    if spec_summary:
        context = f"\nPROJECT SPEC (summary):\n{spec_summary[:800]}\n"

    return (
        f"You are a {task['agent_role']} agent in the Herbert Swarm.\n"
        f"Working directory: {project_path}\n"
        f"{context}\n"
        f"TASK: {task['description']}\n\n"
        f"Files to create/modify:\n{files}\n\n"
        f"Implement the task completely. Create all listed files with production-ready code.\n"
        f"Use best practices for the detected stack. Do not leave TODOs or placeholders."
    )


def _load_hermes_config() -> dict:
    """Load MiniMax API key and base_url from hermes auth.json + config.yaml."""
    import yaml

    hermes_home = Path.home() / ".hermes"
    config: dict = {"base_url": "https://api.minimax.io/anthropic", "api_key": None, "model": "MiniMax-M2.7"}

    cfg_file = hermes_home / "config.yaml"
    if cfg_file.exists():
        try:
            cfg = yaml.safe_load(cfg_file.read_text()) or {}
            model_cfg = cfg.get("model", {})
            if model_cfg.get("base_url"):
                config["base_url"] = model_cfg["base_url"]
            if model_cfg.get("default"):
                config["model"] = model_cfg["default"]
        except Exception:
            pass

    auth_file = hermes_home / "auth.json"
    if auth_file.exists():
        try:
            auth = json.loads(auth_file.read_text())
            pool = auth.get("credential_pool", {})
            for provider in ("minimax", "openrouter"):
                creds = pool.get(provider, [])
                if creds and creds[0].get("access_token"):
                    config["api_key"] = creds[0]["access_token"]
                    if creds[0].get("base_url"):
                        config["base_url"] = creds[0]["base_url"]
                    break
        except Exception:
            pass

    # Env var fallback
    config["api_key"] = config["api_key"] or os.environ.get("MINIMAX_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    return config


def _run_task(tid: str, task: dict, brain: dict, results: dict, lock: threading.Lock) -> None:
    """Execute a single task via Hermes AIAgent (MiniMax)."""
    import sys

    prompt = _build_agent_prompt(task, brain)
    hermes_agent_dir = Path.home() / ".hermes" / "hermes-agent"

    # Add hermes-agent to path so we can import AIAgent
    if str(hermes_agent_dir) not in sys.path:
        sys.path.insert(0, str(hermes_agent_dir))

    try:
        from run_agent import AIAgent  # type: ignore

        cfg = _load_hermes_config()
        if not cfg["api_key"]:
            raise RuntimeError("No API key found in ~/.hermes/auth.json or env vars")

        agent = AIAgent(
            base_url=cfg["base_url"],
            api_key=cfg["api_key"],
            model=cfg["model"],
            enabled_toolsets=["terminal", "file"],
        )

        result = agent.run_conversation(
            user_message=prompt,
            task_id=tid,
        )
        output = result.get("response", "") or ""
        success = True

    except Exception as e:
        success = False
        output = str(e)

    with lock:
        results[tid] = {"success": success, "output": output[:500]}
        log(
            f"  {'✓' if success else '✗'} {tid}: {task['description'][:50]}",
            GREEN if success else RED,
        )
        if not success:
            log(f"    Error: {output[:200]}", RED)


def cmd_run(args) -> None:
    brain = _load_brain()

    if not brain.get("tasks"):
        log("ERROR: No plan. Run 'plan' first.", RED)
        sys.exit(1)

    max_parallel = getattr(args, "parallel", 3)
    dry_run = getattr(args, "dry_run", False)

    log(f"{BOLD}========== HERBERT SWARM 2.0 EXECUTION =========={RESET}", BLUE)
    log(f"Project: {brain['project_name']}", CYAN)
    log(f"Tasks:   {len(brain['tasks'])}", CYAN)
    log(f"Phases:  {', '.join(brain.get('phases', []))}", CYAN)
    if dry_run:
        log("DRY RUN — no agents will be called", YELLOW)

    for phase_num, phase_name in enumerate(brain.get("phases", []), 1):
        phase_tasks = [
            (tid, t)
            for tid, t in brain["tasks"].items()
            if t["phase"] == phase_num and t["status"] == "pending"
        ]

        if not phase_tasks:
            continue

        log(f"\n{BOLD}----- PHASE {phase_num}: {phase_name} -----{RESET}", BLUE)
        log(f"  {len(phase_tasks)} pending tasks, {max_parallel} parallel")

        # Execute in parallel batches
        for i in range(0, len(phase_tasks), max_parallel):
            batch = phase_tasks[i : i + max_parallel]
            log(f"  Batch {i // max_parallel + 1}: {[t[0] for t in batch]}", CYAN)

            # Mark as running
            for tid, task in batch:
                task["status"] = "running"
                task["started_at"] = datetime.now().isoformat()
            _save_brain(brain)

            if dry_run:
                for tid, task in batch:
                    task["status"] = "done"
                    task["completed_at"] = datetime.now().isoformat()
                    log(f"  [DRY] ✓ {tid}: {task['description'][:50]}", YELLOW)
            else:
                results: dict = {}
                lock = threading.Lock()
                threads = []

                for tid, task in batch:
                    t = threading.Thread(
                        target=_run_task,
                        args=(tid, task, brain, results, lock),
                        daemon=True,
                    )
                    threads.append((tid, t))
                    t.start()

                for tid, t in threads:
                    t.join()

                # Update statuses from results
                for tid, task in batch:
                    r = results.get(tid, {})
                    task["status"] = "done" if r.get("success") else "failed"
                    task["completed_at"] = datetime.now().isoformat()

            _save_brain(brain)

        brain["current_phase"] = phase_num
        _save_brain(brain)

    done   = sum(1 for t in brain["tasks"].values() if t["status"] == "done")
    failed = sum(1 for t in brain["tasks"].values() if t["status"] == "failed")
    total  = len(brain["tasks"])
    log(f"\n{BOLD}COMPLETE: {done}/{total} done, {failed} failed{RESET}", GREEN if not failed else YELLOW)


# ---------------------------------------------------------------------------
# brain / status / reset
# ---------------------------------------------------------------------------

def cmd_brain(args) -> None:
    brain = _load_brain()

    print(f"\n{BOLD}{CYAN}===== SWARM BRAIN ====={RESET}")
    print(f"Project:       {brain.get('project_name', 'N/A')}")
    print(f"Path:          {brain.get('project_path', 'N/A')}")
    print(f"Created:       {brain.get('created_at', 'N/A')}")
    print(f"Current Phase: {brain.get('current_phase', 0)}")

    print(f"\n{BOLD}Phases:{RESET}")
    for i, p in enumerate(brain.get("phases", []), 1):
        print(f"  {i}. {p}")

    facts = brain.get("facts", {})
    print(f"\n{BOLD}Facts ({len(facts)}):{RESET}")
    for key, fact in facts.items():
        val = str(fact.get("value", ""))[:60] if isinstance(fact, dict) else str(fact)[:60]
        src = fact.get("source_agent", "?") if isinstance(fact, dict) else "?"
        print(f"  [{src}] {key}: {val}")

    tasks = brain.get("tasks", {})
    print(f"\n{BOLD}Tasks ({len(tasks)}):{RESET}")
    icons = {"pending": "○", "running": "◐", "done": "●", "failed": "✗"}
    for tid, task in tasks.items():
        icon = icons.get(task["status"], "?")
        print(f"  {icon} {tid} [Phase {task['phase']}] {task['description'][:55]}")

    files = brain.get("files", {})
    if files:
        print(f"\n{BOLD}Files ({len(files)}):{RESET}")
        for path in files:
            print(f"  - {path}")


def cmd_status(args) -> None:
    brain = _load_brain()
    tasks = brain.get("tasks", {})

    if not tasks:
        log("No tasks planned yet.", YELLOW)
        return

    by_status: dict[str, list] = {}
    for tid, task in tasks.items():
        by_status.setdefault(task["status"], []).append(task)

    print(f"\n{BOLD}STATUS SUMMARY{RESET}")
    print(f"Total: {len(tasks)}")
    for status, task_list in sorted(by_status.items()):
        icon = {"pending": "○", "running": "◐", "done": "●", "failed": "✗"}.get(status, "?")
        print(f"  {icon} {status}: {len(task_list)}")

    print(f"\n{BOLD}BY PHASE:{RESET}")
    for phase_num, phase_name in enumerate(brain.get("phases", []), 1):
        phase_tasks = [t for t in tasks.values() if t["phase"] == phase_num]
        done   = sum(1 for t in phase_tasks if t["status"] == "done")
        failed = sum(1 for t in phase_tasks if t["status"] == "failed")
        bar = "●" * done + "✗" * failed + "○" * (len(phase_tasks) - done - failed)
        print(f"  Phase {phase_num} {phase_name:15s}: [{bar}] {done}/{len(phase_tasks)}")


def cmd_reset(args) -> None:
    import shutil

    if SWARM_HOME.exists():
        shutil.rmtree(SWARM_HOME)
        SWARM_HOME.mkdir(parents=True)
    log("Brain and state reset", YELLOW)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Herbert Swarm 2.0 CLI")
    subs = parser.add_subparsers()

    p = subs.add_parser("init", help="Initialize swarm for project")
    p.add_argument("--project", required=True)
    p.add_argument("--name")
    p.set_defaults(func=cmd_init)

    p = subs.add_parser("plan", help="Analyze SPEC and create plan")
    p.add_argument("--project", required=True)
    p.set_defaults(func=cmd_plan)

    p = subs.add_parser("run", help="Execute swarm")
    p.add_argument("--project", required=True)
    p.add_argument("--parallel", type=int, default=3)
    p.add_argument("--dry-run", action="store_true", dest="dry_run", help="Plan only, no agents")
    p.set_defaults(func=cmd_run)

    p = subs.add_parser("brain", help="Show brain state")
    p.add_argument("--show", action="store_true")
    p.set_defaults(func=cmd_brain)

    p = subs.add_parser("status", help="Show task status")
    p.set_defaults(func=cmd_status)

    p = subs.add_parser("reset", help="Reset brain")
    p.set_defaults(func=cmd_reset)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
