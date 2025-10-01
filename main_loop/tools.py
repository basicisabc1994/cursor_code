import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    # If the Agents SDK is installed, we use its decorators for typed tools
    from agents import function_tool  # type: ignore
except Exception:  # Fallback to a no-op decorator when SDK is not present
    def function_tool(func=None, **_kwargs):  # type: ignore
        if func is None:
            def wrapper(f):
                return f
            return wrapper
        return func

# Import our modules
from .goal_tree import GoalTree, GoalNode, GoalStatus
from .resource_bounds import ResourceManager, CheckpointDecision


# Basic utility tools
@function_tool
def echo(text: str) -> str:
    """Echo back the provided text. Useful for testing the tool-calling path."""
    return text


@function_tool
def emit_summary(step: str, result: str) -> Dict[str, Any]:
    """Emit a lightweight summary record for telemetry or checkpointing."""
    return {
        "step": step, 
        "result": result, 
        "timestamp": time.time(),
        "type": "summary"
    }


# Goal tree management tools
@function_tool
def list_goals(goal_tree_json: str) -> List[Dict[str, Any]]:
    """Given a JSON-encoded goal tree, return a structured list of goals."""
    try:
        tree_data = json.loads(goal_tree_json)
        tree = GoalTree.from_dict(tree_data)
        
        goals = []
        for goal_id, goal in tree.nodes.items():
            goals.append({
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "status": goal.status.value,
                "priority": goal.priority.value,
                "children_count": len(goal.children_ids),
                "dependencies_count": len(goal.dependencies)
            })
        
        return goals
    except Exception as e:
        return [{"error": f"Failed to parse goal tree: {str(e)}"}]


@function_tool
def get_ready_goals(goal_tree_json: str) -> List[Dict[str, Any]]:
    """Get goals that are ready to be executed (dependencies satisfied)."""
    try:
        tree_data = json.loads(goal_tree_json)
        tree = GoalTree.from_dict(tree_data)
        ready_goals = tree.get_ready_goals()
        
        return [
            {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "priority": goal.priority.value,
                "estimated_effort": goal.estimated_effort
            }
            for goal in ready_goals
        ]
    except Exception as e:
        return [{"error": f"Failed to get ready goals: {str(e)}"}]


