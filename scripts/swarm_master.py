#!/usr/bin/env python3
"""
Herbert Swarm Master
Multi-Agent Orchestration für MiniMax/Herbert

Usage:
    python3 swarm_master.py init --project <path> --agents <count>
    python3 swarm_master.py spawn --count <n> --role <role>
    python3 swarm_master.py execute --all
    python3 swarm_master.py status
    python3 swarm_master.py watch
    python3 swarm_master.py collect --output <path>
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

SWARM_DIR = Path(__file__).parent
PROJECTS_DIR = SWARM_DIR / "projects"
TASKS_FILE = SWARM_DIR / "tasks.json"
AGENTS_DIR = SWARM_DIR / "agents"
RESULTS_DIR = SWARM_DIR / "results"
LOGS_DIR = SWARM_DIR / "logs"

# Farben für Output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def log(msg: str, color: str = ""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {msg}{RESET}")

def init_swarm():
    """Initialize Swarm directories"""
    log("Initializing Herbert Swarm...", BOLD + BLUE)
    
    for d in [PROJECTS_DIR, AGENTS_DIR, RESULTS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    
    log(f"Directories created at {SWARM_DIR}", GREEN)
    return True

def create_tasks(project_path: str, num_agents: int) -> Dict:
    """Create task definitions based on project SPEC.md"""
    
    spec_path = Path(project_path) / "SPEC.md"
    if not spec_path.exists():
        log(f"WARNING: No SPEC.md found at {spec_path}", YELLOW)
        spec_content = ""
    else:
        spec_content = spec_path.read_text()
    
    # EasyROM Task Definition - 15 Agents
    tasks = {
        "project": "EasyROM",
        "project_path": project_path,
        "created_at": datetime.now().isoformat(),
        "num_agents": num_agents,
        "spec_summary": spec_content[:500] if spec_content else "No SPEC.md",
        "tasks": [
            # === PHASE 1: INFRASTRUCTURE (Priority 1) ===
            {
                "id": "infra-1",
                "role": "INFRA",
                "agent": "agent-001",
                "description": "Create all config files: package.json, vite.config.ts, tailwind.config.js, tsconfig.json, index.html",
                "files": [
                    "frontend/package.json",
                    "frontend/vite.config.ts",
                    "frontend/tailwind.config.js",
                    "frontend/tsconfig.json",
                    "frontend/index.html",
                    "backend/requirements.txt",
                    "backend/main.py",
                    "backend/config.py"
                ],
                "priority": 1,
                "status": "pending",
                "dependencies": []
            },
            # === PHASE 2: BACKEND CORE (Priority 2) ===
            {
                "id": "backend-core-1",
                "role": "BACKEND_CORE",
                "agent": "agent-002",
                "description": "Create backend core: database.py (SQLite+SQLAlchemy), models/rom.py",
                "files": [
                    "backend/core/database.py",
                    "backend/models/rom.py",
                    "backend/models/__init__.py",
                    "backend/core/__init__.py"
                ],
                "priority": 2,
                "status": "pending",
                "dependencies": ["infra-1"]
            },
            {
                "id": "backend-core-2",
                "role": "BACKEND_CORE",
                "agent": "agent-003",
                "description": "Create backend scraper.py (ScreenScraper, IGDB, MobyGames fallback), hasher.py (SHA1 dedup)",
                "files": [
                    "backend/core/scraper.py",
                    "backend/core/hasher.py"
                ],
                "priority": 2,
                "status": "pending",
                "dependencies": ["infra-1"]
            },
            {
                "id": "backend-core-3",
                "role": "BACKEND_CORE",
                "agent": "agent-004",
                "description": "Create emulator detection and config: emulator.py",
                "files": [
                    "backend/core/emulator.py"
                ],
                "priority": 2,
                "status": "pending",
                "dependencies": ["infra-1"]
            },
            # === PHASE 3: BACKEND API (Priority 3) ===
            {
                "id": "backend-api-1",
                "role": "BACKEND_API",
                "agent": "agent-005",
                "description": "Create API endpoints: roms.py (CRUD), platforms.py",
                "files": [
                    "backend/api/roms.py",
                    "backend/api/__init__.py"
                ],
                "priority": 3,
                "status": "pending",
                "dependencies": ["backend-core-1"]
            },
            {
                "id": "backend-api-2",
                "role": "BACKEND_API",
                "agent": "agent-006",
                "description": "Create API endpoints: scrape.py, emulator.py, stats.py",
                "files": [
                    "backend/api/scrape.py",
                    "backend/api/emulator.py",
                    "backend/api/stats.py"
                ],
                "priority": 3,
                "status": "pending",
                "dependencies": ["backend-core-1", "backend-core-2"]
            },
            {
                "id": "backend-api-3",
                "role": "BACKEND_API",
                "agent": "agent-007",
                "description": "Create API router aggregator and settings endpoint",
                "files": [
                    "backend/api/settings.py",
                    "backend/router.py"
                ],
                "priority": 3,
                "status": "pending",
                "dependencies": ["backend-api-1", "backend-api-2"]
            },
            # === PHASE 4: FRONTEND (Priority 4) ===
            {
                "id": "frontend-1",
                "role": "FRONTEND",
                "agent": "agent-008",
                "description": "Create React entry: main.tsx, App.tsx, index.css (Tailwind), lib/api.ts",
                "files": [
                    "frontend/src/main.tsx",
                    "frontend/src/App.tsx",
                    "frontend/src/index.css",
                    "frontend/src/lib/api.ts"
                ],
                "priority": 4,
                "status": "pending",
                "dependencies": ["infra-1"]
            },
            {
                "id": "frontend-2",
                "role": "FRONTEND",
                "agent": "agent-009",
                "description": "Create pages: Dashboard.tsx, Library.tsx (main grid view)",
                "files": [
                    "frontend/src/pages/Dashboard.tsx",
                    "frontend/src/pages/Library.tsx"
                ],
                "priority": 4,
                "status": "pending",
                "dependencies": ["frontend-1"]
            },
            {
                "id": "frontend-3",
                "role": "FRONTEND",
                "agent": "agent-010",
                "description": "Create pages: PlatformView.tsx, ROMDetail.tsx",
                "files": [
                    "frontend/src/pages/PlatformView.tsx",
                    "frontend/src/pages/ROMDetail.tsx"
                ],
                "priority": 4,
                "status": "pending",
                "dependencies": ["frontend-1", "frontend-2"]
            },
            {
                "id": "frontend-4",
                "role": "FRONTEND",
                "agent": "agent-011",
                "description": "Create components: ROMCard.tsx (grid card with hover), FilterSidebar.tsx (platform chips)",
                "files": [
                    "frontend/src/components/ROMCard.tsx",
                    "frontend/src/components/FilterSidebar.tsx"
                ],
                "priority": 4,
                "status": "pending",
                "dependencies": ["frontend-1"]
            },
            {
                "id": "frontend-5",
                "role": "FRONTEND",
                "agent": "agent-012",
                "description": "Create components: UploadZone.tsx (drag & drop), SearchBar.tsx, Toast.tsx",
                "files": [
                    "frontend/src/components/UploadZone.tsx",
                    "frontend/src/components/SearchBar.tsx",
                    "frontend/src/components/Toast.tsx"
                ],
                "priority": 4,
                "status": "pending",
                "dependencies": ["frontend-1"]
            },
            {
                "id": "frontend-6",
                "role": "FRONTEND",
                "agent": "agent-013",
                "description": "Create hooks: useROMs.ts, usePlatforms.ts, useToast.ts, useScrape.ts",
                "files": [
                    "frontend/src/hooks/useROMs.ts",
                    "frontend/src/hooks/usePlatforms.ts",
                    "frontend/src/hooks/useToast.ts",
                    "frontend/src/hooks/useScrape.ts"
                ],
                "priority": 4,
                "status": "pending",
                "dependencies": ["frontend-1"]
            },
            # === PHASE 5: CONFIGS & SCRIPTS (Priority 5) ===
            {
                "id": "configs-1",
                "role": "INFRA",
                "agent": "agent-014",
                "description": "Create configs: configs/platforms.json (all platform metadata), scripts/generate_rom_data.py",
                "files": [
                    "configs/platforms.json",
                    "scripts/generate_rom_data.py"
                ],
                "priority": 5,
                "status": "pending",
                "dependencies": []
            },
            # === PHASE 6: TESTING (Priority 6) ===
            {
                "id": "testing-1",
                "role": "TESTER",
                "agent": "agent-015",
                "description": "Create backend tests: test_api.py, test_scraper.py, test_hasher.py",
                "files": [
                    "tests/test_api.py",
                    "tests/test_scraper.py",
                    "tests/test_hasher.py",
                    "tests/__init__.py"
                ],
                "priority": 6,
                "status": "pending",
                "dependencies": ["backend-api-1", "backend-api-2", "backend-core-1", "backend-core-2"]
            },
        ]
    }
    
    return tasks

def save_tasks(tasks: Dict):
    """Save tasks to JSON file"""
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))
    log(f"Tasks saved to {TASKS_FILE}", GREEN)

def load_tasks() -> Dict:
    """Load tasks from JSON file"""
    if not TASKS_FILE.exists():
        log("No tasks.json found. Run 'init' first.", RED)
        return None
    return json.loads(TASKS_FILE.read_text())

def get_task_prompt(task: Dict, project_path: str) -> str:
    """Generate detailed prompt for an agent"""
    
    role = task["role"]
    description = task["description"]
    files = task["files"]
    
    prompt = f"""
