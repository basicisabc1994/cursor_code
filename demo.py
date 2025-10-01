#!/usr/bin/env python3
"""
Demo script for the Main Solving Loop implementation
Shows different scenarios and features
"""

import asyncio
import json
from datetime import timedelta
from main import MainSolvingLoop


async def demo_basic_execution():
    """Demo basic execution without checkpoints"""
    print("="*60)
    print("DEMO 1: Basic Execution (No Checkpoints)")
    print("="*60)
    
    solver = MainSolvingLoop()
    
    result = await solver.main_solving_loop(
        user_objectives=["Create a math utilities file", "Test the math functions"],
        org_policy={"max_iterations": 10, "max_depth": 3},
        cost_limits=50.0,
        time_limits=timedelta(minutes=30),
        sensitivity_levels="LOW",
        user_checkpoints=[]  # No checkpoints for smooth execution
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


async def demo_with_checkpoints():
    """Demo execution with user-defined checkpoints"""
    print("\n" + "="*60)
    print("DEMO 2: Execution with Checkpoints")
    print("="*60)
    
    solver = MainSolvingLoop()
    
    # Define some checkpoints
    checkpoints = [
        {
            "event": "goal_selected",
            "mode": "require_approval",
            "timeout": 5  # Short timeout for demo
        },
        {
            "event": "pre_execution",
            "mode": "pause"
        }
    ]
    
    result = await solver.main_solving_loop(
        user_objectives=["Create a configuration file", "Validate configuration"],
        org_policy={"max_iterations": 5, "max_depth": 2},
        cost_limits=25.0,
        time_limits=timedelta(minutes=15),
        sensitivity_levels="HIGH",
        user_checkpoints=checkpoints
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


async def demo_complex_goals():
    """Demo with more complex, multi-step goals"""
    print("\n" + "="*60)
    print("DEMO 3: Complex Multi-Step Goals")
    print("="*60)
    
    solver = MainSolvingLoop()
    
    result = await solver.main_solving_loop(
        user_objectives=[
            "Set up a simple web server",
            "Create API endpoints for user management", 
            "Add authentication middleware",
            "Write comprehensive tests"
        ],
        org_policy={"max_iterations": 20, "max_depth": 4},
        cost_limits=100.0,
        time_limits=timedelta(hours=1),
        sensitivity_levels="MEDIUM",
        user_checkpoints=[]
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


async def demo_resource_limits():
    """Demo resource limit enforcement"""
    print("\n" + "="*60)
    print("DEMO 4: Resource Limit Enforcement")
    print("="*60)
    
    solver = MainSolvingLoop()
    
    result = await solver.main_solving_loop(
        user_objectives=[
            "Process large dataset",
            "Generate comprehensive report",
            "Create visualization dashboard",
            "Deploy to production"
        ],
        org_policy={"max_iterations": 3, "max_depth": 2},  # Very restrictive
        cost_limits=10.0,  # Low cost limit
        time_limits=timedelta(minutes=5),  # Short time limit
        sensitivity_levels="HIGH",
        user_checkpoints=[]
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


async def main():
    """Run all demos"""
    print("Main Solving Loop - Demonstration Suite")
    print("Based on pseudocode implementation")
    print("This demo shows the system working with fallback implementations")
    print("(without requiring the OpenAI Agents SDK)")
    
    try:
        # Run demos
        await demo_basic_execution()
        await demo_with_checkpoints()
        await demo_complex_goals()
        await demo_resource_limits()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*60)
        
        # Show created files
        import os
        print("\nFiles created during demos:")
        for file in os.listdir("."):
            if file.endswith(('.txt', '.py', '.json', '.html', '.css', '.js')):
                print(f"  - {file}")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())