@function_tool
def update_goal_status(goal_tree_json: str, goal_id: str, status: str) -> Dict[str, Any]:
    """Update the status of a goal in the tree."""
    try:
        tree_data = json.loads(goal_tree_json)
        tree = GoalTree.from_dict(tree_data)
        
        goal_status = GoalStatus(status)
        tree.update_goal_status(goal_id, goal_status)
        
        return {
            "success": True,
            "goal_id": goal_id,
            "new_status": status,
            "updated_tree": tree.to_dict()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Information gathering tools
@function_tool
def gather_information(topic: str, context: str = "") -> Dict[str, Any]:
    """Gather information about a topic using available sources."""
    # This would integrate with the RAG pipeline in practice
    return {
        "topic": topic,
        "context": context,
        "sources": [],
        "information": f"Information gathering for: {topic}",
        "confidence": 0.7,
        "timestamp": time.time()
    }


@function_tool
def validate_understanding(plan: str, examples: List[str]) -> Dict[str, Any]:
    """Validate understanding of a plan against examples."""
    return {
        "plan": plan,
        "examples_count": len(examples),
        "validation_score": 0.8,
        "trusted_sources": True,
        "worked_examples": len(examples) > 0,
        "sufficient_validation": len(examples) >= 2
    }


# Execution and planning tools
@function_tool
def create_plan(goal: str, context: str = "") -> Dict[str, Any]:
    """Create a step-by-step plan for achieving a goal."""
    # Simple plan generation - in practice this would use LLM
    steps = [
        f"Analyze requirements for: {goal}",
        f"Gather necessary resources",
        f"Execute implementation",
        f"Test and validate results",
        f"Review and finalize"
    ]
    
    return {
        "goal": goal,
        "context": context,
        "steps": steps,
        "estimated_duration": len(steps) * 30,  # minutes
        "complexity": "medium",
        "well_defined": len(goal) > 10,
        "timestamp": time.time()
    }


@function_tool
def decompose_plan(plan: str) -> List[Dict[str, Any]]:
    """Decompose a complex plan into smaller subgoals."""
    # Simple decomposition - in practice this would use more sophisticated analysis
    subgoals = []
    
    if "implement" in plan.lower():
        subgoals.extend([
            {"title": "Design Phase", "description": "Create design and architecture"},
            {"title": "Development Phase", "description": "Implement the solution"},
            {"title": "Testing Phase", "description": "Test the implementation"}
        ])
    
    if "deploy" in plan.lower():
        subgoals.extend([
            {"title": "Preparation", "description": "Prepare deployment environment"},
            {"title": "Deployment", "description": "Execute deployment"},
            {"title": "Verification", "description": "Verify deployment success"}
        ])
    
    return subgoals if subgoals else [
        {"title": "Subtask 1", "description": f"First part of: {plan}"},
        {"title": "Subtask 2", "description": f"Second part of: {plan}"}
    ]


@function_tool
def execute_step(step: str, tools: List[str], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single step of a plan."""
    return {
        "step": step,
        "tools_used": tools,
        "constraints": constraints,
        "status": "success",
        "output": f"Executed step: {step}",
        "duration": 5.0,  # seconds
        "resources_used": {"tokens": 100, "cost": 0.01},
        "timestamp": time.time()
    }


@function_tool
def dry_run_step(step: str, tools: List[str], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a dry run of a step to assess risks."""
    return {
        "step": step,
        "dry_run": True,
        "risk_assessment": {
            "risk_level": 0.2,  # 0.0 to 1.0
            "identified_risks": [],
            "mitigation_strategies": []
        },
        "expected_outcome": f"Would execute: {step}",
        "safe_to_proceed": True,
        "timestamp": time.time()
    }


# File and system tools
@function_tool
def read_file(filepath: str) -> Dict[str, Any]:
    """Read contents of a file."""
    try:
        path = Path(filepath)
        if not path.exists():
            return {"success": False, "error": "File not found"}
        
        content = path.read_text(encoding='utf-8')
        return {
            "success": True,
            "filepath": filepath,
            "content": content,
            "size": len(content),
            "lines": len(content.splitlines())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@function_tool
def write_file(filepath: str, content: str) -> Dict[str, Any]:
    """Write content to a file."""
    try:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        
        return {
            "success": True,
            "filepath": filepath,
            "size": len(content),
            "lines": len(content.splitlines())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@function_tool
def list_directory(dirpath: str) -> Dict[str, Any]:
    """List contents of a directory."""
    try:
        path = Path(dirpath)
        if not path.exists():
            return {"success": False, "error": "Directory not found"}
        
        items = []
        for item in path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        
        return {
            "success": True,
            "directory": dirpath,
            "items": items,
            "count": len(items)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@function_tool
def run_command(command: str, working_dir: str = ".") -> Dict[str, Any]:
    """Run a shell command (with safety restrictions)."""
    # Safety check - only allow safe commands
    safe_commands = ["ls", "pwd", "echo", "cat", "grep", "find", "wc", "head", "tail"]
    cmd_parts = command.split()
    
    if not cmd_parts or cmd_parts[0] not in safe_commands:
        return {
            "success": False,
            "error": f"Command '{cmd_parts[0] if cmd_parts else command}' not allowed",
            "allowed_commands": safe_commands
        }
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": True,
            "command": command,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "working_dir": working_dir
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Review and validation tools
@function_tool
def review_execution(result: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Review execution results against acceptance criteria."""
    # Simple review logic - in practice this would be more sophisticated
    passed_tests = []
    failed_tests = []
    
    # Check basic success criteria
    if result.get("status") == "success":
        passed_tests.append("execution_successful")
    else:
        failed_tests.append("execution_failed")
    
    # Check resource usage
    cost = result.get("resources_used", {}).get("cost", 0)
    cost_limit = criteria.get("cost_limit", float('inf'))
    if cost <= cost_limit:
        passed_tests.append("cost_within_limits")
    else:
        failed_tests.append("cost_exceeded")
    
    all_passed = len(failed_tests) == 0
    
    return {
        "review_result": "PASSED" if all_passed else "FAILED",
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "evidence": {
            "execution_result": result,
            "criteria": criteria
        },
        "confidence": 0.9 if all_passed else 0.3,
        "timestamp": time.time()
    }


@function_tool
def analyze_failure(execution_result: Dict[str, Any], review_result: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze failure to determine root cause and suggest adjustments."""
    root_causes = []
    adjustments = []
    
    # Analyze execution failure
    if execution_result.get("status") != "success":
        root_causes.append("execution_failure")
        adjustments.append("retry_with_different_approach")
    
    # Analyze review failure
    failed_tests = review_result.get("failed_tests", [])
    for test in failed_tests:
        if "cost" in test:
            root_causes.append("resource_overuse")
            adjustments.append("optimize_resource_usage")
        elif "time" in test:
            root_causes.append("performance_issue")
            adjustments.append("improve_efficiency")
    
    return {
        "root_causes": root_causes,
        "suggested_adjustments": adjustments,
        "confidence": 0.7,
        "retry_recommended": len(adjustments) > 0,
        "timestamp": time.time()
    }


# Telemetry and monitoring tools
@function_tool
def log_telemetry(step: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Log telemetry data for a step execution."""
    telemetry = {
        "step": step,
        "result_summary": {
            "status": result.get("status", "unknown"),
            "duration": result.get("duration", 0),
            "resources": result.get("resources_used", {})
        },
        "metrics": {
            "tokens_per_minute": result.get("resources_used", {}).get("tokens", 0) / max(result.get("duration", 1), 1) * 60,
            "cost_per_step": result.get("resources_used", {}).get("cost", 0),
            "success_rate": 1.0 if result.get("status") == "success" else 0.0
        },
        "timestamp": time.time()
    }
    
    return {
        "logged": True,
        "telemetry": telemetry
    }


@function_tool
def emit_checkpoint_summary(plan: Dict[str, Any], step: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Emit a periodic summary for checkpointing."""
    return {
        "type": "checkpoint_summary",
        "plan_title": plan.get("goal", "Unknown"),
        "current_step": step,
        "step_result": result.get("status", "unknown"),
        "progress": {
            "completed_steps": plan.get("completed_steps", 0),
            "total_steps": len(plan.get("steps", [])),
            "percentage": (plan.get("completed_steps", 0) / max(len(plan.get("steps", [])), 1)) * 100
        },
        "resources": result.get("resources_used", {}),
        "timestamp": time.time()
    }


# Registry of available tools for the solving loop
AVAILABLE_TOOLS = [
    # Basic utilities
    echo,
    emit_summary,
    
    # Goal management
    list_goals,
    get_ready_goals,
    update_goal_status,
    
    # Information gathering
    gather_information,
    validate_understanding,
    
    # Planning and execution
    create_plan,
    decompose_plan,
    execute_step,
    dry_run_step,
    
    # File operations
    read_file,
    write_file,
    list_directory,
    run_command,
    
    # Review and validation
    review_execution,
    analyze_failure,
    
    # Telemetry
    log_telemetry,
    emit_checkpoint_summary,
]


def get_tools_by_category() -> Dict[str, List[Any]]:
    """Get tools organized by category."""
    return {
        "basic": [echo, emit_summary],
        "goal_management": [list_goals, get_ready_goals, update_goal_status],
        "information": [gather_information, validate_understanding],
        "planning": [create_plan, decompose_plan, execute_step, dry_run_step],
        "file_operations": [read_file, write_file, list_directory, run_command],
        "review": [review_execution, analyze_failure],
        "telemetry": [log_telemetry, emit_checkpoint_summary]
    }


def get_safe_tools() -> List[Any]:
    """Get tools that are safe for unrestricted use."""
    return [
        echo, emit_summary, list_goals, get_ready_goals, 
        gather_information, validate_understanding, create_plan, 
        decompose_plan, dry_run_step, read_file, list_directory,
        review_execution, analyze_failure, log_telemetry, emit_checkpoint_summary
    ]


def get_restricted_tools() -> List[Any]:
    """Get tools that require special permissions."""
    return [
        update_goal_status, execute_step, write_file, run_command
    ]