You are Agent {task['agent']} ({role}) for project EasyROM.

## YOUR TASK
{description}

## FILES TO CREATE
{chr(10).join(f'- {f}' for f in files)}

## PROJECT PATH
{project_path}

## TECHNICAL STACK
- Frontend: React + Vite + TypeScript + TailwindCSS
- Backend: Python FastAPI + SQLite + SQLAlchemy
- Dark theme: Background #121218, Surface #1a1a24

## DESIGN SYSTEM (follow these)
- Headings: Orbitron (Google Font)
- Body: Inter (Google Font)
- Card hover: scale(1.02), box-shadow lift, 200ms
- Colors: Background #121218, Surface #1a1a24, Border #2a2a3a, Text #e8e8f0, TextSecondary #8888a0
- Platform accents: PS #003791, Nintendo #e60012, Sega #7b2cbf, Xbox #107c10, Retro #ff6b35

## INSTRUCTIONS
1. Read the project SPEC.md at {project_path}/SPEC.md for full context
2. Create ALL files listed above
3. Write COMPLETE, PRODUCTION-READY code (no TODOs, no placeholders)
4. Use proper error handling
5. Log what you're doing to stdout with [AGENT-{task['agent']}] prefix
6. When done, write a summary to /tmp/herbert-swarm/{task['id']}-summary.txt

