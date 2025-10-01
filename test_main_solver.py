#!/usr/bin/env python3
"""
Integration test for the Main Solving Loop implementation.

This script tests the complete integration of all components:
- Goal tree management
- Resource bounds and checkpoints
- Agent framework selection
- Tool usage
- Telemetry and learning
- RAG pipeline integration
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the main_loop directory to the path
sys.path.insert(0, str(Path(__file__).parent / "main_loop"))

from main_loop.main_solver import main_solving_loop, select_agent_framework, AgentFramework
from main_loop.goal_tree import construct_goal_tree, GoalStatus
from main_loop.resource_bounds import ResourceBounds, create_default_checkpoints
from main_loop.telemetry import get_telemetry_collector, get_learning_system
from main_loop.tools import get_tools_by_category, AVAILABLE_TOOLS


async def test_basic_functionality():
    """Test basic functionality of the main solver."""
    print("Testing basic functionality...")
    
    objectives = ["Create a simple test file", "Verify the file was created"]
    
    result = await main_solving_loop(
        user_objectives=objectives,
        resource_bounds=ResourceBounds(
            max_iterations=5,
            cost_limit=1.0,
            time_limit=120
        )
    )
    
    print(f"✓ Basic test completed with status: {result['status']}")
    print(f"  Goals completed: {result['telemetry']['goals_completed']}")
    print(f"  Total iterations: {result['telemetry']['total_iterations']}")
    
    return result


async def test_complex_scenario():
    """Test a more complex scenario with multiple objectives."""
    print("\nTesting complex scenario...")
    
    objectives = [
        "Analyze the current project structure",
        "Identify potential improvements",
        "Create a summary report"
    ]
    
    inferred_subgoals = [
        {
            "title": "Directory Analysis",
            "description": "Analyze directory structure and file organization",
            "priority": 3,
            "tags": ["analysis", "structure"]
        },
        {
            "title": "Code Quality Check",
            "description": "Review code quality and identify issues",
            "priority": 2,
            "tags": ["quality", "review"]
        }
    ]
    
    user_checkpoints = [
        {
            "event": "goal_selected",
            "mode": "require_approval",
            "condition": "'analysis' in ctx.get('current_goal', {}).get('description', '').lower()",
            "description": "Analysis goal selected"
        }
    ]
    
    result = await main_solving_loop(
        user_objectives=objectives,
        inferred_subgoals=inferred_subgoals,
        user_checkpoints=user_checkpoints,
        resource_bounds=ResourceBounds(
            max_iterations=10,
            cost_limit=2.0,
            time_limit=300,
            enable_dry_runs=True
        )
    )
    
    print(f"✓ Complex test completed with status: {result['status']}")
    print(f"  Goals in tree: {len(result['goal_tree']['nodes'])}")
    print(f"  Escalations: {len(result['escalations'])}")
    
    return result


async def test_failure_handling():
    """Test failure handling and recovery mechanisms."""
    print("\nTesting failure handling...")
    
    objectives = ["Attempt an impossible task"]
    
    # Very restrictive bounds to force failures
    result = await main_solving_loop(
        user_objectives=objectives,
        resource_bounds=ResourceBounds(
            max_iterations=2,
            cost_limit=0.01,
            time_limit=10,
            no_progress_timeout=5
        )
    )
    
    print(f"✓ Failure test completed with status: {result['status']}")
    print(f"  Escalations: {len(result['escalations'])}")
    if result['escalations']:
        print(f"  Last escalation: {result['escalations'][-1]['reason']}")
    
    return result


def test_goal_tree_operations():
    """Test goal tree construction and manipulation."""
    print("\nTesting goal tree operations...")
    
    objectives = ["Build application", "Test application", "Deploy application"]
    subgoals = [
        {
            "title": "Setup Environment",
            "description": "Set up development environment",
            "priority": 3,
            "tags": ["setup"]
        }
    ]
    
    tree = construct_goal_tree(objectives, subgoals)
    
    print(f"✓ Goal tree created with {len(tree.nodes)} nodes")
    
    # Test goal selection
    ready_goals = tree.get_ready_goals()
    print(f"  Ready goals: {len(ready_goals)}")
    
    # Test status updates
    if ready_goals:
        goal = ready_goals[0]
        tree.update_goal_status(goal.id, GoalStatus.COMPLETED)
        print(f"  Updated goal status: {goal.status}")
    
    # Test completion stats
    stats = tree.get_completion_stats()
    print(f"  Completion stats: {stats}")
    
    return tree


def test_telemetry_system():
    """Test telemetry collection and learning system."""
    print("\nTesting telemetry system...")
    
    collector = get_telemetry_collector()
    learning = get_learning_system()
    
    # Log some test events
    collector.log_event("test_event", step="test_step", success=True)
    collector.log_step_execution("test_execution", {
        "status": "success",
        "duration": 1.5,
        "resources_used": {"tokens": 100, "cost": 0.05}
    })
    
    # Test learning system
    learning.store_explicit_memory("test_fact", "This is a test", "fact")
    learning.record_episodic_trace("test_step", {"status": "success"})
    
    session_summary = collector.get_session_summary()
    learning_summary = learning.get_learning_summary()
    
    print(f"✓ Telemetry system tested")
    print(f"  Session events: {session_summary['total_events']}")
    print(f"  Learning facts: {learning_summary['facts_count']}")
    
    return collector, learning


def test_tool_system():
    """Test the tool system and categorization."""
    print("\nTesting tool system...")
    
    categories = get_tools_by_category()
    
    print(f"✓ Tool system tested")
    print(f"  Tool categories: {len(categories)}")
    print(f"  Total tools: {len(AVAILABLE_TOOLS)}")
    
    for category, tools in categories.items():
        print(f"  {category}: {len(tools)} tools")
    
    return categories


def test_agent_framework_selection():
    """Test agent framework selection logic."""
    print("\nTesting agent framework selection...")
    
    test_cases = [
        ("HIGH", True, "HIGH", "cloud"),
        ("MEDIUM", False, "HIGH", "local"),
        ("LOW", False, "LOW", "local")
    ]
    
    for complexity, collaboration, safety, deployment in test_cases:
        framework = select_agent_framework(complexity, collaboration, safety, deployment)
        print(f"  {complexity}/{collaboration}/{safety}/{deployment} -> {framework.value}")
    
    print("✓ Agent framework selection tested")


async def run_integration_tests():
    """Run all integration tests."""
    print("=" * 80)
    print("MAIN SOLVING LOOP - INTEGRATION TESTS")
    print("=" * 80)
    
    # Test individual components first
    test_goal_tree_operations()
    test_telemetry_system()
    test_tool_system()
    test_agent_framework_selection()
    
    # Test async functionality
    results = {}
    
    try:
        results["basic"] = await test_basic_functionality()
    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        results["basic"] = {"error": str(e)}
    
    try:
        results["complex"] = await test_complex_scenario()
    except Exception as e:
        print(f"✗ Complex test failed: {e}")
        results["complex"] = {"error": str(e)}
    
    try:
        results["failure"] = await test_failure_handling()
    except Exception as e:
        print(f"✗ Failure test failed: {e}")
        results["failure"] = {"error": str(e)}
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        if "error" in result:
            print(f"✗ {test_name}: FAILED - {result['error']}")
            failed += 1
        else:
            print(f"✓ {test_name}: PASSED")
            passed += 1
    
    print(f"\nTotal: {passed + failed}, Passed: {passed}, Failed: {failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    return results


def create_test_data():
    """Create test data directories and files."""
    print("Creating test data...")
    
    # Create directories
    Path("./data/telemetry").mkdir(parents=True, exist_ok=True)
    Path("./data/learning").mkdir(parents=True, exist_ok=True)
    Path("./data/test").mkdir(parents=True, exist_ok=True)
    
    # Create a test file
    test_file = Path("./data/test/sample.txt")
    test_file.write_text("This is a sample test file for the main solver.")
    
    print("✓ Test data created")


def cleanup_test_data():
    """Clean up test data."""
    print("Cleaning up test data...")
    
    import shutil
    
    test_dirs = ["./data/telemetry", "./data/learning", "./data/test"]
    
    for test_dir in test_dirs:
        if Path(test_dir).exists():
            shutil.rmtree(test_dir)
    
    print("✓ Test data cleaned up")


async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Integration tests for Main Solving Loop")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data after running")
    parser.add_argument("--no-setup", action="store_true", help="Skip test data setup")
    
    args = parser.parse_args()
    
    if not args.no_setup:
        create_test_data()
    
    try:
        results = await run_integration_tests()
        
        # Save results
        results_file = Path("./test_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Detailed results saved to: {results_file}")
        
    finally:
        if args.cleanup:
            cleanup_test_data()


if __name__ == "__main__":
    asyncio.run(main())