#!/usr/bin/env python3
"""
Example usage of the Main Solving Loop implementation.

This demonstrates how to use the main solver with different configurations,
goal trees, checkpoints, and resource bounds.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any

from main_solver import main_solving_loop, select_agent_framework, AgentFramework
from goal_tree import GoalTree, GoalNode, GoalPriority, GoalStatus, construct_goal_tree
from resource_bounds import ResourceBounds, UserCheckpoint, create_default_checkpoints
from tools import AVAILABLE_TOOLS, get_tools_by_category


async def example_simple_task():
    """Example 1: Simple single-objective task."""
    print("=" * 60)
    print("EXAMPLE 1: Simple Task")
    print("=" * 60)
    
    objectives = ["Create a simple Python script that prints 'Hello, World!'"]
    
    result = await main_solving_loop(
        user_objectives=objectives
    )
    
    print("Result:")
    print(json.dumps(result, indent=2, default=str))
    return result


async def example_complex_project():
    """Example 2: Complex multi-objective project."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Complex Project")
    print("=" * 60)
    
    objectives = [
        "Design and implement a REST API for user management",
        "Create a database schema for user data",
        "Implement authentication and authorization",
        "Write comprehensive tests",
        "Deploy to a staging environment"
    ]
    
    # Define some inferred subgoals
    inferred_subgoals = [
        {
            "title": "API Design",
            "description": "Design RESTful endpoints for user operations",
            "parent_id": None,  # Will be linked to first objective
            "priority": 3,
            "tags": ["design", "api"]
        },
        {
            "title": "Database Setup",
            "description": "Set up database connection and migrations",
            "parent_id": None,  # Will be linked to second objective
            "priority": 3,
            "tags": ["database", "setup"]
        }
    ]
    
    # Custom resource bounds
    resource_bounds = ResourceBounds(
        max_iterations=20,
        max_depth=5,
        cost_limit=5.0,  # $5 limit
        time_limit=1800,  # 30 minutes
        no_progress_timeout=300,  # 5 minutes
        enable_dry_runs=True,
        sandbox_mode=True
    )
    
    # Custom checkpoints
    user_checkpoints = [
        {
            "event": "goal_selected",
            "mode": "require_approval",
            "condition": "'deploy' in ctx.get('current_goal', {}).get('description', '').lower()",
            "description": "Deployment goal selected - requires approval"
        },
        {
            "event": "before_step",
            "mode": "pause",
            "condition": "'database' in ctx.get('step', {}).get('description', '').lower()",
            "description": "Database operation detected"
        }
    ]
    
    result = await main_solving_loop(
        user_objectives=objectives,
        inferred_subgoals=inferred_subgoals,
        user_checkpoints=user_checkpoints,
        resource_bounds=resource_bounds
    )
    
    print("Result:")
    print(json.dumps(result, indent=2, default=str))
    return result


async def example_research_task():
    """Example 3: Research and analysis task."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Research Task")
    print("=" * 60)
    
    objectives = [
        "Research best practices for microservices architecture",
        "Analyze trade-offs between different deployment strategies",
        "Create a recommendation report with pros and cons"
    ]
    
    # Research-focused checkpoints
    user_checkpoints = [
        {
            "event": "plan_created",
            "mode": "require_approval",
            "condition": "len(ctx.get('plan', {}).get('steps', [])) > 8",
            "description": "Complex research plan created"
        },
        {
            "event": "after_goal_execution",
            "mode": "require_approval",
            "condition": "ctx.get('result', {}).get('status') == 'SUCCESS'",
            "description": "Research goal completed - review findings"
        }
    ]
    
    result = await main_solving_loop(
        user_objectives=objectives,
        user_checkpoints=user_checkpoints
    )
    
    print("Result:")
    print(json.dumps(result, indent=2, default=str))
    return result


async def example_with_rag_integration():
    """Example 4: Task that uses RAG pipeline for information gathering."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: RAG Integration")
    print("=" * 60)
    
    objectives = [
        "Analyze the uploaded PDF documents and summarize key findings",
        "Extract actionable insights from the research papers",
        "Create a structured report with recommendations"
    ]
    
    # Ensure we have some PDFs to work with
    pdf_dir = Path("./data/pdfs")
    if not pdf_dir.exists() or not list(pdf_dir.glob("*.pdf")):
        print("Note: No PDFs found in ./data/pdfs/ - this example will use simulated data")
    
    result = await main_solving_loop(
        user_objectives=objectives
    )
    
    print("Result:")
    print(json.dumps(result, indent=2, default=str))
    return result