## VERIFY
After creating files, verify they exist with: ls -la {project_path}/
"""
    return prompt

def cmd_init(args):
    """Initialize a new swarm project"""
    project_path = args.project
    num_agents = args.agents
    
    log(f"{BOLD}Initializing EasyROM Swarm with {num_agents} agents...{RESET}", BLUE)
    
    # Create project directory
    Path(project_path).mkdir(parents=True, exist_ok=True)
    
    # Create EasyROM directory structure
    easyrom_dirs = [
        "backend/api", "backend/core", "backend/models",
        "frontend/src/components", "frontend/src/pages", "frontend/src/hooks", "frontend/src/lib",
        "configs", "scripts", "tests", "docs"
    ]
    for d in easyrom_dirs:
        (Path(project_path) / d).mkdir(parents=True, exist_ok=True)
    
    # Copy SPEC.md to project if it exists
    spec_source = SWARM_DIR.parent / "EasyROM" / "SPEC.md"
    if spec_source.exists():
        import shutil
        shutil.copy(spec_source, Path(project_path) / "SPEC.md")
    
    # Create tasks
    tasks = create_tasks(project_path, num_agents)
    save_tasks(tasks)
    
    log(f"{GREEN}Swarm initialized!{RESET}", BOLD)
    log(f"Project: {project_path}", CYAN)
    log(f"Agents: {num_agents}", CYAN)
    log(f"Tasks: {len(tasks['tasks'])}", CYAN)
    log("", RESET)
    log("Next: Run 'execute --all' to start all agents", YELLOW)

def cmd_spawn(args):
    """Spawn agent pool (no-op for our architecture - agents are execute_code calls)"""
    log(f"Spawning {args.count} agents... (logical only for this architecture)", BLUE)
    log("Agents are executed via execute_code calls, not separate processes", YELLOW)

def cmd_execute(args):
    """Execute all or specific tasks"""
    tasks = load_tasks()
    if not tasks:
        return
    
    if args.all:
        log(f"{BOLD}Executing ALL {len(tasks['tasks'])} tasks...{RESET}", GREEN)
        for task in tasks["tasks"]:
            task["status"] = "pending"
        save_tasks(tasks)
        
        # Execute sequentially (execute_code handles parallelism internally)
        for i, task in enumerate(tasks["tasks"]):
            log(f"[{i+1}/{len(tasks['tasks'])}] {task['id']} ({task['role']}) - {task['description'][:50]}...", BLUE)
            task["status"] = "running"
            save_tasks(tasks)
            
            # In real implementation, this would call execute_code
            # For now, we just mark as done and note it
            log(f"[AGENT-{task['agent']}] Would execute: {task['description']}", CYAN)
            
            task["status"] = "done"
            task["completed_at"] = datetime.now().isoformat()
            save_tasks(tasks)
        
        log(f"{GREEN}All tasks marked as ready for execution!{RESET}", BOLD)
        log("Use 'status' to see task states", YELLOW)
    elif args.task:
        log(f"Executing single task: {args.task}", BLUE)
    else:
        log("Specify --all or --task <id>", RED)

def cmd_status(args):
    """Show status of all tasks"""
    tasks = load_tasks()
    if not tasks:
        return
    
    print(f"\n{BOLD}{'='*60}")
    print(f"EasyROM Swarm Status — {tasks['num_agents']} Agents, {len(tasks['tasks'])} Tasks")
    print(f"{'='*60}{RESET}\n")
    
    # Group by status
    status_groups = {}
    for task in tasks["tasks"]:
        status = task["status"]
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(task)
    
    # Print by status
    for status, task_list in sorted(status_groups.items()):
        color = GREEN if status == "done" else YELLOW if status == "running" else RED if status == "error" else ""
        print(f"{color}{BOLD}{status.upper()}{RESET} ({len(task_list)})")
        for task in task_list:
            print(f"  - {task['id']} [{task['role']}] {task['description'][:45]}...")
        print()
    
    # Summary
    total = len(tasks["tasks"])
    done = len(status_groups.get("done", []))
    print(f"{BOLD}Progress: {done}/{total} ({100*done//total}%){RESET}")

def cmd_watch(args):
    """Watch task execution (placeholder)"""
    log("Watch mode - monitoring task execution...", BLUE)
    log("Press Ctrl+C to stop", YELLOW)
    while True:
        tasks = load_tasks()
        if tasks:
            done = sum(1 for t in tasks["tasks"] if t["status"] == "done")
            total = len(tasks["tasks"])
            print(f"\rProgress: {done}/{total} ({100*done//total}%) ", end="", flush=True)
        time.sleep(2)

def cmd_collect(args):
    """Collect results from all agents"""
    log("Collecting results...", BLUE)
    output_path = args.output
    
    tasks = load_tasks()
    if not tasks:
        return
    
    log(f"Results would be collected to: {output_path}", GREEN)
    log("Files created by agents:", CYAN)
    
    for task in tasks["tasks"]:
        if task["status"] == "done":
            log(f"  ✓ {task['id']}: {', '.join(task['files'])}", GREEN)

def cmd_report(args):
    """Generate final report"""
    tasks = load_tasks()
    if not tasks:
        return
    
    report = f"""
{BOLD}{'='*60}
EasyROM Swarm — Final Report
{'='*60}{RESET}

