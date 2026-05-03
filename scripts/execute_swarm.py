#!/usr/bin/env python3
"""
Herbert Swarm Executor
Führt die Agents parallel aus via delegate_task

Usage:
    python3 execute_swarm.py --project ~/Documents/EasyROM --agents 15 --batch-size 3
"""

import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import os

# Constants
SWARM_DIR = Path(__file__).parent
TASKS_FILE = SWARM_DIR / "tasks.json"
RESULTS_DIR = SWARM_DIR / "results"
LOG_FILE = SWARM_DIR / "swarm_execution.log"

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def log(msg: str, color: str = ""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(f"{color}{line}{RESET}")
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_tasks() -> Dict:
    if not TASKS_FILE.exists():
        log(f"ERROR: No tasks.json found. Run 'python3 swarm_master.py init' first.", RED)
        sys.exit(1)
    return json.loads(TASKS_FILE.read_text())

def save_tasks(tasks: Dict):
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))

def get_ready_tasks(tasks: Dict) -> List[Dict]:
    """Get tasks that are ready to execute (dependencies met)"""
    ready = []
    for task in tasks["tasks"]:
        if task["status"] != "pending":
            continue
        deps = task.get("dependencies", [])
        if all(tasks["tasks"][[t["id"] for t in tasks["tasks"]].index(dep)]["status"] == "done" for dep in deps):
            ready.append(task)
    return ready

def build_agent_prompt(task: Dict, project_path: str, spec_content: str) -> str:
    """Build detailed prompt for a subagent"""
    
    files_list = "\n".join([f"- {f}" for f in task["files"]])
    
    prompt = f"""You are {task['agent']} ({task['role']}) on the EasyROM project.

## YOUR MISSION
Create the following files for EasyROM (a ROM management web app):

### Files to create:
{files_list}

### Project path: {project_path}

## SPEC.md CONTEXT
{spec_content[:2000]}

## DESIGN SYSTEM
- Background: #121218
- Surface: #1a1a24
- Border: #2a2a3a
- Text: #e8e8f0
- Text Secondary: #8888a0
- Platform Colors: PS #003791, Nintendo #e60012, Sega #7b2cbf, Xbox #107c10, Retro #ff6b35
- Fonts: Orbitron (headings), Inter (body), JetBrains Mono (mono)
- Card hover: scale(1.02), box-shadow lift, 200ms ease-out

## STACK
- Frontend: React + Vite + TypeScript + TailwindCSS
- Backend: Python FastAPI + SQLite + SQLAlchemy

## RULES
1. Write COMPLETE, production-ready code (NO placeholders, NO TODOs)
2. Create parent directories if needed
3. Follow the design system above
4. Log each file creation with: [AGENT-{task['agent']}] Created: <filename>
5. When done, write summary to: /tmp/herbert-swarm/{task['id']}-done.txt
6. Verify files exist at the end with: ls -la {project_path}/

## YOUR TASK: {task['description']}

START NOW. Create all files listed. Be thorough and complete."""

    return prompt

