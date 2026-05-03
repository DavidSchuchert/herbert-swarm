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

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Constants
SWARM_DIR = Path(__file__).parent
BRAIN_FILE = "/tmp/herbert-swarm/brain.json"
STATE_FILE = "/tmp/herbert-swarm/state.json"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log(msg: str, color: str = ""):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{RESET}")


def cmd_init(args):
    """Initialize swarm for a project"""
    project_path = Path(args.project).resolve()
    project_name = args.name or project_path.name
    
    log(f"{BOLD}{BLUE}Initializing Herbert Swarm 2.0 for '{project_name}'...{RESET}", BLUE)
    
    # Create project directories
    (project_path).mkdir(parents=True, exist_ok=True)
    (project_path / "SPEC.md").parent.mkdir(exist_ok=True)
    
    # Initialize brain
    brain = {
        "project_name": project_name,
        "project_path": str(project_path),
        "spec_summary": "",
        "facts": {},
        "files": {},
        "tasks": {},
        "phases": [],
        "created_at": datetime.now().isoformat(),
        "current_phase": 0
    }
    
    os.makedirs("/tmp/herbert-swarm", exist_ok=True)
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain, f, indent=2)
    
    log(f"Swarm initialized at {BRAIN_FILE}", GREEN)
    log(f"Project: {project_name} ({project_path})", CYAN)


def cmd_plan(args):
    """Analyze SPEC and create intelligent task plan"""
    project_path = Path(args.project).resolve()
    
    if not os.path.exists(BRAIN_FILE):
        log(f"ERROR: No swarm initialized. Run 'init' first.", RED)
        return
    
    # Load brain
    with open(BRAIN_FILE, "r") as f:
        brain = json.load(f)
    
    # Read SPEC
    spec_path = project_path / "SPEC.md"
    if not spec_path.exists():
        log(f"WARNING: No SPEC.md found at {spec_path}", YELLOW)
        spec_content = ""
    else:
        spec_content = spec_path.read_text()
        brain["spec_summary"] = spec_content[:2000]
    
    # Analyze spec and create tasks
    tasks = analyze_and_plan(spec_content, project_path, brain.get("phases", []))
    
    # Save
    brain["tasks"] = tasks
    if not brain.get("phases"):
        brain["phases"] = ["INFRA", "BACKEND_CORE", "BACKEND_API", "FRONTEND", "TESTING"]
    
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain, f, indent=2)
    
    log(f"{GREEN}Plan created: {len(tasks)} tasks{RESET}")
    for phase_id, phase_name in enumerate(brain["phases"], 1):
        phase_tasks = [t for t in tasks.values() if t["phase"] == phase_id]
        log(f"  Phase {phase_id}: {phase_name} ({len(phase_tasks)} tasks)")