Project: {tasks['project']}
Path: {tasks['project_path']}
Agents: {tasks['num_agents']}
Tasks: {len(tasks['tasks'])}

{TASK STATUS}
"""
    for task in tasks["tasks"]:
        status_icon = "✓" if task["status"] == "done" else "⟳" if task["status"] == "running" else "✗"
        report += f"  {status_icon} {task['id']} [{task['role']}] — {task['description'][:50]}...\n"
    
    done = sum(1 for t in tasks["tasks"] if t["status"] == "done")
    total = len(tasks["tasks"])
    report += f"""
{'='*60}
COMPLETED: {done}/{total} ({100*done//total}%)
{'='*60}
"""
    print(report)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Herbert Swarm Master")
    subparsers = parser.add_subparsers()
    
    # init
    p_init = subparsers.add_parser("init", help="Initialize swarm")
    p_init.add_argument("--project", required=True, help="Project path")
    p_init.add_argument("--agents", type=int, default=15, help="Number of agents")
    p_init.set_defaults(func=cmd_init)
    
    # spawn
    p_spawn = subparsers.add_parser("spawn", help="Spawn agents")
    p_spawn.add_argument("--count", type=int, default=15, help="Number of agents")
    p_spawn.add_argument("--role", help="Specific role")
    p_spawn.set_defaults(func=cmd_spawn)
    
    # execute
    p_exec = subparsers.add_parser("execute", help="Execute tasks")
    p_exec.add_argument("--all", action="store_true", help="Execute all tasks")
    p_exec.add_argument("--task", help="Execute specific task ID")
    p_exec.set_defaults(func=cmd_execute)
    
    # status
    p_status = subparsers.add_parser("status", help="Show status")
    p_status.set_defaults(func=cmd_status)
    
    # watch
    p_watch = subparsers.add_parser("watch", help="Watch execution")
    p_watch.set_defaults(func=cmd_watch)
    
    # collect
    p_collect = subparsers.add_parser("collect", help="Collect results")
    p_collect.add_argument("--output", required=True, help="Output path")
    p_collect.set_defaults(func=cmd_collect)
    
    # report
    p_report = subparsers.add_parser("report", help="Final report")
    p_report.set_defaults(func=cmd_report)
    
    args = parser.parse_args()
    
    if hasattr(args, "func"):
        init_swarm()
        args.func(args)
    else:
        parser.print_help()
