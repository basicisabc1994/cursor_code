import os
import json
from typing import Any, Dict, List, Optional


try:
    # Agents SDK is optional but recommended. We design imports to fail soft.
    from agents import Agent, Runner  # type: ignore
except Exception:
    Agent = None  # type: ignore
    Runner = None  # type: ignore


from .tools import AVAILABLE_TOOLS


DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
DEFAULT_OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")


def select_backend() -> Dict[str, str]:
    """Select LLM backend and model by env, defaulting to Ollama.

    Env vars:
      - LLM_BACKEND: "ollama" (default) | "openrouter"
      - OLLAMA_HOST, OLLAMA_MODEL (optional)
      - OPENROUTER_API_KEY, OPENROUTER_MODEL (optional)
    """
    backend = os.environ.get("LLM_BACKEND", "ollama").lower()
    if backend not in ("ollama", "openrouter"):
        backend = "ollama"
    if backend == "ollama":
        return {
            "provider": "ollama",
            "model": DEFAULT_OLLAMA_MODEL,
            "host": os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
        }
    return {
        "provider": "openrouter",
        "model": DEFAULT_OPENROUTER_MODEL,
        "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "base_url": os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    }


def build_agent(instructions: str, tools: Optional[List[Any]] = None):
    """Construct an agent for the solving loop using the selected backend.

    If Agents SDK is unavailable, raise a helpful error.
    """
    if Agent is None:
        raise RuntimeError(
            "OpenAI Agents SDK not available. Install from GitHub: "
            "pip install git+https://github.com/openai/openai-agents-python.git"
        )

    backend = select_backend()
    # We pass model details in the Agent's model field as a dict for the SDK to interpret.
    # Many SDKs accept either a string model or a richer config object; we use a dict here
    # to keep provider-specific details together.
    agent = Agent(
        name="MainSolver",
        instructions=instructions,
        tools=tools or [],
        model=backend,
    )
    return agent


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


async def main() -> None:
    goal = os.environ.get("MAIN_SOLVER_GOAL", "Implement example feature end-to-end")
    result = await execute_goal_loop(goal)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

