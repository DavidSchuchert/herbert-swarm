"""
Herbert Swarm 2.0 — Intelligent Swarm Orchestration with Shared Brain

Architecture:
- SwarmBrain: Shared blackboard with facts, findings, file inventory
- SwarmMemory: Persistent project context that all agents share  
- SwarmPlanner: Analyzes SPEC, creates dependency graph, assigns tasks
- SwarmCoordinator: Executes tasks with dependency awareness

Each agent:
1. Reads from Brain (what has been created, what's planned)
2. Writes to Brain (files created, findings, dependencies discovered)
3. Coordinates via Planner (who does what, when)
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading

# Constants
SWARM_BRAIN_FILE = "/tmp/herbert-swarm/brain.json"
SWARM_STATE_FILE = "/tmp/herbert-swarm/state.json"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class TaskStatus(Enum):
    PENDING = "pending"
    PLANNED = "planned"
    RUNNING = "running"
    DONE = "done"
    BLOCKED = "blocked"
    FAILED = "failed"


class AgentRole(Enum):
    PLANNER = "planner"      # Analyzes, decomposes tasks
    COORDINATOR = "coordinator"  # Orchestrates execution
    CODER = "coder"          # Writes code
    REVIEWER = "reviewer"    # Reviews, quality gates
    RESEARCHER = "researcher"  # Investigates, gathers info


@dataclass
class Fact:
    """A piece of knowledge in the shared brain"""
    key: str
    value: Any
    source_agent: str
    timestamp: str
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "source_agent": self.source_agent,
            "timestamp": self.timestamp,
            "tags": self.tags
        }


@dataclass
class FileRecord:
    """Record of a file created by an agent"""
    path: str
    agent: str
    size: int = 0
    lines: int = 0
    status: str = "created"
    verified: bool = False
    timestamp: str = ""
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Task:
    """A task in the swarm execution plan"""
    id: str
    description: str
    agent_role: str
    files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: str = TaskStatus.PENDING.value
    priority: int = 0
    phase: int = 0
    created_by: str = ""
    assigned_to: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "agent_role": self.agent_role,
            "files": self.files,
            "dependencies": self.dependencies,
            "status": self.status,
            "priority": self.priority,
            "phase": self.phase,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class SwarmBrain:
    """Shared brain for all swarm agents"""
    project_name: str = ""
    project_path: str = ""
    spec_summary: str = ""
    facts: Dict[str, Fact] = field(default_factory=dict)
    files: Dict[str, FileRecord] = field(default_factory=dict)
    tasks: Dict[str, Task] = field(default_factory=dict)
    agents: Dict[str, Dict] = field(default_factory=dict)
    phases: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    current_phase: int = 0
    
    def save(self):
        """Persist brain to disk"""
        os.makedirs(os.path.dirname(SWARM_BRAIN_FILE), exist_ok=True)
        data = {
            "project_name": self.project_name,
            "project_path": self.project_path,
            "spec_summary": self.spec_summary,
            "facts": {k: v.to_dict() for k, v in self.facts.items()},
            "files": {k: v.to_dict() for k, v in self.files.items()},
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "agents": self.agents,
            "phases": self.phases,
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat(),
            "current_phase": self.current_phase
        }
        with open(SWARM_BRAIN_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls) -> "SwarmBrain":
        """Load brain from disk"""
        if not os.path.exists(SWARM_BRAIN_FILE):
            return cls()
        with open(SWARM_BRAIN_FILE, "r") as f:
            data = json.load(f)
        brain = cls()
        brain.project_name = data.get("project_name", "")
        brain.project_path = data.get("project_path", "")
        brain.spec_summary = data.get("spec_summary", "")
        brain.facts = {k: Fact(**v) for k, v in data.get("facts", {}).items()}
        brain.files = {k: FileRecord(**v) for k, v in data.get("files", {}).items()}
        brain.tasks = {k: Task(**v) for k, v in data.get("tasks", {}).items()}
        brain.agents = data.get("agents", {})
        brain.phases = data.get("phases", [])
        brain.created_at = data.get("created_at", "")
        brain.updated_at = data.get("updated_at", "")
        brain.current_phase = data.get("current_phase", 0)
        return brain
    
    def add_fact(self, key: str, value: Any, agent: str, tags: List[str] = None):
        """Add a fact to the brain"""
        self.facts[key] = Fact(
            key=key,
            value=value,
            source_agent=agent,
            timestamp=datetime.now().isoformat(),
            tags=tags or []
        )
    
    def get_fact(self, key: str) -> Optional[Any]:
        """Get a fact by key"""
        return self.facts.get(key)
    
    def query_facts(self, tag: str) -> List[Fact]:
        """Query facts by tag"""
        return [f for f in self.facts.values() if tag in f.tags]
    
    def add_file(self, path: str, agent: str, size: int = 0, lines: int = 0):
        """Record a file creation"""
        self.files[path] = FileRecord(
            path=path,
            agent=agent,
            size=size,
            lines=lines,
            status="created",
            timestamp=datetime.now().isoformat()
        )
    
    def verify_file(self, path: str) -> bool:
        """Verify a file exists"""
        if path in self.files:
            self.files[path].verified = os.path.exists(path)
            return self.files[path].verified
        return False
    
    def add_task(self, task: Task):
        """Add a task to the brain"""
        self.tasks[task.id] = task
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (all deps done)"""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING.value:
                continue
            deps_done = all(
                self.tasks.get(dep_id, Task(id="")).status == TaskStatus.DONE.value
                for dep_id in task.dependencies
            )
            if deps_done:
                ready.append(task)
        return ready
    
    def get_next_phase_tasks(self) -> List[Task]:
        """Get tasks for the next phase that are ready"""
        next_phase = self.current_phase + 1
        ready = self.get_ready_tasks()
        return [t for t in ready if t.phase == next_phase]