def analyze_and_plan(spec_content: str, project_path: Path, phases: List[str]) -> Dict:
    """Analyze SPEC.md and create intelligent task plan"""
    
    # Detect what needs to be built
    has_backend = any(k in spec_content.lower() for k in ["fastapi", "backend", "python", "api"])
    has_frontend = any(k in spec_content.lower() for k in ["react", "frontend", "vite", "typescript", "tailwind"])
    has_docker = any(k in spec_content.lower() for k in ["docker", "container"])
    has_tests = any(k in spec_content.lower() for k in ["test", "pytest", "unittest"])
    
    tasks = {}
    task_id = 1
    
    # ===== PHASE 1: INFRASTRUCTURE (no dependencies) =====
    infra_files = []
    if has_docker:
        infra_files.extend([
            "docker/docker-compose.yml",
            "docker/docker-compose.dev.yml",
            "docker/backend/Dockerfile",
            "docker/frontend/Dockerfile",
            "docker/.env.example",
        ])
    if has_backend:
        infra_files.extend([
            "backend/requirements.txt",
            "backend/config.py",
        ])
    if has_frontend:
        infra_files.extend([
            "frontend/package.json",
            "frontend/vite.config.ts",
            "frontend/tailwind.config.js",
        ])
    
    if infra_files:
        tasks[f"task-{task_id:03d}"] = {
            "id": f"task-{task_id:03d}",
            "description": "Create infrastructure and configuration files",
            "agent_role": "coder",
            "files": infra_files,
            "dependencies": [],
            "status": "pending",
            "priority": 1,
            "phase": 1,
            "created_by": "planner"
        }
        task_id += 1
    
    # ===== PHASE 2: BACKEND CORE =====
    if has_backend:
        db_task_files = [
            "backend/core/database.py",
            "backend/models/rom.py",
        ]
        tasks[f"task-{task_id:03d}"] = {
            "id": f"task-{task_id:03d}",
            "description": "Create database models and connection layer (SQLAlchemy async)",
            "agent_role": "coder",
            "files": db_task_files,
            "dependencies": [f"task-{task_id-1:03d}"] if infra_files else [],
            "status": "pending",
            "priority": 2,
            "phase": 2,
            "created_by": "planner"
        }
        task_id += 1
        
        scraper_task_files = [
            "backend/core/scraper.py",
            "backend/core/hasher.py",
        ]
        tasks[f"task-{task_id:03d}"] = {
            "id": f"task-{task_id:03d}",
            "description": "Create scraper (ScreenScraper API) and file hasher (SHA1)",
            "agent_role": "coder",
            "files": scraper_task_files,
            "dependencies": [f"task-{task_id-2:03d}"] if infra_files else [],
            "status": "pending",
            "priority": 2,
            "phase": 2,
            "created_by": "planner"
        }
        task_id += 1
    
    # ===== PHASE 3: BACKEND API =====
    if has_backend:
        api_task_files = [
            "backend/api/roms.py",
            "backend/api/platforms.py",
            "backend/api/scrape.py",
            "backend/main.py",
        ]
        # Find the db_task dependency
        db_dep = None
        for t in tasks.values():
            if "database" in t["description"].lower():
                db_dep = t["id"]
                break
        
        tasks[f"task-{task_id:03d}"] = {
            "id": f"task-{task_id:03d}",
            "description": "Create FastAPI endpoints (ROMs CRUD, Platforms, Scrape)",
            "agent_role": "coder",
            "files": api_task_files,
            "dependencies": [db_dep] if db_dep else [],
            "status": "pending",
            "priority": 3,
            "phase": 3,
            "created_by": "planner"
        }
        task_id += 1
    
    # ===== PHASE 4: FRONTEND =====
    if has_frontend:
        # Find infra task dependency
        infra_dep = None
        for t in tasks.values():
            if t["phase"] == 1:
                infra_dep = t["id"]
                break
        
        frontend_pages = [
            "frontend/src/pages/Dashboard.tsx",
            "frontend/src/pages/Library.tsx",
        ]
        tasks[f"task-{task_id:03d}"] = {
            "id": f"task-{task_id:03d}",
            "description": "Create React pages (Dashboard, Library with grid view)",
            "agent_role": "coder",
            "files": frontend_pages,
            "dependencies": [infra_dep] if infra_dep else [],
            "status": "pending",
            "priority": 4,
            "phase": 4,
            "created_by": "planner"
        }
        task_id += 1
        
        frontend_components = [
            "frontend/src/components/ROMCard.tsx",
            "frontend/src/components/FilterSidebar.tsx",
            "frontend/src/components/UploadZone.tsx",
        ]
        tasks[f"task-{task_id:03d}"] = {
            "id": f"task-{task_id:03d}",
            "description": "Create React components (ROMCard, FilterSidebar, UploadZone)",
            "agent_role": "coder",
            "files": frontend_components,
            "dependencies": [infra_dep] if infra_dep else [],
            "status": "pending",
            "priority": 4,
            "phase": 4,
            "created_by": "planner"
        }
        task_id += 1
    
    # ===== PHASE 5: TESTING & DOCKER =====
    if has_tests:
        test_files = [
            "tests/test_api.py",
            "tests/test_scraper.py",
            "tests/conftest.py",
        ]
        # Depend on backend API task
        api_dep = None
        for t in tasks.values():
            if "api" in t["description"].lower() and t["phase"] == 3:
                api_dep = t["id"]
                break
        
        tasks[f"task-{task_id:03d}"] = {
            "id": f"task-{task_id:03d}",
            "description": "Create pytest tests for API and scraper",
            "agent_role": "reviewer",
            "files": test_files,
            "dependencies": [api_dep] if api_dep else [],
            "status": "pending",
            "priority": 5,
            "phase": 5,
            "created_by": "planner"
        }
    
    return tasks


