#!/usr/bin/env python3
"""
Herbert Swarm 2.0 — Intelligent Swarm CLI

Usage:
    python3 swarm_cli.py init   --project <path> [--name <name>]
    python3 swarm_cli.py plan   --project <path> [--spec <file>]
    python3 swarm_cli.py run    --project <path> [--parallel N] [--timeout S] [--dry-run] [--retry-failed]
    python3 swarm_cli.py brain  --show  [--project <path>]
    python3 swarm_cli.py status         [--project <path>]
    python3 swarm_cli.py report         [--project <path>]
    python3 swarm_cli.py reset          [--project <path>] [--yes]
"""

from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Storage — per-project brain files inside the project directory
# ---------------------------------------------------------------------------

SWARM_HOME = Path.home() / ".local" / "share" / "herbert-swarm"
# Legacy global brain (fallback when no --project given)
_LEGACY_BRAIN_FILE = SWARM_HOME / "brain.json"

# Global file-write lock — shared by ALL threads to serialise brain saves
_brain_file_lock = threading.Lock()

# Colors
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def log(msg: str, color: str = "") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{RESET}", flush=True)


# ---------------------------------------------------------------------------
# Brain file helpers
# ---------------------------------------------------------------------------

def _brain_file_for(project_path: str | Path | None) -> Path:
    """Return the brain-file path for a given project (or the legacy global one)."""
    if project_path:
        return Path(project_path).resolve() / ".swarm_brain.json"
    return _LEGACY_BRAIN_FILE