def log(msg: str, color: str = ""):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{RESET}")


def log_brain(msg: str):
    """Log with brain indicator"""
    log(f"[BRAIN] {msg}", CYAN)


# ==================== PLANNER ====================

class SwarmPlanner:
    """
    Intelligent task planner that:
    1. Reads SPEC.md to understand the project
    2. Analyzes dependencies
    3. Creates phases based on dependencies
    4. Assigns tasks to appropriate agents
    """
    
    def __init__(self, brain: SwarmBrain):
        self.brain = brain
    
    def analyze_spec(self, spec_content: str) -> Dict:
        """Analyze SPEC.md and extract key information"""
        analysis = {
            "has_backend": "backend" in spec_content.lower() or "fastapi" in spec_content.lower(),
            "has_frontend": "frontend" in spec_content.lower() or "react" in spec_content.lower(),
            "has_database": "database" in spec_content.lower() or "sqlite" in spec_content.lower(),
            "has_api": "api" in spec_content.lower() or "endpoint" in spec_content.lower(),
            "stack": [],
            "platforms": [],
            "pages": [],
            "components": []
        }
        
        # Detect stack
        if "react" in spec_content.lower():
            analysis["stack"].append("React")
        if "fastapi" in spec_content.lower():
            analysis["stack"].append("FastAPI")
        if "sqlite" in spec_content.lower():
            analysis["stack"].append("SQLite")
        if "tailwind" in spec_content.lower():
            analysis["stack"].append("TailwindCSS")
        
        return analysis
    
    def create_task_graph(self, project_path: str) -> List[Task]:
        """Create task graph based on project structure"""
        tasks = []
        task_id = 1
        
        # Phase 1: Infrastructure (no dependencies)
        infra_task = Task(
            id=f"task-{task_id:03d}",
            description="Create all configuration files (package.json, vite.config, Dockerfile, docker-compose, etc.)",
            agent_role=AgentRole.CODER.value,
            files=[],
            dependencies=[],
            priority=1,
            phase=1,
            created_by="planner"
        )
        tasks.append(infra_task)
        task_id += 1
        
        # Phase 2: Backend Core (depends on INFRA)
        db_task = Task(
            id=f"task-{task_id:03d}",
            description="Create database models and connection layer (SQLAlchemy, ROM model)",
            agent_role=AgentRole.CODER.value,
            files=["backend/core/database.py", "backend/models/rom.py"],
            dependencies=[infra_task.id],
            priority=2,
            phase=2,
            created_by="planner"
        )
        tasks.append(db_task)
        task_id += 1
        
        scraper_task = Task(
            id=f"task-{task_id:03d}",
            description="Create scraper and hasher (ScreenScraper API, SHA1 hashing)",
            agent_role=AgentRole.CODER.value,
            files=["backend/core/scraper.py", "backend/core/hasher.py"],
            dependencies=[infra_task.id],
            priority=2,
            phase=2,
            created_by="planner"
        )
        tasks.append(scraper_task)
        task_id += 1
        
        # Phase 3: Backend API (depends on BACKEND_CORE)
        api_task = Task(
            id=f"task-{task_id:03d}",
            description="Create FastAPI endpoints (ROMs, Platforms, Scrape, Stats)",
            agent_role=AgentRole.CODER.value,
            files=["backend/api/roms.py", "backend/api/platforms.py", "backend/api/scrape.py"],
            dependencies=[db_task.id],
            priority=3,
            phase=3,
            created_by="planner"
        )
        tasks.append(api_task)
        task_id += 1
        
        # Phase 4: Frontend (depends on INFRA)
        frontend_task = Task(
            id=f"task-{task_id:03d}",
            description="Create React pages and components (Dashboard, Library, ROMCard, etc.)",
            agent_role=AgentRole.CODER.value,
            files=["frontend/src/pages/*.tsx", "frontend/src/components/*.tsx"],
            dependencies=[infra_task.id],
            priority=4,
            phase=4,
            created_by="planner"
        )
        tasks.append(frontend_task)
        task_id += 1
        
        # Phase 5: Testing & Integration (depends on ALL)
        test_task = Task(
            id=f"task-{task_id:03d}",
            description="Create tests and Docker setup",
            agent_role=AgentRole.REVIEWER.value,
            files=["tests/*.py", "docker/**/*.yml", "docker/**/*.dockerfile"],
            dependencies=[api_task.id, frontend_task.id],
            priority=5,
            phase=5,
            created_by="planner"
        )
        tasks.append(test_task)
        
        return tasks
    
    def plan(self, project_path: str, spec_content: str) -> SwarmBrain:
        """Create complete execution plan"""
        log(f"{BOLD}PLANNER: Analyzing project...{RESET}", BLUE)
        
        # Analyze spec
        analysis = self.analyze_spec(spec_content)
        self.brain.add_fact(
            "spec_analysis",
            analysis,
            "planner",
            tags=["analysis", "spec"]
        )
        
        # Create task graph
        tasks = self.create_task_graph(project_path)
        for task in tasks:
            self.brain.add_task(task)
        
        # Set phases
        self.brain.phases = ["INFRA", "BACKEND_CORE", "BACKEND_API", "FRONTEND", "TESTING"]
        
        # Add planning facts
        self.brain.add_fact(
            "task_count",
            len(tasks),
            "planner",
            tags=["planning"]
        )
        self.brain.add_fact(
            "phases",
            self.brain.phases,
            "planner",
            tags=["planning", "phases"]
        )
        
        self.brain.save()
        log_brain(f"Plan created: {len(tasks)} tasks across {len(self.brain.phases)} phases")
        
        return self.brain


