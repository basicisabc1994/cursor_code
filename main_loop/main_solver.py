import os
import json
import time
import asyncio
from typing import Any, Dict, List, Optional, Union
from enum import Enum

try:
    # Agents SDK is optional but recommended. We design imports to fail soft.
    from agents import Agent, Runner  # type: ignore
except Exception:
    Agent = None  # type: ignore
    Runner = None  # type: ignore

# Import our modules
from .tools import AVAILABLE_TOOLS, get_safe_tools, get_restricted_tools
from .goal_tree import GoalTree, GoalNode, GoalStatus, GoalPriority, construct_goal_tree
from .resource_bounds import ResourceBounds, ResourceManager, CheckpointDecision, EscalationReason
from .telemetry import get_telemetry_collector, get_learning_system, log_telemetry, update_learning
from src.config import settings
from src.rag_pipeline import RAGPipeline


class ResultStatus(Enum):
    """Result status types from the pseudocode."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    STOP_AND_WAIT = "STOP_AND_WAIT"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class AgentFramework(Enum):
    """Available agent frameworks."""
    AGENTSDK = "agentsdk"
    AUTOGEN = "autogen"
    LOW_ABSTRACTION = "low-abstraction"


def select_backend() -> Dict[str, str]:
    """Select LLM backend and model from settings."""
    backend = settings.llm_backend.lower()
    if backend not in ("ollama", "openrouter", "openai"):
        backend = "ollama"
    
    if backend == "ollama":
        return {
            "provider": "ollama",
            "model": settings.ollama_model,
            "host": settings.ollama_host,
        }
    elif backend == "openrouter":
        return {
            "provider": "openrouter",
            "model": settings.openrouter_model,
            "api_key": settings.openrouter_api_key,
            "base_url": settings.openrouter_base_url,
        }
    else:  # openai
        return {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
        }


def select_agent_framework(complexity: str, collaboration: bool, safety: str, deployment: str) -> AgentFramework:
    """Select agent framework based on requirements."""
    if complexity == "HIGH" and collaboration:
        return AgentFramework.AUTOGEN
    elif complexity == "MEDIUM" and safety == "HIGH":
        return AgentFramework.AGENTSDK
    else:
        return AgentFramework.LOW_ABSTRACTION


def build_agent(instructions: str, tools: Optional[List[Any]] = None, framework: AgentFramework = AgentFramework.AGENTSDK):
    """Construct an agent for the solving loop using the selected backend and framework."""
    if framework == AgentFramework.AGENTSDK:
        if Agent is None:
            raise RuntimeError(
                "OpenAI Agents SDK not available. Install from GitHub: "
                "pip install git+https://github.com/openai/openai-agents-python.git"
            )
        
        backend = select_backend()
        agent = Agent(
            name="MainSolver",
            instructions=instructions,
            tools=tools or [],
            model=backend,
        )
        return agent
    
    elif framework == AgentFramework.LOW_ABSTRACTION:
        # Return a simple agent-like object for low-abstraction mode
        return {
            "name": "MainSolver",
            "instructions": instructions,
            "tools": tools or [],
            "backend": select_backend(),
            "framework": "low-abstraction"
        }
    
    else:
        raise NotImplementedError(f"Framework {framework} not yet implemented")


def create_plan_prompt(goal: str) -> str:
    return (
        "You are a meticulous planner. Create a concise step-by-step plan to accomplish the goal. "
        "Plan should include 3-7 steps, each actionable and tool-friendly.\n"
        f"Goal: {goal}\n"
    )


def review_prompt(goal: str, execution_summary: str) -> str:
    return (
        "Review the execution against the goal. Identify pass/fail, risks, and next actions.\n"
        f"Goal: {goal}\n"
        f"Execution Summary: {execution_summary}\n"
    )


def normalize_result(value: Any) -> Dict[str, Any]:
    """Normalize result to standard format from pseudocode."""
    if isinstance(value, dict) and "status" in value:
        return value
    
    # Backward compatibility: wrap legacy constants
    if value in ["SUCCESS", "FAILURE", "STOP_AND_WAIT", "NEEDS_CLARIFICATION"]:
        return {"status": value}
    
    if isinstance(value, str) and value.upper() in [s.value for s in ResultStatus]:
        return {"status": value.upper()}
    
    return {"status": "FAILURE", "error": "unknown_result_type", "meta": {"raw": value}}


async def execute_goal_loop(goal: str, user_checkpoints: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Implements the high-level flow from pseudocode with lightweight prompts.

    Returns a normalized Result-like dict with keys: status, data, error, meta.
    """
    instructions = (
        "You are the Main Solving Loop agent. Follow the structured process: plan, gather info if needed, "
        "execute with tools, and review. Respect checkpoints if present. Use tools when beneficial."
    )
    agent = build_agent(instructions=instructions, tools=AVAILABLE_TOOLS)

    # Planning Phase
    plan_msg = create_plan_prompt(goal)
    plan_result = await Runner.run(agent, plan_msg)  # type: ignore
    plan_text = getattr(plan_result, "final_output", None) or str(plan_result)

    # Basic decision for info gathering: if plan seems vague/short
    if plan_text is None or len(plan_text.split()) < 12:
        clarify_prompt = (
            "The current plan is under-specified. Ask minimal clarifying questions or propose the next best subtask.\n"
            f"Current Plan: {plan_text}\n"
        )
        plan_result = await Runner.run(agent, clarify_prompt)  # type: ignore
        plan_text = getattr(plan_result, "final_output", None) or str(plan_result)

    # Execution Phase: request the agent to execute the plan using available tools
    exec_prompt = (
        "Execute the plan step-by-step. Before each step, consider whether a tool is appropriate. "
        "If a step requires a tool, call it. Provide a concise running summary as you go.\n"
        f"Plan:\n{plan_text}\n"
    )
    exec_result = await Runner.run(agent, exec_prompt)  # type: ignore
    exec_text = getattr(exec_result, "final_output", None) or str(exec_result)

    # Review Phase
    review_msg = review_prompt(goal, exec_text)
    review_result = await Runner.run(agent, review_msg)  # type: ignore
    review_text = getattr(review_result, "final_output", None) or str(review_result)

    return {
        "status": "SUCCESS",
        "data": {
            "plan": plan_text,
            "execution": exec_text,
            "review": review_text,
        },
        "error": None,
        "meta": {
            "backend": select_backend(),
        },
    }