def cmd_run(args):
    """Execute the swarm with intelligent coordination"""
    if not os.path.exists(BRAIN_FILE):
        log(f"ERROR: No swarm initialized. Run 'init' first.", RED)
        return
    
    with open(BRAIN_FILE, "r") as f:
        brain = json.load(f)
    
    if not brain.get("tasks"):
        log(f"ERROR: No plan. Run 'plan' first.", RED)
        return
    
    log(f"{BOLD}{BLUE}========== HERBERT SWARM 2.0 EXECUTION =========={RESET}", BOLD + BLUE)
    log(f"Project: {brain['project_name']}", CYAN)
    log(f"Tasks: {len(brain['tasks'])}", CYAN)
    log(f"Phases: {', '.join(brain.get('phases', []))}", CYAN)
    
    # Execute phases
    for phase_num, phase_name in enumerate(brain.get("phases", []), 1):
        log(f"\n{BOLD}{BLUE}----- PHASE {phase_num}: {phase_name} -----{RESET}")
        
        # Get tasks for this phase
        phase_tasks = [
            (tid, t) for tid, t in brain["tasks"].items()
            if t["phase"] == phase_num and t["status"] == "pending"
        ]
        
        if not phase_tasks:
            log(f"No pending tasks in this phase", YELLOW)
            continue
        
        log(f"Found {len(phase_tasks)} tasks to execute")
        
        # Execute in parallel batches
        max_parallel = args.parallel if hasattr(args, 'parallel') else 3
        
        for i in range(0, len(phase_tasks), max_parallel):
            batch = phase_tasks[i:i+max_parallel]
            log(f"Batch {i//max_parallel + 1}: {[t[0] for t in batch]}", CYAN)
            
            # Mark as running
            for tid, task in batch:
                task["status"] = "running"
                task["started_at"] = datetime.now().isoformat()
            
            # HERE: In real implementation, we call delegate_task
            # For now, we just mark as done
            for tid, task in batch:
                task["status"] = "done"
                task["completed_at"] = datetime.now().isoformat()
                log(f"  ✓ {tid}: {task['description'][:50]}...", GREEN)
            
            # Save progress
            with open(BRAIN_FILE, "w") as f:
                json.dump(brain, f, indent=2)
        
        brain["current_phase"] = phase_num
    
    # Final save
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain, f, indent=2)
    
    # Summary
    done = sum(1 for t in brain["tasks"].values() if t["status"] == "done")
    total = len(brain["tasks"])
    log(f"\n{BOLD}{GREEN}COMPLETE: {done}/{total} tasks{RESET}")