def _load_brain(brain_file: Path) -> dict:
    if not brain_file.exists():
        log(f"ERROR: No swarm brain found at {brain_file}. Run 'init' first.", RED)
        sys.exit(1)
    with _brain_file_lock:
        try:
            return json.loads(brain_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            log(f"ERROR: brain file corrupt: {e}", RED)
            sys.exit(1)


def _save_brain(brain: dict, brain_file: Path) -> None:
    brain_file.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: write to tmp then rename so concurrent readers never see partial JSON
    tmp = brain_file.with_suffix(".json.tmp")
    with _brain_file_lock:
        tmp.write_text(json.dumps(brain, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(brain_file)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def cmd_init(args) -> None:
    project_path = Path(args.project).resolve()
    project_name = args.name or project_path.name
    brain_file   = _brain_file_for(project_path)

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

    _save_brain(brain, brain_file)
    log(f"Swarm brain saved to {brain_file}", GREEN)
    log(f"Project: {project_name} ({project_path})", CYAN)


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------

def cmd_plan(args) -> None:
    project_path = Path(args.project).resolve()
    brain_file   = _brain_file_for(project_path)
    brain        = _load_brain(brain_file)

    # Allow --spec to point at an arbitrary file; fall back to SPEC.md in project
    spec_path = Path(args.spec).resolve() if getattr(args, "spec", None) else project_path / "SPEC.md"
    if not spec_path.exists():
        log(f"WARNING: No spec file found at {spec_path}", YELLOW)
        spec_content = ""
    else:
        spec_content = spec_path.read_text(encoding="utf-8")
        brain["spec_summary"] = spec_content[:2000]

    tasks, phases = _analyze_and_plan(spec_content, project_path)

    brain["tasks"] = tasks
    if not brain.get("phases"):
        brain["phases"] = phases

    _save_brain(brain, brain_file)

    log(f"Plan created: {len(tasks)} tasks", GREEN)
    for phase_num, phase_name in enumerate(brain["phases"], 1):
        phase_tasks = [t for t in tasks.values() if t["phase"] == phase_num]
        log(f"  Phase {phase_num}: {phase_name} ({len(phase_tasks)} tasks)")


def _scan_project_files(project_path: Path) -> set[str]:
    found: set[str] = set()
    try:
        for entry in project_path.rglob("*"):
            if entry.is_file():
                found.add(entry.name.lower())
    except Exception:
        pass
    return found


def _analyze_and_plan(spec_content: str, project_path: Path) -> tuple[dict, list[str]]:
    """Analyze SPEC.md and create an intelligent, dependency-correct task plan."""
    lower = spec_content.lower()

    backend_keywords  = [
        "fastapi", "flask", "django", "starlette", "express", "aiohttp",
        "tornado", "backend", "python", "api", "rest", "graphql", "grpc",
        "server", "endpoint", "routes", "uvicorn", "gunicorn",
    ]
    frontend_keywords = [
        "react", "next.js", "nextjs", "nuxt", "sveltekit", "svelte",
        "vue", "vite", "angular", "astro", "remix", "frontend",
        "typescript", "tailwind", "html", "css", "ui", "web app",
    ]
    database_keywords = [
        "postgresql", "postgres", "mysql", "mariadb", "mongodb", "mongo",
        "redis", "sqlite", "cassandra", "elasticsearch", "database", "db",
        "sqlalchemy", "prisma", "alembic", "migration",
    ]
    docker_keywords = ["docker", "container", "compose", "kubernetes", "k8s", "helm"]
    ci_keywords     = [
        "github actions", "github-actions", "ci", "pytest-cov", "coverage",
        "test", "pytest", "unittest", "jest", "vitest", "cypress",
    ]

    has_backend  = any(k in lower for k in backend_keywords)
    has_frontend = any(k in lower for k in frontend_keywords)
    has_database = any(k in lower for k in database_keywords)
    has_docker   = any(k in lower for k in docker_keywords)
    has_ci       = any(k in lower for k in ci_keywords)

    # Fallback: scan actual project files when SPEC is empty or too short
    if not spec_content.strip() or len(spec_content.strip()) < 80:
        file_names = _scan_project_files(project_path)
        if not has_backend:
            has_backend = bool(file_names & {
                "requirements.txt", "pyproject.toml", "setup.py",
                "main.py", "app.py", "server.py", "manage.py",
            })
        if not has_frontend:
            has_frontend = bool(file_names & {
                "package.json", "vite.config.ts", "vite.config.js",
                "next.config.js", "nuxt.config.ts", "svelte.config.js",
                "tailwind.config.js", "tailwind.config.ts",
            })
        if not has_docker:
            has_docker = bool(file_names & {"dockerfile", "docker-compose.yml", "docker-compose.yaml"})
        if not has_ci:
            has_ci = bool(file_names & {"pytest.ini", "conftest.py"})

    tasks: dict = {}
    task_id = 1

    def make_task(desc: str, role: str, files: list[str], deps: list[str], phase: int, priority: int) -> dict:
        nonlocal task_id
        tid = f"task-{task_id:03d}"
        task_id += 1
        return {
            "id": tid,
            "description": desc,
            "agent_role": role,
            "files": files,
            "dependencies": [d for d in deps if d],  # filter None/empty
            "status": "pending",
            "priority": priority,
            "phase": phase,
            "created_by": "planner",
        }

    # Build dynamic phase list
    phase_names: list[str] = ["INFRA"]
    phase_map: dict[str, int] = {"INFRA": 1}
    next_phase = 2

    if has_database:
        phase_names.append("DATABASE")
        phase_map["DATABASE"] = next_phase
        next_phase += 1
    if has_backend:
        phase_names.append("BACKEND_CORE")
        phase_map["BACKEND_CORE"] = next_phase
        next_phase += 1
        phase_names.append("BACKEND_API")
        phase_map["BACKEND_API"] = next_phase
        next_phase += 1
    if has_frontend:
        phase_names.append("FRONTEND")
        phase_map["FRONTEND"] = next_phase
        next_phase += 1
    if has_ci:
        phase_names.append("TESTING")
        phase_map["TESTING"] = next_phase
        next_phase += 1

    # ---- Phase INFRA ----
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
        infra_files += [
            "frontend/package.json",
            "frontend/vite.config.ts",
            "frontend/tailwind.config.js",
        ]

    infra_id: str | None = None
    if infra_files:
        t = make_task(
            "Create infrastructure and configuration files",
            "coder", infra_files, [], phase_map["INFRA"], 1,
        )
        infra_id = t["id"]
        tasks[infra_id] = t

    # ---- Phase DATABASE (optional) ----
    db_model_id: str | None = None
    if has_database and "DATABASE" in phase_map:
        t = make_task(
            "Create database models and migration scripts",
            "coder",
            ["backend/core/database.py", "backend/models/__init__.py", "alembic/env.py"],
            [infra_id],
            phase_map["DATABASE"], 2,
        )
        db_model_id = t["id"]
        tasks[db_model_id] = t

    # ---- Phase BACKEND_CORE ----
    core_task_ids: list[str] = []
    if has_backend and "BACKEND_CORE" in phase_map:
        core_deps = [infra_id, db_model_id]

        if not has_database:
            t = make_task(
                "Create database connection layer (SQLAlchemy async)",
                "coder",
                ["backend/core/database.py", "backend/models/rom.py"],
                core_deps,
                phase_map["BACKEND_CORE"], 2,
            )
            core_task_ids.append(t["id"])
            tasks[t["id"]] = t
        else:
            t = make_task(
                "Create core services: scraper, hasher, business logic",
                "coder",
                ["backend/core/scraper.py", "backend/core/hasher.py", "backend/services/rom_service.py"],
                core_deps,
                phase_map["BACKEND_CORE"], 2,
            )
            core_task_ids.append(t["id"])
            tasks[t["id"]] = t

        # Scraper + hasher are always useful alongside the core
        t2 = make_task(
            "Create scraper (ScreenScraper API) and file hasher (SHA1)",
            "coder",
            ["backend/core/scraper.py", "backend/core/hasher.py"],
            core_deps,
            phase_map["BACKEND_CORE"], 2,
        )
        core_task_ids.append(t2["id"])
        tasks[t2["id"]] = t2

    # ---- Phase BACKEND_API ----
    api_id: str | None = None
    if has_backend and "BACKEND_API" in phase_map:
        # API waits for ALL BACKEND_CORE tasks (not just the first one)
        t = make_task(
            "Create API endpoints (ROMs CRUD, Platforms, Scrape)",
            "coder",
            ["backend/api/roms.py", "backend/api/platforms.py", "backend/api/scrape.py", "backend/main.py"],
            core_task_ids,  # ← all BACKEND_CORE tasks
            phase_map["BACKEND_API"], 3,
        )
        api_id = t["id"]
        tasks[api_id] = t

    # ---- Phase FRONTEND ----
    fe_task_ids: list[str] = []
    if has_frontend and "FRONTEND" in phase_map:
        # Frontend depends on infra configs AND backend API (so it can mirror endpoints)
        fe_deps = [infra_id, api_id]

        t = make_task(
            "Create main pages (Dashboard, Library with grid view)",
            "coder",
            ["frontend/src/pages/Dashboard.tsx", "frontend/src/pages/Library.tsx"],
            fe_deps,
            phase_map["FRONTEND"], 4,
        )
        fe_task_ids.append(t["id"])
        tasks[t["id"]] = t

        t2 = make_task(
            "Create UI components (ROMCard, FilterSidebar, UploadZone)",
            "coder",
            [
                "frontend/src/components/ROMCard.tsx",
                "frontend/src/components/FilterSidebar.tsx",
                "frontend/src/components/UploadZone.tsx",
            ],
            fe_deps,
            phase_map["FRONTEND"], 4,
        )
        fe_task_ids.append(t2["id"])
        tasks[t2["id"]] = t2

    # ---- Phase TESTING ----
    if has_ci and "TESTING" in phase_map:
        # Tests depend on API and frontend (all prior work)
        test_deps = [api_id] + fe_task_ids
        t = make_task(
            "Create tests for API and core services",
            "reviewer",
            ["tests/test_api.py", "tests/test_scraper.py", "tests/conftest.py"],
            test_deps,
            phase_map["TESTING"], 5,
        )
        tasks[t["id"]] = t

    return tasks, phase_names


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def _build_agent_prompt(task: dict, brain: dict, brain_file: Path) -> str:
    project_path  = str(Path(brain.get("project_path", ".")).resolve())
    spec_summary  = brain.get("spec_summary", "")
    tid           = task["id"]
    files         = "\n".join(f"  - {f}" for f in task["files"])

    context = f"\nPROJECT SPEC (summary):\n{spec_summary[:800]}\n" if spec_summary else ""

    brain_instructions = (
        f"\nBRAIN FILE: {brain_file}\n"
        f"After completing your task, update the brain file:\n"
        f"  1. Read the JSON from {brain_file}\n"
        f"  2. Set brain[\"facts\"][\"task_{tid}_result\"] = {{\n"
        f"       \"files_created\": [<list of absolute paths you actually created/modified>],\n"
        f"       \"summary\": \"<one-sentence description of what you did>\"\n"
        f"     }}\n"
        f"  3. Write the updated JSON back to {brain_file}\n"
        f"Do this ONLY after all files are complete and correct.\n"
    )

    return (
        f"You are a {task['agent_role']} agent in the Herbert Swarm.\n"
        f"Working directory (absolute): {project_path}\n"
        f"All file paths you create/modify must be INSIDE this directory.\n"
        f"{context}\n"
        f"TASK: {task['description']}\n\n"
        f"Files to create/modify:\n{files}\n\n"
        f"Implement the task completely. Create all listed files with production-ready code.\n"
        f"Use best practices for the detected stack. Do not leave TODOs or placeholders.\n"
        f"{brain_instructions}"
    )


def _load_hermes_config() -> dict:
    """Load MiniMax API key and base_url from hermes auth.json + config.yaml."""
    hermes_home = Path.home() / ".hermes"
    config: dict = {
        "base_url": "https://api.minimax.io/anthropic",
        "api_key":  None,
        "model":    "MiniMax-M2.7",
    }

    # Try to load yaml (optional dependency)
    cfg_file = hermes_home / "config.yaml"
    if cfg_file.exists():
        try:
            import importlib.util
            if importlib.util.find_spec("yaml"):
                import yaml  # type: ignore
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

    config["api_key"] = (
        config["api_key"]
        or os.environ.get("MINIMAX_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
    )
    return config


def _run_task(
    tid: str,
    task: dict,
    brain: dict,
    brain_file: Path,
    results: dict,
    lock: threading.Lock,
    semaphore: threading.Semaphore,
    timeout: int,
) -> None:
    """Execute a single task via Hermes AIAgent (MiniMax)."""
    with semaphore:
        prompt = _build_agent_prompt(task, brain, brain_file)
        hermes_agent_dir = Path.home() / ".hermes" / "hermes-agent"

        if str(hermes_agent_dir) not in sys.path:
            sys.path.insert(0, str(hermes_agent_dir))

        try:
            try:
                from run_agent import AIAgent  # type: ignore
            except ImportError:
                raise RuntimeError(
                    f"Hermes AIAgent not found at {hermes_agent_dir}/run_agent.py. "
                    "Install Hermes first: https://github.com/DavidSchuchert/hermes"
                )

            cfg = _load_hermes_config()
            if not cfg["api_key"]:
                raise RuntimeError(
                    "No API key found. Set MINIMAX_API_KEY env var "
                    "or add credentials to ~/.hermes/auth.json"
                )

            agent = AIAgent(
                base_url=cfg["base_url"],
                api_key=cfg["api_key"],
                model=cfg["model"],
                enabled_toolsets=["terminal", "file"],
            )

            result  = agent.run_conversation(user_message=prompt, task_id=tid)
            output  = result.get("response", "") or ""
            success = True

        except Exception as e:
            success = False
            output  = str(e)

        with lock:
            results[tid] = {"success": success, "output": output[:500]}
            log(
                f"  {'✓' if success else '✗'} {tid}: {task['description'][:50]}",
                GREEN if success else RED,
            )
            if not success:
                log(f"    Error: {output[:200]}", RED)


def cmd_run(args) -> None:
    project_path  = Path(args.project).resolve()
    brain_file    = _brain_file_for(project_path)
    brain         = _load_brain(brain_file)

    if not brain.get("tasks"):
        log("ERROR: No plan. Run 'plan' first.", RED)
        sys.exit(1)

    max_parallel  = getattr(args, "parallel", 3)
    dry_run       = getattr(args, "dry_run", False)
    retry_failed  = getattr(args, "retry_failed", False)
    agent_timeout = getattr(args, "timeout", 300)

    if retry_failed:
        retried = 0
        for task in brain["tasks"].values():
            if task["status"] == "failed":
                task["status"] = "pending"
                task.pop("error", None)
                task.pop("completed_at", None)
                retried += 1
        if retried == 0:
            log("No failed tasks to retry.", YELLOW)
            return
        log(f"Retrying {retried} failed task(s)...", YELLOW)
        _save_brain(brain, brain_file)

    run_start = datetime.now()

    log(f"{BOLD}========== HERBERT SWARM 2.0 EXECUTION =========={RESET}", BLUE)
    log(f"Project:  {brain['project_name']}", CYAN)
    log(f"Tasks:    {len(brain['tasks'])}", CYAN)
    log(f"Phases:   {', '.join(brain.get('phases', []))}", CYAN)
    log(f"Parallel: {max_parallel}  Timeout: {agent_timeout}s/agent", CYAN)
    if dry_run:
        log("DRY RUN — no agents will be called", YELLOW)
    if retry_failed:
        log("Mode: retry failed tasks only", YELLOW)

    semaphore = threading.Semaphore(max_parallel)

    for phase_num, phase_name in enumerate(brain.get("phases", []), 1):
        phase_tasks = [
            (tid, t)
            for tid, t in brain["tasks"].items()
            if t["phase"] == phase_num and t["status"] == "pending"
        ]

        if not phase_tasks:
            continue

        log(f"\n{BOLD}----- PHASE {phase_num}: {phase_name} -----{RESET}", BLUE)
        log(f"  {len(phase_tasks)} pending tasks (max {max_parallel} parallel)")

        # Mark all as running, then execute
        for tid, task in phase_tasks:
            task["status"] = "running"
            task["started_at"] = datetime.now().isoformat()
        _save_brain(brain, brain_file)

        if dry_run:
            for tid, task in phase_tasks:
                task["status"] = "done"
                task["completed_at"] = datetime.now().isoformat()
                log(f"  [DRY] ✓ {tid}: {task['description'][:50]}", YELLOW)
        else:
            results: dict = {}
            lock    = threading.Lock()
            threads: list[tuple[str, threading.Thread]] = []

            for tid, task in phase_tasks:
                t = threading.Thread(
                    target=_run_task,
                    args=(tid, task, brain, brain_file, results, lock, semaphore, agent_timeout),
                    daemon=True,
                )
                threads.append((tid, t))
                t.start()

            for tid, t in threads:
                t.join(timeout=agent_timeout + 10)  # grace period beyond agent timeout
                if t.is_alive():
                    log(f"  TIMEOUT: {tid} did not finish within {agent_timeout}s", RED)
                    with lock:
                        results.setdefault(tid, {"success": False, "output": "Agent timed out"})

            for tid, task in phase_tasks:
                r = results.get(tid, {})
                if r.get("success"):
                    task["status"] = "done"
                    task.pop("error", None)
                else:
                    task["status"] = "failed"
                    task["error"]  = r.get("output", "unknown error")[:500]
                task["completed_at"] = datetime.now().isoformat()

        _save_brain(brain, brain_file)
        brain["current_phase"] = phase_num
        _save_brain(brain, brain_file)

    done    = sum(1 for t in brain["tasks"].values() if t["status"] == "done")
    failed  = sum(1 for t in brain["tasks"].values() if t["status"] == "failed")
    total   = len(brain["tasks"])
    elapsed = (datetime.now() - run_start).seconds
    log(
        f"\n{BOLD}COMPLETE: {done}/{total} done, {failed} failed (elapsed: {elapsed}s){RESET}",
        GREEN if not failed else YELLOW,
    )

    if failed:
        log(
            f"Re-run failed tasks: python3 swarm_cli.py run --project {brain['project_path']} --retry-failed",
            YELLOW,
        )


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def cmd_report(args) -> None:
    project_path = Path(getattr(args, "project", None) or ".").resolve()
    brain_file   = _brain_file_for(project_path)
    brain        = _load_brain(brain_file)
    tasks        = brain.get("tasks", {})
    facts        = brain.get("facts", {})

    if not tasks:
        log("No tasks found. Run 'plan' and 'run' first.", YELLOW)
        return

    total   = len(tasks)
    done    = sum(1 for t in tasks.values() if t["status"] == "done")
    failed  = sum(1 for t in tasks.values() if t["status"] == "failed")
    pending = sum(1 for t in tasks.values() if t["status"] == "pending")
    running = sum(1 for t in tasks.values() if t["status"] == "running")
    success_rate = (done / total * 100) if total else 0

    print(f"\n{BOLD}{CYAN}{'=' * 55}{RESET}")
    print(f"{BOLD}{CYAN}  HERBERT SWARM 2.0 — FINAL REPORT{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 55}{RESET}")
    print(f"\n{BOLD}Project:{RESET} {brain.get('project_name', 'N/A')}")
    print(f"{BOLD}Path:   {RESET} {brain.get('project_path', 'N/A')}")
    print(f"{BOLD}Created:{RESET} {brain.get('created_at', 'N/A')}")
    print()

    print(f"{BOLD}Task Summary ({total} total):{RESET}")
    print(f"  {'done':>8}: {done}  ({success_rate:.0f}%)")
    print(f"  {'failed':>8}: {failed}")
    if pending:
        print(f"  {'pending':>8}: {pending}")
    if running:
        print(f"  {'running':>8}: {running}")
    print()

    icons = {"pending": "○", "running": "◐", "done": "●", "failed": "✗"}
    print(f"{BOLD}By Phase:{RESET}")
    for phase_num, phase_name in enumerate(brain.get("phases", []), 1):
        phase_tasks = [(tid, t) for tid, t in tasks.items() if t["phase"] == phase_num]
        if not phase_tasks:
            continue
        p_done   = sum(1 for _, t in phase_tasks if t["status"] == "done")
        p_failed = sum(1 for _, t in phase_tasks if t["status"] == "failed")
        bar = "●" * p_done + "✗" * p_failed + "○" * (len(phase_tasks) - p_done - p_failed)
        elapsed_parts = []
        for _, t in phase_tasks:
            started, completed = t.get("started_at"), t.get("completed_at")
            if started and completed:
                try:
                    elapsed_parts.append(
                        (datetime.fromisoformat(completed) - datetime.fromisoformat(started)).seconds
                    )
                except Exception:
                    pass
        dur_str = f"  ~{max(elapsed_parts)}s" if elapsed_parts else ""
        print(f"  Phase {phase_num} {phase_name:15s}: [{bar}] {p_done}/{len(phase_tasks)}{dur_str}")

    # Files created
    all_created: list[str] = []
    task_summaries: list[tuple[str, str, str]] = []

    for tid, task in tasks.items():
        fact = facts.get(f"task_{tid}_result", {})
        if isinstance(fact, dict):
            fc = fact.get("files_created", [])
            if isinstance(fc, list):
                all_created.extend(fc)
            summary = fact.get("summary", "")
        else:
            summary = ""
        task_summaries.append((tid, task["status"], summary))

    for tid, task in tasks.items():
        if task["status"] == "done":
            project = brain.get("project_path", "")
            for f in task.get("files", []):
                full = str(Path(project) / f) if project else f
                if full not in all_created:
                    all_created.append(full)

    if all_created:
        unique_files = list(dict.fromkeys(all_created))
        print(f"\n{BOLD}Files Created ({len(unique_files)}):{RESET}")
        for f in unique_files:
            exists = Path(f).exists()
            mark = GREEN + "✓" + RESET if exists else YELLOW + "?" + RESET
            print(f"  {mark} {f}")
    else:
        print(f"\n{BOLD}Files Created:{RESET} (none recorded — run the swarm first)")

    agent_summaries = [(tid, st, sm) for tid, st, sm in task_summaries if sm]
    if agent_summaries:
        print(f"\n{BOLD}Agent Summaries:{RESET}")
        for tid, status, summary in agent_summaries:
            icon  = icons.get(status, "?")
            color = GREEN if status == "done" else RED
            print(f"  {color}{icon}{RESET} {tid}: {summary}")

    failed_tasks = [(tid, t) for tid, t in tasks.items() if t["status"] == "failed"]
    if failed_tasks:
        print(f"\n{BOLD}{RED}Failed Tasks:{RESET}")
        for tid, task in failed_tasks:
            err = task.get("error", "no error recorded")
            print(f"  {RED}✗{RESET} {tid}: {task['description'][:55]}")
            print(f"      Error: {err[:200]}")
        print(f"\n  Retry: python3 swarm_cli.py run --project {brain.get('project_path')} --retry-failed")

    print(f"\n{BOLD}{CYAN}{'=' * 55}{RESET}\n")


# ---------------------------------------------------------------------------
# brain / status / reset
# ---------------------------------------------------------------------------

def _resolve_brain(args) -> tuple[Path, dict]:
    """Load brain from --project path or legacy global file."""
    project_arg = getattr(args, "project", None)
    brain_file  = _brain_file_for(project_arg)
    # Migrate from legacy global brain if needed
    if not brain_file.exists() and not project_arg and _LEGACY_BRAIN_FILE.exists():
        brain_file = _LEGACY_BRAIN_FILE
    brain = _load_brain(brain_file)
    return brain_file, brain


def cmd_brain(args) -> None:
    _, brain = _resolve_brain(args)

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
    icons = {"pending": "○", "running": "◐", "done": "●", "failed": "✗"}
    print(f"\n{BOLD}Tasks ({len(tasks)}):{RESET}")
    for tid, task in tasks.items():
        icon = icons.get(task["status"], "?")
        print(f"  {icon} {tid} [Phase {task['phase']}] {task['description'][:55]}")

    files = brain.get("files", {})
    if files:
        print(f"\n{BOLD}Files ({len(files)}):{RESET}")
        for path in files:
            print(f"  - {path}")


def cmd_status(args) -> None:
    _, brain = _resolve_brain(args)
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

    brain_file, brain = _resolve_brain(args)
    project_name = brain.get("project_name", "?")

    if not getattr(args, "yes", False):
        try:
            answer = input(f"Reset brain for '{project_name}'? This cannot be undone. [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer not in ("y", "yes"):
            log("Reset cancelled.", YELLOW)
            return

    # Remove only project-specific brain, not entire SWARM_HOME
    if brain_file == _LEGACY_BRAIN_FILE:
        if SWARM_HOME.exists():
            shutil.rmtree(SWARM_HOME)
        SWARM_HOME.mkdir(parents=True, exist_ok=True)
    else:
        brain_file.unlink(missing_ok=True)

    log(f"Brain for '{project_name}' reset.", YELLOW)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Herbert Swarm 2.0 CLI")
    subs   = parser.add_subparsers()

    p = subs.add_parser("init", help="Initialize swarm for a project")
    p.add_argument("--project", required=True, help="Absolute path to project directory")
    p.add_argument("--name", help="Project name (defaults to directory name)")
    p.set_defaults(func=cmd_init)

    p = subs.add_parser("plan", help="Analyze SPEC and create execution plan")
    p.add_argument("--project", required=True)
    p.add_argument("--spec", help="Path to spec file (default: <project>/SPEC.md)")
    p.set_defaults(func=cmd_plan)

    p = subs.add_parser("run", help="Execute swarm agents")
    p.add_argument("--project", required=True)
    p.add_argument("--parallel", type=int, default=3, help="Max concurrent agents (default: 3)")
    p.add_argument("--timeout",  type=int, default=300, help="Per-agent timeout in seconds (default: 300)")
    p.add_argument("--dry-run",      action="store_true", dest="dry_run",      help="Plan only, no API calls")
    p.add_argument("--retry-failed", action="store_true", dest="retry_failed", help="Re-run only failed tasks")
    p.set_defaults(func=cmd_run)

    p = subs.add_parser("brain", help="Show brain state")
    p.add_argument("--show",    action="store_true")
    p.add_argument("--project", help="Project directory (optional)")
    p.set_defaults(func=cmd_brain)

    p = subs.add_parser("status", help="Show task status")
    p.add_argument("--project", help="Project directory (optional)")
    p.set_defaults(func=cmd_status)

    p = subs.add_parser("report", help="Show final report: files, durations, success rate")
    p.add_argument("--project", help="Project directory (optional)")
    p.set_defaults(func=cmd_report)

    p = subs.add_parser("reset", help="Reset brain (wipes all task state)")
    p.add_argument("--project", help="Project directory (optional)")
    p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    p.set_defaults(func=cmd_reset)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
