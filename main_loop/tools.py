import json
from typing import Any, Dict, List

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


@function_tool
def echo(text: str) -> str:
    """Echo back the provided text. Useful for testing the tool-calling path."""
    return text


@function_tool
def list_goals(goal_tree_json: str) -> List[str]:
    """Given a JSON-encoded goal tree, return a flat list of goal labels."""
    try:
        tree = json.loads(goal_tree_json)
    except Exception:
        return []

    def _flatten(node: Any, acc: List[str]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                acc.append(str(key))
                _flatten(value, acc)
        elif isinstance(node, list):
            for item in node:
                _flatten(item, acc)
        else:
            acc.append(str(node))

    goals: List[str] = []
    _flatten(tree, goals)
    return goals


@function_tool
def emit_summary(step: str, result: str) -> Dict[str, Any]:
    """Emit a lightweight summary record for telemetry or checkpointing."""
    return {"step": step, "result": result}


# Registry of available tools for the solving loop
AVAILABLE_TOOLS = [
    echo,
    list_goals,
    emit_summary,
]