def cmd_brain(args):
    """Show brain state"""
    if not os.path.exists(BRAIN_FILE):
        log(f"No brain found. Initialize first.", RED)
        return
    
    with open(BRAIN_FILE, "r") as f:
        brain = json.load(f)
    
    print(f"\n{BOLD}{CYAN}===== SWARM BRAIN ====={RESET}")
    print(f"Project: {brain.get('project_name', 'N/A')}")
    print(f"Path: {brain.get('project_path', 'N/A')}")
    print(f"Created: {brain.get('created_at', 'N/A')}")
    print(f"Current Phase: {brain.get('current_phase', 0)}")
    
    print(f"\n{BOLD}Phases:{RESET}")
    for i, p in enumerate(brain.get("phases", []), 1):
        print(f"  {i}. {p}")
    
    print(f"\n{BOLD}Facts ({len(brain.get('facts', {}))}):{RESET}")
    for key, fact in brain.get("facts", {}).items():
        print(f"  [{fact.get('source_agent')}] {key}: {str(fact.get('value', ''))[:60]}...")
    
    print(f"\n{BOLD}Tasks ({len(brain.get('tasks', {}))}):{RESET}")
    for tid, task in brain.get("tasks", {}).items():
        status_icon = {"pending": "○", "running": "◐", "done": "●", "failed": "✗"}.get(task["status"], "?")
        print(f"  {status_icon} {tid} [Phase {task['phase']}] {task['description'][:50]}...")
    
    print(f"\n{BOLD}Files ({len(brain.get('files', {}))}):{RESET}")
    for path in brain.get("files", {}).keys():
        print(f"  - {path}")


def cmd_status(args):
    """Show task status"""
    if not os.path.exists(BRAIN_FILE):
        log(f"No brain found.", RED)
        return
    
    with open(BRAIN_FILE, "r") as f:
        brain = json.load(f)
    
    tasks = brain.get("tasks", {})
    if not tasks:
        log("No tasks planned yet.", YELLOW)
        return
    
    # Group by status
    by_status = {}
    for tid, task in tasks.items():
        status = task["status"]
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(task)
    
    print(f"\n{BOLD}STATUS SUMMARY{RESET}")
    print(f"Total: {len(tasks)}")
    for status, task_list in sorted(by_status.items()):
        print(f"  {status}: {len(task_list)}")
    
    print(f"\n{BOLD}BY PHASE:{RESET}")
    for phase_num, phase_name in enumerate(brain.get("phases", []), 1):
        phase_tasks = [t for t in tasks.values() if t["phase"] == phase_num]
        done = sum(1 for t in phase_tasks if t["status"] == "done")
        print(f"  Phase {phase_num} {phase_name}: {done}/{len(phase_tasks)}")


def cmd_reset(args):
    """Reset brain and state"""
    import shutil
    
    if os.path.exists("/tmp/herbert-swarm"):
        shutil.rmtree("/tmp/herbert-swarm")
        os.makedirs("/tmp/herbert-swarm")
    
    log("Brain and state reset", YELLOW)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Herbert Swarm 2.0 CLI")
    subparsers = parser.add_subparsers()
    
    # init
    p_init = subparsers.add_parser("init", help="Initialize swarm for project")
    p_init.add_argument("--project", required=True, help="Project path")
    p_init.add_argument("--name", help="Project name")
    p_init.set_defaults(func=cmd_init)
    
    # plan
    p_plan = subparsers.add_parser("plan", help="Analyze SPEC and create plan")
    p_plan.add_argument("--project", required=True, help="Project path")
    p_plan.set_defaults(func=cmd_plan)
    
    # run
    p_run = subparsers.add_parser("run", help="Execute swarm")
    p_run.add_argument("--project", required=True, help="Project path")
    p_run.add_argument("--parallel", type=int, default=3, help="Parallel agents")
    p_run.set_defaults(func=cmd_run)
    
    # brain
    p_brain = subparsers.add_parser("brain", help="Show brain state")
    p_brain.add_argument("--show", action="store_true", help="Show brain")
    p_brain.set_defaults(func=cmd_brain)
    
    # status
    p_status = subparsers.add_parser("status", help="Show task status")
    p_status.set_defaults(func=cmd_status)
    
    # reset
    p_reset = subparsers.add_parser("reset", help="Reset brain")
    p_reset.set_defaults(func=cmd_reset)
    
    args = parser.parse_args()
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