async def example_failure_handling():
    """Example 5: Demonstrate failure handling and recovery."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Failure Handling")
    print("=" * 60)
    
    objectives = [
        "Attempt an impossible task that will fail",
        "Recover from the failure gracefully",
        "Complete a simpler alternative task"
    ]
    
    # Strict resource bounds to trigger failures
    resource_bounds = ResourceBounds(
        max_iterations=3,  # Very low limit
        cost_limit=0.1,   # Very low cost limit
        time_limit=60,    # 1 minute limit
        retry_limit=1,    # Only 1 retry
        no_progress_timeout=30  # 30 seconds
    )
    
    # Checkpoints for failure scenarios
    user_checkpoints = [
        {
            "event": "after_goal_execution",
            "mode": "require_approval",
            "condition": "ctx.get('result', {}).get('status') == 'FAILURE'",
            "description": "Goal execution failed - decide next action"
        }
    ]
    
    result = await main_solving_loop(
        user_objectives=objectives,
        user_checkpoints=user_checkpoints,
        resource_bounds=resource_bounds
    )
    
    print("Result:")
    print(json.dumps(result, indent=2, default=str))
    return result


def demonstrate_goal_tree_operations():
    """Demonstrate goal tree construction and manipulation."""
    print("\n" + "=" * 60)
    print("GOAL TREE OPERATIONS DEMO")
    print("=" * 60)
    
    # Create a goal tree
    objectives = ["Build a web application", "Deploy to production"]
    subgoals = [
        {
            "title": "Frontend Development",
            "description": "Create React frontend",
            "priority": 3,
            "tags": ["frontend", "react"]
        },
        {
            "title": "Backend Development", 
            "description": "Create Express.js backend",
            "priority": 3,
            "tags": ["backend", "nodejs"]
        }
    ]
    
    tree = construct_goal_tree(objectives, subgoals)
    
    print("Initial Goal Tree:")
    print(json.dumps(tree.to_dict(), indent=2, default=str))
    
    # Get ready goals
    ready_goals = tree.get_ready_goals()
    print(f"\nReady goals: {len(ready_goals)}")
    for goal in ready_goals:
        print(f"  - {goal.title}: {goal.description}")
    
    # Select next goal
    next_goal = tree.select_next_goal()
    if next_goal:
        print(f"\nSelected next goal: {next_goal.title}")
        
        # Update status
        tree.update_goal_status(next_goal.id, GoalStatus.IN_PROGRESS)
        print(f"Updated status to: {next_goal.status}")
    
    # Get completion stats
    stats = tree.get_completion_stats()
    print(f"\nCompletion stats: {stats}")


def demonstrate_resource_management():
    """Demonstrate resource bounds and checkpoint management."""
    print("\n" + "=" * 60)
    print("RESOURCE MANAGEMENT DEMO")
    print("=" * 60)
    
    # Create resource bounds
    bounds = ResourceBounds.from_settings()
    print("Default resource bounds:")
    print(f"  Max iterations: {bounds.max_iterations}")
    print(f"  Cost limit: ${bounds.cost_limit}")
    print(f"  Time limit: {bounds.time_limit}s")
    
    # Create custom checkpoints
    checkpoints = create_default_checkpoints()
    bounds.user_checkpoints = checkpoints
    
    print(f"\nDefault checkpoints: {len(checkpoints)}")
    for cp in checkpoints:
        print(f"  - {cp.event}: {cp.description}")
    
    # Demonstrate resource manager
    from resource_bounds import ResourceManager
    manager = ResourceManager(bounds)
    
    # Simulate resource usage
    manager.usage.iterations = 5
    manager.usage.cost = 1.5
    manager.usage.tokens = 5000
    
    print(f"\nCurrent usage: {manager.get_usage_summary()}")
    
    # Check stop conditions
    current_state = {"confidence": 0.9, "safety_violation": False}
    should_stop = manager.check_stop_conditions(current_state)
    print(f"Should stop: {should_stop}")


def demonstrate_tool_categories():
    """Demonstrate available tools and their categories."""
    print("\n" + "=" * 60)
    print("AVAILABLE TOOLS DEMO")
    print("=" * 60)
    
    categories = get_tools_by_category()
    
    print("Tool categories:")
    for category, tools in categories.items():
        print(f"\n{category.upper()}:")
        for tool in tools:
            print(f"  - {tool.__name__}: {tool.__doc__ or 'No description'}")
    
    print(f"\nTotal tools available: {len(AVAILABLE_TOOLS)}")


async def run_all_examples():
    """Run all examples in sequence."""
    print("MAIN SOLVING LOOP - COMPREHENSIVE EXAMPLES")
    print("=" * 80)
    
    # Demonstrate components first
    demonstrate_goal_tree_operations()
    demonstrate_resource_management()
    demonstrate_tool_categories()
    
    # Run async examples
    examples = [
        ("Simple Task", example_simple_task),
        ("Complex Project", example_complex_project),
        ("Research Task", example_research_task),
        ("RAG Integration", example_with_rag_integration),
        ("Failure Handling", example_failure_handling)
    ]
    
    results = {}
    
    for name, example_func in examples:
        try:
            print(f"\n{'='*20} Running {name} {'='*20}")
            result = await example_func()
            results[name] = result
            print(f"✓ {name} completed successfully")
        except Exception as e:
            print(f"✗ {name} failed: {str(e)}")
            results[name] = {"error": str(e)}
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for name, result in results.items():
        status = "SUCCESS" if "error" not in result else "FAILED"
        print(f"{name}: {status}")
    
    return results


async def interactive_mode():
    """Interactive mode for testing custom objectives."""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)
    
    print("Enter your objectives (one per line, empty line to finish):")
    objectives = []
    while True:
        obj = input(f"Objective {len(objectives) + 1}: ").strip()
        if not obj:
            break
        objectives.append(obj)
    
    if not objectives:
        print("No objectives provided. Using default.")
        objectives = ["Complete a simple demonstration task"]
    
    print(f"\nObjectives: {objectives}")
    
    # Ask about checkpoints
    use_checkpoints = input("Use default checkpoints? (y/n): ").lower().startswith('y')
    user_checkpoints = create_default_checkpoints() if use_checkpoints else None
    
    # Ask about resource limits
    use_limits = input("Use strict resource limits? (y/n): ").lower().startswith('y')
    resource_bounds = None
    if use_limits:
        resource_bounds = ResourceBounds(
            max_iterations=10,
            cost_limit=2.0,
            time_limit=300
        )
    
    print("\nRunning main solving loop...")
    result = await main_solving_loop(
        user_objectives=objectives,
        user_checkpoints=[cp.__dict__ for cp in user_checkpoints] if user_checkpoints else None,
        resource_bounds=resource_bounds
    )
    
    print("\nResult:")
    print(json.dumps(result, indent=2, default=str))


async def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await interactive_mode()
    else:
        await run_all_examples()


if __name__ == "__main__":
    asyncio.run(main())