# ==================== COORDINATOR ====================

class SwarmCoordinator:
    """
    Coordinates task execution across agents:
    1. Manages phase progression
    2. Assigns tasks to agents
    3. Tracks dependencies
    4. Collects results
    """
    
    def __init__(self, brain: SwarmBrain):
        self.brain = brain
    
    def get_executable_tasks(self, max_parallel: int = 3) -> List[Task]:
        """Get tasks that can run now (dependencies met, within parallel limit)"""
        ready = self.brain.get_ready_tasks()
        
        # Filter by current phase
        next_phase = self.brain.current_phase + 1
        phase_ready = [t for t in ready if t.phase == next_phase]
        
        # Respect parallel limit
        return phase_ready[:max_parallel]
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent"""
        if task_id not in self.brain.tasks:
            return False
        
        task = self.brain.tasks[task_id]
        if task.status != TaskStatus.PENDING.value:
            return False
        
        task.status = TaskStatus.RUNNING.value
        task.assigned_to = agent_id
        task.started_at = datetime.now().isoformat()
        self.brain.save()
        
        log(f"{YELLOW}[COORD] Assigned {task_id} to {agent_id}{RESET}")
        return True
    
    def complete_task(self, task_id: str, result: Dict = None, error: str = None):
        """Mark a task as complete"""
        if task_id not in self.brain.tasks:
            return
        
        task = self.brain.tasks[task_id]
        task.status = TaskStatus.DONE.value if not error else TaskStatus.FAILED.value
        task.completed_at = datetime.now().isoformat()
        task.result = result
        task.error = error
        
        # Record files created
        if result and "files_created" in result:
            for f in result["files_created"]:
                self.brain.add_file(f, task.assigned_to or "unknown")
        
        self.brain.save()
        
        if error:
            log(f"{RED}[COORD] Task {task_id} FAILED: {error}{RESET}")
        else:
            log(f"{GREEN}[COORD] Task {task_id} COMPLETE{RESET}")
    
    def advance_phase(self) -> bool:
        """Advance to next phase"""
        next_phase = self.brain.current_phase + 1
        phase_tasks = [t for t in self.brain.tasks.values() if t.phase == next_phase]
        
        if not phase_tasks:
            return False
        
        all_done = all(t.status == TaskStatus.DONE.value for t in phase_tasks)
        if not all_done:
            return False
        
        self.brain.current_phase = next_phase
        self.brain.save()
        
        phase_name = self.brain.phases[next_phase - 1] if next_phase <= len(self.brain.phases) else f"Phase {next_phase}"
        log(f"{BOLD}{BLUE}[COORD] ===== PHASE {next_phase}: {phase_name} ====={RESET}")
        return True
    
    def is_complete(self) -> bool:
        """Check if all tasks are complete"""
        return all(
            t.status in [TaskStatus.DONE.value, TaskStatus.FAILED.value]
            for t in self.brain.tasks.values()
        )
    
    def get_status_summary(self) -> Dict:
        """Get current status summary"""
        tasks = list(self.brain.tasks.values())
        return {
            "total": len(tasks),
            "done": sum(1 for t in tasks if t.status == TaskStatus.DONE.value),
            "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING.value),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING.value),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED.value),
            "current_phase": self.brain.current_phase,
            "next_phase": self.brain.current_phase + 1,
            "phases": self.brain.phases
        }


# ==================== AGENT FACTORY ====================

def create_agent_prompt(task: Task, brain: SwarmBrain, project_path: str) -> str:
    """Create a detailed prompt for an agent based on task and brain context"""
    
    # Get relevant facts from brain
    spec_analysis = brain.get_fact("spec_analysis")
    files_created = list(brain.files.keys())
    
    prompt = f"""You are a {task.agent_role.upper()} agent for project "{brain.project_name}".