async def main_solving_loop(user_objectives: List[str], 
                          inferred_subgoals: Optional[List[Dict[str, Any]]] = None,
                          user_checkpoints: Optional[List[Dict[str, Any]]] = None,
                          resource_bounds: Optional[ResourceBounds] = None) -> Dict[str, Any]:
    """
    Main solving loop implementation following the pseudocode algorithm.
    
    Args:
        user_objectives: List of high-level objectives to achieve
        inferred_subgoals: Optional list of inferred subgoals
        user_checkpoints: Optional user-defined checkpoints
        resource_bounds: Optional resource bounds configuration
    
    Returns:
        Final status with goal tree, resource usage, and telemetry
    """
    # Phase 1: Initialization
    start_time = time.time()
    
    # Select agent framework
    framework = select_agent_framework(
        complexity="MEDIUM",  # Default to medium complexity
        collaboration=False,
        safety="HIGH",
        deployment="local"
    )
    
    # Construct goal tree
    goal_tree = construct_goal_tree(user_objectives, inferred_subgoals)
    
    # Assign resource bounds
    if resource_bounds is None:
        resource_bounds = ResourceBounds.from_settings()
    
    # Register user checkpoints
    if user_checkpoints:
        from .resource_bounds import register_user_checkpoints
        resource_bounds.user_checkpoints = register_user_checkpoints(user_checkpoints, resource_bounds)
    
    # Initialize resource manager
    resource_manager = ResourceManager(resource_bounds)
    
    # Initialize telemetry and learning
    telemetry = get_telemetry_collector()
    learning = get_learning_system()
    
    # Initialize counters
    iteration_count = 0
    last_progress_tick = time.time()
    
    # Initialize RAG pipeline for information gathering
    try:
        rag_pipeline = RAGPipeline(use_local_embeddings=True)
    except Exception:
        rag_pipeline = None
    
    # Log session start
    telemetry.log_event("session_start", 
                       result={"objectives": user_objectives, "framework": framework.value})
    
    # Phase 2: Main execution loop
    while goal_tree.has_remaining_goals():
        # Manage resource bounds
        current_usage = {
            "iterations": iteration_count,
            "cost": resource_manager.usage.cost,
            "tokens": resource_manager.usage.tokens,
            "expected_cost": iteration_count * 0.1,  # Rough estimate
            "expected_time": iteration_count * 30  # Rough estimate
        }
        resource_manager.manage_resource_bounds(current_usage)
        
        # Check stop conditions
        current_state = {
            "iteration_count": iteration_count,
            "goal_tree": goal_tree.to_dict(),
            "confidence": 0.8  # Default confidence
        }
        
        if resource_manager.check_stop_conditions(current_state):
            break
        
        # Check max iterations
        if (resource_bounds.max_iterations is not None and 
            iteration_count >= resource_bounds.max_iterations):
            resource_manager.escalate(EscalationReason.MAX_ITERATIONS_REACHED)
            break
        
        # User-defined checkpoint at loop iteration start
        checkpoint_context = {
            "goal_tree": goal_tree.to_dict(),
            "iteration_count": iteration_count
        }
        decision = resource_manager.evaluate_user_checkpoints("loop_iteration_start", checkpoint_context)
        if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
            break
        
        # Select next goal
        current_goal = goal_tree.select_next_goal({"max_effort": 2.0})  # 2 hour limit
        
        if current_goal is None:
            break  # No progress possible or all done
        
        # User-defined checkpoint on goal selection
        goal_context = {"current_goal": current_goal.to_dict()}
        decision = resource_manager.evaluate_user_checkpoints("goal_selected", goal_context)
        if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
            break
        
        # Execute goal loop (simplified version for now)
        try:
            # Log goal execution start
            telemetry.log_event("goal_execution_start", 
                              goal_id=current_goal.id,
                              iteration=iteration_count)
            
            result = await execute_goal_loop(current_goal.description, user_checkpoints)
            result = normalize_result(result)
            
            # Log goal execution result
            telemetry.log_step_execution(f"goal_{current_goal.id}", result)
            update_learning(f"goal_{current_goal.id}", result)
            
        except Exception as e:
            result = {
                "status": ResultStatus.FAILURE.value,
                "error": str(e),
                "meta": {"exception_type": type(e).__name__}
            }
            
            # Log exception
            telemetry.log_event("goal_execution_error",
                              goal_id=current_goal.id,
                              result=result,
                              success=False)
        
        # Handle result status
        if result["status"] in [ResultStatus.STOP_AND_WAIT.value, ResultStatus.NEEDS_CLARIFICATION.value]:
            # Queue human follow-ups (in practice, this would integrate with UI)
            break  # Wait for user input
        elif result["status"] == ResultStatus.FAILURE.value:
            # Handle failure
            current_goal.status = GoalStatus.FAILED
            current_goal.failure_reasons.append(result.get("error", "Unknown failure"))
            
            if resource_manager.check_stop_conditions(current_state):
                break
        
        # User-defined checkpoint after goal execution
        execution_context = {
            "current_goal": current_goal.to_dict(),
            "result": result
        }
        decision = resource_manager.evaluate_user_checkpoints("after_goal_execution", execution_context)
        if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
            break
        
        # Update goal tree
        progress_made = False
        if result["status"] == ResultStatus.SUCCESS.value:
            goal_tree.update_goal_status(current_goal.id, GoalStatus.COMPLETED)
            goal_tree.add_execution_result(current_goal.id, result)
            progress_made = True
            last_progress_tick = time.time()
            
            # Log goal completion
            telemetry.log_goal_completion(current_goal.id, True, 
                                        iteration=iteration_count,
                                        duration=time.time() - start_time)
        
        # Check progress timeout
        if not progress_made and (time.time() - last_progress_tick) > resource_bounds.no_progress_timeout:
            resource_manager.escalate(EscalationReason.NO_PROGRESS)
            telemetry.log_escalation("no_progress", {"timeout": resource_bounds.no_progress_timeout})
            break
        
        iteration_count += 1
        resource_manager.usage.iterations = iteration_count
    
    # Log session end
    session_summary = telemetry.get_session_summary()
    learning_summary = learning.get_learning_summary()
    
    telemetry.log_event("session_end", 
                       result=session_summary,
                       duration=time.time() - start_time)
    
    # Return final status
    return {
        "status": "COMPLETED",
        "goal_tree": goal_tree.to_dict(),
        "resource_usage": resource_manager.get_usage_summary(),
        "escalations": resource_manager.escalations,
        "telemetry": {
            "session_summary": session_summary,
            "learning_summary": learning_summary,
            "total_iterations": iteration_count,
            "total_time": time.time() - start_time,
            "goals_completed": len([g for g in goal_tree.nodes.values() if g.status == GoalStatus.COMPLETED]),
            "goals_failed": len([g for g in goal_tree.nodes.values() if g.status == GoalStatus.FAILED])
        }
    }


async def main() -> None:
    """Main entry point for the solver."""
    # Get objectives from environment or use default
    objectives_str = os.environ.get("MAIN_SOLVER_OBJECTIVES", "Implement example feature end-to-end")
    objectives = [obj.strip() for obj in objectives_str.split(",")]
    
    # Example user checkpoints
    user_checkpoints = [
        {
            "event": "loop_iteration_start",
            "mode": "require_approval",
            "condition": "ctx.get('iteration_count', 0) > 10",
            "timeout": 300,
            "description": "High iteration count reached"
        }
    ]
    
    # Run the main solving loop
    result = await main_solving_loop(
        user_objectives=objectives,
        user_checkpoints=user_checkpoints
    )
    
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