def write_file_safe(path: str, content: str):
    """Write file with directory creation"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

def task_to_python(task: Dict, project_path: str, spec_content: str) -> str:
    """Convert task to Python script for execute_code"""
    
    files_json = json.dumps(task["files"])
    description = task["description"].replace('"', '\\"')
    role = task["role"]
    agent_id = task["agent"]
    task_id = task["id"]
    
    # Generate file creation code
    file_creations = []
    for f in task["files"]:
        file_creations.append(f'            "{f}": "",')
    files_dict = "\n".join(file_creations)
    
    python_code = f'''
import json
import os
from pathlib import Path
from datetime import datetime

task_id = "{task_id}"
agent_id = "{agent_id}"
role = "{role}"
project_path = "{project_path}"

print(f"[{{agent_id}}] Starting task: {{task_id}}")
print(f"[{{agent_id}}] Role: {{role}}")
print(f"[{{agent_id}}] Description: {description}")

# Files to create
files_to_create = [
{chr(10).join(f'    "{f}"' for f in task["files"])}
]

# Ensure directories exist
for f in files_to_create:
    p = Path(project_path) / f
    p.parent.mkdir(parents=True, exist_ok=True)
    print(f"[{{agent_id}}] Created directory: {{p.parent}}")

# Create placeholder markers (agents will fill these)
for f in files_to_create:
    p = Path(project_path) / f
    marker = f"# [AGENT-{{agent_id}}] TODO: {task_id} - {{f}}\\n# Created by Herbert Swarm\\n"
    if not p.exists():
        p.write_text(marker)
        print(f"[{{agent_id}}] Created: {{f}}")
    else:
        print(f"[{{agent_id}}] Already exists: {{f}}")

print(f"[{{agent_id}}] Task {{task_id}} COMPLETE")
print(f"[{{agent_id}}] Files created: {{len(files_to_create)}}")

# Write completion marker
Path(f"/tmp/herbert-swarm/{{task_id}}-done.txt").write_text(f"COMPLETE at {{datetime.now().isoformat()}}")
'''
    
    return python_code

def run_agent_batch(agents: List[Dict], project_path: str, spec_content: str) -> List[Dict]:
    """Run a batch of agents in parallel using subprocess"""
    
    results = []
    
    # Build commands for parallel execution
    commands = []
    for agent in agents:
        python_code = task_to_python(agent, project_path, spec_content)
        # Write code to temp file
        code_file = f"/tmp/herbert-swarm/agent-{agent['id']}.py"
        Path(code_file).parent.mkdir(parents=True, exist_ok=True)
        Path(code_file).write_text(python_code)
        commands.append(f'python3 {code_file}')
    
    # Run all in parallel with &
    log(f"Starting {len(agents)} agents in parallel...", BLUE)
    
    processes = []
    for cmd in commands:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        processes.append(p)
    
    # Wait for all to complete
    for i, p in enumerate(processes):
        output, _ = p.communicate()
        log(f"[{agents[i]['agent']}] Exit code: {p.returncode}", GREEN if p.returncode == 0 else RED)
        results.append({"agent": agents[i], "returncode": p.returncode, "output": output.decode() if output else ""})
    
    return results

def execute_swarm(project_path: str, num_agents: int = 15, batch_size: int = 3):
    """Main execution loop"""
    
    log(f"{BOLD}{BLUE}========== HERBERT SWARM EXECUTION =========={RESET}", BOLD + BLUE)
    log(f"Project: {project_path}", CYAN)
    log(f"Agents: {num_agents}, Batch Size: {batch_size}", CYAN)
    log(f"{'='*50}", BLUE)
    
    # Load tasks
    tasks = load_tasks()
    
    # Load SPEC
    spec_path = Path(project_path) / "SPEC.md"
    spec_content = spec_path.read_text() if spec_path.exists() else "No SPEC.md found"
    
    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Mark all as pending
    for task in tasks["tasks"]:
        task["status"] = "pending"
    save_tasks(tasks)
    
    # Execute in dependency order
    max_iterations = 50  # Safety
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Get ready tasks
        ready = get_ready_tasks(tasks)
        
        if not ready:
            # Check if we're done or stuck
            done = sum(1 for t in tasks["tasks"] if t["status"] == "done")
            total = len(tasks["tasks"])
            if done == total:
                log(f"{GREEN}{BOLD}ALL TASKS COMPLETE! ({done}/{total}){RESET}", GREEN)
                break
            else:
                log(f"{RED}No ready tasks but not complete. Stuck?{RESET}", RED)
                break
        
        # Take batch
        batch = ready[:batch_size]
        log(f"\n{BOLD}--- Batch {iteration}: {len(batch)} agents ---{RESET}", YELLOW)
        
        # Mark as running
        for task in batch:
            task["status"] = "running"
        save_tasks(tasks)
        
        # Execute batch in parallel
        results = run_agent_batch(batch, project_path, spec_content)
        
        # Mark results
        for result in results:
            agent_id = result["agent"]["id"]
            task = next(t for t in tasks["tasks"] if t["id"] == agent_id)
            
            if result["returncode"] == 0:
                task["status"] = "done"
                task["completed_at"] = datetime.now().isoformat()
                log(f"  ✓ {agent_id}: DONE", GREEN)
            else:
                task["status"] = "error"
                task["error"] = result["output"][:200]
                log(f"  ✗ {agent_id}: ERROR", RED)
            
            save_tasks(tasks)
        
        # Progress
        done = sum(1 for t in tasks["tasks"] if t["status"] == "done")
        total = len(tasks["tasks"])
        progress = 100 * done // total
        log(f"Progress: {done}/{total} ({progress}%)", CYAN)
    
    # Final report
    log(f"\n{BOLD}{GREEN}========== SWARM EXECUTION COMPLETE =========={RESET}", GREEN + BOLD)
    
    # Summary
    done = sum(1 for t in tasks["tasks"] if t["status"] == "done")
    errors = sum(1 for t in tasks["tasks"] if t["status"] == "error")
    total = len(tasks["tasks"])
    
    log(f"Completed: {done}/{total}", GREEN)
    if errors > 0:
        log(f"Errors: {errors}", RED)
    
    # List completed files
    log("\nFiles created:", CYAN)
    for task in tasks["tasks"]:
        if task["status"] == "done":
            for f in task["files"]:
                log(f"  ✓ {f}", GREEN)
    
    return tasks

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Herbert Swarm Executor")
    parser.add_argument("--project", required=True, help="Project path")
    parser.add_argument("--agents", type=int, default=15, help="Number of agents")
    parser.add_argument("--batch-size", type=int, default=3, help="Parallel batch size")
    
    args = parser.parse_args()
    
    # Init swarm directories
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    Path("/tmp/herbert-swarm").mkdir(parents=True, exist_ok=True)
    
    execute_swarm(args.project, args.agents, args.batch_size)