## YOUR TASK (Task ID: {task.id})
{task.description}

## FILES TO CREATE
{chr(10).join(f'- {f}' for f in task.files)}

## PROJECT PATH
{brain.project_path}

## PREVIOUS FILES CREATED (in this swarm)
{chr(10).join(f'- {f}' for f in files_created) if files_created else '(none yet)'}

## DEPENDENCIES (these tasks must complete first)
{chr(10).join(f'- {d}' for d in task.dependencies) if task.dependencies else '(no dependencies)'}

## SPEC CONTEXT
{brain.spec_summary[:1500]}

## KNOWLEDGE FROM OTHER AGENTS
"""
    
    # Add facts from brain
    for key, fact in brain.facts.items():
        if fact.source_agent != "planner" and fact.source_agent != task.id:
            prompt += f"- [{fact.source_agent}] {key}: {str(fact.value)[:200]}...\n"
    
    prompt += f"""
## INSTRUCTIONS
1. Read the brain at {SWARM_BRAIN_FILE} to understand current state
2. Create ALL files listed above - COMPLETE code, no placeholders
3. Log each file creation: [AGENT-{task.id}] Created: <filename>
4. Write result to /tmp/herbert-swarm/task-result-{task.id}.json
5. Update brain with your findings using the Brain API

## LOG FORMAT
Use this format for all logging:
[BRAIN] <message> - to share knowledge
[AGENT-{task.id}] <message> - for file operations
[STATUS] <message> - for task completion

START NOW."""
    
    return prompt


# ==================== MAIN SWARM ORCHESTRATOR ====================

class HerbertSwarm:
    """
    Main swarm orchestrator that coordinates the entire process.
    This is the "master" that manages everything.
    """
    
    def __init__(self, project_name: str, project_path: str):
        self.project_name = project_name
        self.project_path = project_path
        self.brain = SwarmBrain()
        self.brain.project_name = project_name
        self.brain.project_path = project_path
        self.brain.created_at = datetime.now().isoformat()
        
        self.planner = SwarmPlanner(self.brain)
        self.coordinator = SwarmCoordinator(self.brain)
        
        # Ensure directories exist
        os.makedirs("/tmp/herbert-swarm", exist_ok=True)
        os.makedirs(project_path, exist_ok=True)
    
    def initialize(self, spec_content: str = None):
        """Initialize the swarm with project spec"""
        log(f"{BOLD}{BLUE}========== HERBERT SWARM 2.0 =========={RESET}", BOLD + BLUE)
        log(f"Project: {self.project_name}", CYAN)
        log(f"Path: {self.project_path}", CYAN)
        
        # Load or create brain
        if os.path.exists(SWARM_BRAIN_FILE):
            self.brain = SwarmBrain.load()
            log_brain("Loaded existing brain from disk")
        else:
            # Analyze spec and create plan
            if spec_content is None:
                spec_path = Path(self.project_path) / "SPEC.md"
                spec_content = spec_path.read_text() if spec_path.exists() else "No SPEC.md"
            
            self.brain.spec_summary = spec_content[:2000]
            self.planner.plan(self.project_path, spec_content)
        
        # Show initial status
        status = self.coordinator.get_status_summary()
        log(f"\n{BOLD}Plan: {status['total']} tasks across {len(status['phases'])} phases{RESET}")
        for i, phase in enumerate(status['phases'], 1):
            phase_tasks = [t for t in self.brain.tasks.values() if t.phase == i]
            log(f"  Phase {i}: {phase} ({len(phase_tasks)} tasks)")
        
        return self
    
    def run_phase(self, phase: int, max_parallel: int = 3) -> List[Dict]:
        """Execute all tasks in a phase with parallel agents"""
        phase_name = self.brain.phases[phase - 1] if phase <= len(self.brain.phases) else f"Phase {phase}"
        log(f"\n{BOLD}{BLUE}===== PHASE {phase}: {phase_name} ====={RESET}")
        
        results = []
        phase_tasks = [t for t in self.brain.tasks.values() if t.phase == phase]
        
        while True:
            # Get ready tasks
            ready = [t for t in phase_tasks if t.status == TaskStatus.PENDING.value]
            if not ready:
                break
            
            # Get executable batch
            batch = ready[:max_parallel]
            
            log(f"Executing {len(batch)} tasks in parallel...")
            
            # In real implementation, this would spawn actual agents via delegate_task
            for task in batch:
                self.coordinator.assign_task(task.id, f"agent-{task.id}")
            
            # Simulate agent work (in real: delegate_task calls)
            for task in batch:
                # Create agent prompt
                prompt = create_agent_prompt(task, self.brain, self.project_path)
                
                # For now, mark as done (real agents do the work)
                self.coordinator.complete_task(task.id, result={"files_created": task.files})
                
                results.append({"task": task.id, "status": "executed"})
            
            # Check if phase is complete
            phase_done = all(t.status != TaskStatus.PENDING.value for t in phase_tasks)
            if phase_done:
                break
        
        return results
    
    def run(self) -> Dict:
        """Run the entire swarm"""
        self.initialize()
        
        max_phases = max(t.phase for t in self.brain.tasks.values()) if self.brain.tasks else 0
        
        for phase in range(1, max_phases + 1):
            self.run_phase(phase)
            
            # Advance phase
            if not self.coordinator.advance_phase():
                # Check if we can advance or if we're stuck
                status = self.coordinator.get_status_summary()
                if status['pending'] > 0 and status['running'] == 0:
                    log(f"{RED}No tasks running but phase not complete. Possible deadlock.{RESET}")
                    break
        
        # Final summary
        status = self.coordinator.get_status_summary()
        log(f"\n{BOLD}{GREEN}========== SWARM COMPLETE =========={RESET}")
        log(f"Total: {status['total']}, Done: {status['done']}, Failed: {status['failed']}")
        
        return {
            "status": "complete" if self.coordinator.is_complete() else "partial",
            "summary": status,
            "files_created": list(self.brain.files.keys())
        }
    
    def get_brain(self) -> SwarmBrain:
        """Get current brain state"""
        return SwarmBrain.load()
    
    def print_report(self):
        """Print final report"""
        brain = self.get_brain()
        
        print(f"\n{BOLD}{'='*60}")
        print(f"HERBERT SWARM 2.0 — FINAL REPORT")
        print(f"{'='*60}{RESET}\n")
        
        print(f"Project: {brain.project_name}")
        print(f"Path: {brain.project_path}\n")
        
        print(f"{BOLD}PHASES:{RESET}")
        for i, phase in enumerate(brain.phases, 1):
            phase_tasks = [t for t in brain.tasks.values() if t.phase == i]
            done = sum(1 for t in phase_tasks if t.status == TaskStatus.DONE.value)
            print(f"  {i}. {phase}: {done}/{len(phase_tasks)} tasks")
        
        print(f"\n{BOLD}FILES CREATED:{RESET}")
        for path, record in brain.files.items():
            verified = "✓" if record.verified else "?"
            print(f"  {verified} {path} ({record.agent})")
        
        print(f"\n{BOLD}SHARED KNOWLEDGE (Facts):{RESET}")
        for key, fact in brain.facts.items():
            print(f"  [{fact.source_agent}] {key}: {str(fact.value)[:80]}...")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 swarm_brain.py <project_name> <project_path> [spec_file]")
        sys.exit(1)
    
    project_name = sys.argv[1]
    project_path = sys.argv[2]
    spec_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    spec_content = Path(spec_file).read_text() if spec_file else None
    
    swarm = HerbertSwarm(project_name, project_path)
    swarm.run()
    swarm.print_report()
