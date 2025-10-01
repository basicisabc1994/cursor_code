#!/usr/bin/env python3
"""
Main Solving Loop Implementation
Based on the pseudocode algorithm in main_solving_loop_pseudocode.md
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta

# Import existing components
from main_loop.main_solver import build_agent, select_backend, AVAILABLE_TOOLS
from main_loop.tools import AVAILABLE_TOOLS as TOOLS_REGISTRY


class ResultStatus(Enum):
    """Result status enumeration matching pseudocode"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    STOP_AND_WAIT = "STOP_AND_WAIT"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class CheckpointDecision(Enum):
    """Checkpoint decision enumeration"""
    CONTINUE = "CONTINUE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    TIMEOUT = "TIMEOUT"


@dataclass
class Result:
    """Result type matching pseudocode specification"""
    status: ResultStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    @classmethod
    def success(cls, data: Any = None, meta: Dict[str, Any] = None) -> 'Result':
        return cls(ResultStatus.SUCCESS, data=data, meta=meta)
    
    @classmethod
    def failure(cls, error: str, meta: Dict[str, Any] = None) -> 'Result':
        return cls(ResultStatus.FAILURE, error=error, meta=meta)
    
    @classmethod
    def stop_and_wait(cls, error: str = None, meta: Dict[str, Any] = None) -> 'Result':
        return cls(ResultStatus.STOP_AND_WAIT, error=error, meta=meta)
    
    @classmethod
    def needs_clarification(cls, data: Any = None, error: str = None, meta: Dict[str, Any] = None) -> 'Result':
        return cls(ResultStatus.NEEDS_CLARIFICATION, data=data, error=error, meta=meta)


@dataclass
class UserCheckpoint:
    """User-defined checkpoint configuration"""
    event: str
    mode: str = "require_approval"  # "require_approval" | "pause"
    timeout: Optional[int] = None
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None


@dataclass
class ResourceBounds:
    """Resource bounds and constraints"""
    max_iterations: Optional[int] = None
    max_depth: Optional[int] = None
    time_limit: Optional[timedelta] = None
    cost_limit: Optional[float] = None
    token_limit: Optional[int] = None
    no_progress_timeout: timedelta = timedelta(minutes=30)
    retry_limit: int = 3
    retry_backoff: float = 1.0
    approval_timeout: int = 300  # seconds
    user_checkpoints: List[UserCheckpoint] = field(default_factory=list)
    
    # Safety and governance
    tool_permissions: Dict[str, bool] = field(default_factory=dict)
    enable_dry_runs: bool = True
    policies: Dict[str, Any] = field(default_factory=dict)
    data_rules: Dict[str, Any] = field(default_factory=dict)
    sandbox_config: Dict[str, Any] = field(default_factory=dict)
    rollback_strategy: str = "auto"
    rate_limits: Dict[str, Any] = field(default_factory=dict)
    audit_logging: bool = True
    timeouts: Dict[str, int] = field(default_factory=dict)
    
    # Checkpointing
    checkpoints: List[str] = field(default_factory=list)
    summary_every_n: Optional[int] = None


@dataclass
class GoalNode:
    """Goal tree node"""
    objective: str
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    status: str = "pending"  # pending | in_progress | completed | failed
    priority: int = 0
    subgoals: List['GoalNode'] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GoalTree:
    """Goal tree structure"""
    root_goals: List[GoalNode] = field(default_factory=list)
    completed_goals: List[GoalNode] = field(default_factory=list)
    failed_goals: List[GoalNode] = field(default_factory=list)


@dataclass
class Plan:
    """Execution plan structure"""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def is_well_defined(self) -> bool:
        """Check if plan is well-defined"""
        return len(self.steps) > 0 and all('action' in step for step in self.steps)


class MainSolvingLoop:
    """Main solving loop implementation based on pseudocode"""
    
    def __init__(self):
        self.telemetry: Dict[str, Any] = {}
        self.current_usage: Dict[str, Any] = {
            'time_elapsed': 0,
            'cost': 0,
            'tokens': 0,
            'iterations': 0
        }
        
    def normalize_result(self, value: Any) -> Result:
        """Normalize result value to Result object (pseudocode: NormalizeResult)"""
        if isinstance(value, Result):
            return value
        
        # Backward compatibility with legacy constants
        if isinstance(value, str) and value in [status.value for status in ResultStatus]:
            return Result(ResultStatus(value))
        
        if isinstance(value, ResultStatus):
            return Result(value)
            
        return Result(ResultStatus.FAILURE, error="unknown_result_type", meta={"raw": value})
    
    def select_agent_framework(self, complexity: str, collaboration: bool, safety: str, deployment: str) -> str:
        """Select agent framework based on requirements (pseudocode: SelectAgentFramework)"""
        if complexity == "HIGH" and collaboration:
            return "autogen"
        elif complexity == "MEDIUM" and safety == "HIGH":
            return "agentsdk"
        else:
            return "low-abstraction"
    
    def construct_goal_tree(self, objectives: List[str], subgoals: List[str] = None) -> GoalTree:
        """Construct goal tree from objectives (pseudocode: ConstructGoalTree)"""
        tree = GoalTree()
        subgoals = subgoals or []
        
        for objective in objectives:
            goal_node = GoalNode(objective=objective)
            
            # Infer dependencies (simplified)
            dependencies = self.infer_dependencies(objective, subgoals)
            goal_node.dependencies = dependencies
            
            # Define acceptance criteria (simplified)
            acceptance_criteria = self.define_acceptance_criteria(objective)
            goal_node.acceptance_criteria = acceptance_criteria
            
            tree.root_goals.append(goal_node)
        
        # Prioritize tree
        self.prioritize_tree(tree)
        return tree
    
    def infer_dependencies(self, objective: str, subgoals: List[str]) -> List[str]:
        """Infer dependencies for an objective"""
        # Simplified dependency inference
        dependencies = []
        for subgoal in subgoals:
            if any(keyword in objective.lower() for keyword in subgoal.lower().split()):
                dependencies.append(subgoal)
        return dependencies
    
    def define_acceptance_criteria(self, objective: str) -> List[str]:
        """Define acceptance criteria for an objective"""
        # Simplified criteria definition
        return [f"Successfully complete: {objective}", "No errors or failures", "Meets quality standards"]
    
    def prioritize_tree(self, tree: GoalTree) -> None:
        """Prioritize goals in the tree"""
        # Simple priority assignment based on dependencies
        for i, goal in enumerate(tree.root_goals):
            goal.priority = len(goal.dependencies) + i
        
        # Sort by priority
        tree.root_goals.sort(key=lambda g: g.priority)
    
    def assign_resource_bounds(self, org_policy: Dict[str, Any], cost_limits: float, 
                             time_limits: timedelta, sensitivity_levels: str) -> ResourceBounds:
        """Assign resource bounds based on policy and limits"""
        bounds = ResourceBounds(
            cost_limit=cost_limits,
            time_limit=time_limits,
            max_iterations=org_policy.get('max_iterations', 100),
            max_depth=org_policy.get('max_depth', 10)
        )
        
        # Configure based on sensitivity
        if sensitivity_levels == "HIGH":
            bounds.enable_dry_runs = True
            bounds.approval_timeout = 600  # 10 minutes
            bounds.checkpoints = ["schema_change", "external_call", "policy_sensitive"]
        
        return bounds
    
    def register_user_checkpoints(self, user_defs: List[Dict[str, Any]], bounds: ResourceBounds) -> List[UserCheckpoint]:
        """Register user-defined checkpoints"""
        if not user_defs:
            return []
        
        checkpoints = []
        for cp_def in user_defs:
            checkpoint = UserCheckpoint(
                event=cp_def['event'],
                mode=cp_def.get('mode', 'require_approval'),
                timeout=cp_def.get('timeout', bounds.approval_timeout)
            )
            
            # Handle condition if provided
            if 'condition' in cp_def:
                # In a real implementation, this would be more sophisticated
                checkpoint.condition = lambda ctx: True  # Simplified
            
            checkpoints.append(checkpoint)
        
        return checkpoints
    
    def has_remaining_goals(self, goal_tree: GoalTree) -> bool:
        """Check if there are remaining goals to process"""
        return any(goal.status in ['pending', 'in_progress'] for goal in goal_tree.root_goals)
    
    def select_next_goal(self, goal_tree: GoalTree) -> Optional[GoalNode]:
        """Select the next goal to execute"""
        # Find highest priority pending goal with satisfied dependencies
        for goal in goal_tree.root_goals:
            if goal.status == 'pending' and self.dependencies_satisfied(goal, goal_tree):
                return goal
        return None
    
    def dependencies_satisfied(self, goal: GoalNode, goal_tree: GoalTree) -> bool:
        """Check if goal dependencies are satisfied"""
        for dep in goal.dependencies:
            # Check if dependency is completed
            dep_completed = any(
                g.objective == dep and g.status == 'completed' 
                for g in goal_tree.completed_goals
            )
            if not dep_completed:
                return False
        return True
    
    def check_stop_conditions(self, current_state: Dict[str, Any], bounds: ResourceBounds) -> bool:
        """Check if stop conditions are met"""
        # Resource exhaustion
        if bounds.time_limit and self.current_usage['time_elapsed'] > bounds.time_limit.total_seconds():
            return True
        
        if bounds.cost_limit and self.current_usage['cost'] > bounds.cost_limit:
            return True
        
        if bounds.token_limit and self.current_usage['tokens'] > bounds.token_limit:
            return True
        
        # Other stop conditions (simplified)
        if current_state.get('unsafe_action', False):
            return True
        
        if current_state.get('ambiguity_not_resolvable', False):
            return True
        
        return False
    
    def manage_resource_bounds(self, bounds: ResourceBounds, current_usage: Dict[str, Any]) -> None:
        """Manage resource bounds and trigger escalation if needed"""
        self.current_usage.update(current_usage)
        
        # Check limits and trigger escalation
        if bounds.time_limit and self.current_usage['time_elapsed'] > bounds.time_limit.total_seconds():
            self.escalate("time_limit_exceeded")
        
        if bounds.cost_limit and self.current_usage['cost'] > bounds.cost_limit:
            self.escalate("cost_limit_exceeded")
        
        if bounds.token_limit and self.current_usage['tokens'] > bounds.token_limit:
            self.escalate("token_limit_exceeded")
    
    def escalate(self, reason: str) -> None:
        """Escalate to human intervention"""
        print(f"ESCALATION: {reason}")
        # In a real implementation, this would notify humans
    
    def evaluate_user_checkpoints(self, event: str, context: Dict[str, Any], 
                                checkpoints: List[UserCheckpoint], 
                                constraints: ResourceBounds) -> CheckpointDecision:
        """Evaluate user-defined checkpoints"""
        if not checkpoints:
            return CheckpointDecision.CONTINUE
        
        # Find matching checkpoints for this event
        matching_checkpoints = [cp for cp in checkpoints if cp.event == event]
        
        for cp in matching_checkpoints:
            if self.should_trigger_checkpoint(cp, context):
                self.emit_checkpoint_prompt(cp, context)
                
                if self.should_halt_for_checkpoint(cp):
                    # In a real implementation, this would wait for user input
                    decision = self.wait_for_approval_or_timeout(cp.timeout or constraints.approval_timeout)
                    return decision
        
        return CheckpointDecision.CONTINUE
    
    def should_trigger_checkpoint(self, cp: UserCheckpoint, context: Dict[str, Any]) -> bool:
        """Check if checkpoint should be triggered"""
        if cp.condition is None:
            return True
        return cp.condition(context)
    
    def should_halt_for_checkpoint(self, cp: UserCheckpoint) -> bool:
        """Check if checkpoint should halt execution"""
        return cp.mode in ["require_approval", "pause"]
    
    def emit_checkpoint_prompt(self, cp: UserCheckpoint, context: Dict[str, Any]) -> None:
        """Emit checkpoint prompt for human review"""
        print(f"CHECKPOINT: {cp.event} - {cp.mode}")
        
        # Create a serializable version of context
        serializable_context = {}
        for key, value in context.items():
            try:
                json.dumps(value)  # Test if serializable
                serializable_context[key] = value
            except (TypeError, ValueError):
                # Convert non-serializable objects to string representation
                if hasattr(value, '__dict__'):
                    serializable_context[key] = str(value.__class__.__name__)
                else:
                    serializable_context[key] = str(type(value).__name__)
        
        print(f"Context: {json.dumps(serializable_context, indent=2)}")
    
    def wait_for_approval_or_timeout(self, timeout: int) -> CheckpointDecision:
        """Wait for approval or timeout (simplified implementation)"""
        # In a real implementation, this would wait for user input
        # For now, we'll auto-approve after a short delay
        print(f"Waiting for approval (timeout: {timeout}s)...")
        time.sleep(1)  # Simulate brief wait
        return CheckpointDecision.APPROVED
    
    def queue_human_followups(self, result: Result) -> None:
        """Queue human follow-up tasks"""
        print(f"HUMAN FOLLOW-UP REQUIRED: {result.error}")
        # In a real implementation, this would add to a task queue
    
    def handle_failure(self, goal: GoalNode, result: Result) -> None:
        """Handle goal execution failure"""
        goal.status = 'failed'
        goal.meta['failure_reason'] = result.error
        goal.meta['failure_time'] = datetime.now().isoformat()
        print(f"Goal failed: {goal.objective} - {result.error}")
    
    def update_goal_tree(self, goal_tree: GoalTree, current_goal: GoalNode, result: Result) -> bool:
        """Update goal tree with execution results"""
        if result.status == ResultStatus.SUCCESS:
            current_goal.status = 'completed'
            goal_tree.completed_goals.append(current_goal)
            if current_goal in goal_tree.root_goals:
                goal_tree.root_goals.remove(current_goal)
            return True
        elif result.status == ResultStatus.FAILURE:
            current_goal.status = 'failed'
            goal_tree.failed_goals.append(current_goal)
            if current_goal in goal_tree.root_goals:
                goal_tree.root_goals.remove(current_goal)
        
        return False
    
    def has_exceeded_no_progress_window(self, last_progress_tick: float, timeout: timedelta) -> bool:
        """Check if no progress timeout has been exceeded"""
        return time.time() - last_progress_tick > timeout.total_seconds()
    
    async def execute_goal_loop(self, goal: GoalNode, framework: str, bounds: ResourceBounds, depth: int = 0) -> Result:
        """Execute goal loop (pseudocode: ExecuteGoalLoop)"""
        # Check depth limit
        if bounds.max_depth is not None and depth > bounds.max_depth:
            return Result.stop_and_wait("max_depth_exceeded", meta={"goal": goal.objective})
        
        # Planning Phase
        plan = await self.create_plan(goal)
        
        # User checkpoint on plan creation
        decision = self.evaluate_user_checkpoints("plan_created", {"goal": goal, "plan": plan}, 
                                                 bounds.user_checkpoints, bounds)
        if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
            return Result.stop_and_wait("checkpoint_halt_on_plan_created")
        
        # Information gathering if needed
        if not plan.is_well_defined():
            info_result = await self.gather_information(goal, plan)
            if info_result == "INSUFFICIENT":
                return Result.stop_and_wait("insufficient_information")
            plan = await self.update_plan(plan, info_result)
        
        # Complexity assessment and decomposition
        if await self.is_too_difficult(plan):
            subgoals = await self.decompose_plan(plan)
            for subgoal in subgoals:
                sub_result = await self.execute_goal_loop(subgoal, framework, bounds, depth + 1)
                sub_result = self.normalize_result(sub_result)
                if sub_result.status == ResultStatus.FAILURE:
                    return sub_result
                elif sub_result.status in [ResultStatus.STOP_AND_WAIT, ResultStatus.NEEDS_CLARIFICATION]:
                    return sub_result
            return Result.success()
        
        # Execution setup
        constraints = self.set_constraints(plan, bounds)
        tools = self.select_tools(plan, constraints)
        workflow = self.select_workflow(plan, framework)
        
        # Final validation
        if not await self.final_check(plan, constraints, tools, workflow):
            human_tasks = await self.emit_human_tasks(plan)
            return Result.needs_clarification(data=human_tasks)
        
        # Pre-execution checkpoint
        decision = self.evaluate_user_checkpoints("pre_execution", 
                                                 {"goal": goal, "plan": plan, "constraints": constraints},
                                                 bounds.user_checkpoints, bounds)
        if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
            return Result.stop_and_wait("checkpoint_halt_pre_execution")
        
        # Execution with retry logic
        retry_attempts = 0
        execution_result = await self.execute_plan(plan, tools, workflow, constraints)
        
        while self.is_transient_failure(execution_result) and retry_attempts < bounds.retry_limit:
            await self.backoff(retry_attempts, bounds.retry_backoff)
            retry_attempts += 1
            execution_result = await self.execute_plan(plan, tools, workflow, constraints)
        
        # Review phase
        review_result = await self.review_execution(execution_result, constraints)
        
        if review_result == "PASSED":
            await self.forward_dependencies(goal, execution_result)
            self.mark_goal_complete(goal)
            
            decision = self.evaluate_user_checkpoints("post_review_passed",
                                                     {"goal": goal, "execution_result": execution_result, "review_result": review_result},
                                                     bounds.user_checkpoints, bounds)
            if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
                return Result.stop_and_wait("checkpoint_halt_post_review")
            
            return Result.success(data=execution_result)
        else:
            root_cause = await self.analyze_failure(execution_result, review_result)
            adjusted_plan = await self.adjust_plan(plan, root_cause)
            
            if await self.is_still_too_difficult(adjusted_plan):
                return Result.needs_clarification(data=await self.decompose_plan(adjusted_plan))
            else:
                adjusted_result = await self.execute_plan(adjusted_plan, tools, workflow, constraints)
                return self.normalize_result(adjusted_result)
    
    async def create_plan(self, goal: GoalNode) -> Plan:
        """Create execution plan for goal"""
        try:
            # Try to use existing agent to create plan
            instructions = f"Create a detailed step-by-step plan to accomplish: {goal.objective}"
            agent = build_agent(instructions, AVAILABLE_TOOLS)
            
            from agents import Runner
            result = await Runner.run(agent, instructions)
            plan_text = getattr(result, "final_output", None) or str(result)
            
            # Parse plan into steps (simplified)
            steps = []
            for i, line in enumerate(plan_text.split('\n')):
                if line.strip() and not line.startswith('#'):
                    steps.append({
                        'step_number': i + 1,
                        'action': line.strip(),
                        'status': 'pending'
                    })
            
            return Plan(steps=steps, meta={'raw_plan': plan_text})
        except Exception as e:
            # Fallback plan creation without agents SDK
            print(f"Using fallback plan creation: {e}")
            
            # Create a simple plan based on the goal objective
            objective = goal.objective.lower()
            steps = []
            
            if "create" in objective and "file" in objective:
                steps = [
                    {'step_number': 1, 'action': 'Determine file name and location', 'status': 'pending'},
                    {'step_number': 2, 'action': 'Create the file with appropriate content', 'status': 'pending'},
                    {'step_number': 3, 'action': 'Verify file was created successfully', 'status': 'pending'}
                ]
            elif "write" in objective and "function" in objective:
                steps = [
                    {'step_number': 1, 'action': 'Define function signature and parameters', 'status': 'pending'},
                    {'step_number': 2, 'action': 'Implement function logic', 'status': 'pending'},
                    {'step_number': 3, 'action': 'Test function works correctly', 'status': 'pending'}
                ]
            else:
                # Generic plan
                steps = [
                    {'step_number': 1, 'action': f'Analyze requirements for: {goal.objective}', 'status': 'pending'},
                    {'step_number': 2, 'action': f'Execute main task: {goal.objective}', 'status': 'pending'},
                    {'step_number': 3, 'action': f'Verify completion of: {goal.objective}', 'status': 'pending'}
                ]
            
            return Plan(steps=steps, meta={'fallback': True, 'error': str(e)})
    
    async def gather_information(self, goal: GoalNode, plan: Plan) -> str:
        """Gather additional information if plan is under-specified"""
        # Simplified information gathering
        return "SUFFICIENT"  # For now, assume we have enough info
    
    async def update_plan(self, plan: Plan, info_result: str) -> Plan:
        """Update plan with gathered information"""
        # Simplified plan update
        return plan
    
    async def is_too_difficult(self, plan: Plan) -> bool:
        """Check if plan is too difficult for direct execution"""
        # Simple heuristic: if plan has more than 10 steps, decompose
        return len(plan.steps) > 10
    
    async def decompose_plan(self, plan: Plan) -> List[GoalNode]:
        """Decompose complex plan into subgoals"""
        subgoals = []
        for i, step in enumerate(plan.steps):
            subgoal = GoalNode(
                objective=step['action'],
                priority=i,
                meta={'parent_plan': plan.meta}
            )
            subgoals.append(subgoal)
        return subgoals
    
    def set_constraints(self, plan: Plan, bounds: ResourceBounds) -> ResourceBounds:
        """Set execution constraints for plan"""
        # Copy bounds and add plan-specific constraints
        constraints = ResourceBounds(
            max_iterations=bounds.max_iterations,
            max_depth=bounds.max_depth,
            time_limit=bounds.time_limit,
            cost_limit=bounds.cost_limit,
            token_limit=bounds.token_limit,
            user_checkpoints=bounds.user_checkpoints,
            tool_permissions=bounds.tool_permissions.copy(),
            enable_dry_runs=bounds.enable_dry_runs
        )
        return constraints
    
    def select_tools(self, plan: Plan, constraints: ResourceBounds) -> List[Any]:
        """Select appropriate tools for plan execution"""
        return AVAILABLE_TOOLS  # Use all available tools for now
    
    def select_workflow(self, plan: Plan, framework: str) -> str:
        """Select execution workflow based on framework"""
        return framework
    
    async def final_check(self, plan: Plan, constraints: ResourceBounds, tools: List[Any], workflow: str) -> bool:
        """Perform final validation before execution"""
        # Basic validation checks
        if not plan.steps:
            return False
        
        # Check tool permissions
        for step in plan.steps:
            if not self.has_tool_permission_for_step(step, constraints.tool_permissions):
                return False
        
        return True
    
    def has_tool_permission_for_step(self, step: Dict[str, Any], permissions: Dict[str, bool]) -> bool:
        """Check if step has required tool permissions"""
        # Simplified permission check
        return True  # Allow all for now
    
    async def emit_human_tasks(self, plan: Plan) -> List[Dict[str, Any]]:
        """Emit human tasks for manual intervention"""
        return [{"task": "Review and approve plan", "plan": plan.steps}]
    
    async def execute_plan(self, plan: Plan, tools: List[Any], workflow: str, constraints: ResourceBounds) -> Dict[str, Any]:
        """Execute the plan with tools and workflow"""
        results = []
        
        for step in plan.steps:
            # Pre-step checkpoint
            decision = self.evaluate_user_checkpoints("before_step", 
                                                     {"plan": plan, "step": step},
                                                     constraints.user_checkpoints, constraints)
            if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
                return {"status": "FAILURE", "error": "checkpoint_halt_before_step"}
            
            # Execute step
            step_result = await self.execute_step(step, tools, constraints)
            results.append(step_result)
            
            # Post-step checkpoint
            decision = self.evaluate_user_checkpoints("after_step",
                                                     {"plan": plan, "step": step, "step_result": step_result},
                                                     constraints.user_checkpoints, constraints)
            if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
                return {"status": "FAILURE", "error": "checkpoint_halt_after_step"}
        
        return {"status": "SUCCESS", "results": results}
    
    async def execute_step(self, step: Dict[str, Any], tools: List[Any], constraints: ResourceBounds) -> Dict[str, Any]:
        """Execute a single step"""
        try:
            action = step.get('action', '')
            print(f"  Executing step: {action}")
            
            try:
                # Try to use agent to execute the step
                instructions = f"Execute this step: {action}"
                agent = build_agent(instructions, tools)
                
                from agents import Runner
                result = await Runner.run(agent, instructions)
                output = getattr(result, "final_output", None) or str(result)
                
                return {
                    "status": "SUCCESS",
                    "output": output,
                    "step": step
                }
            except Exception as agent_error:
                # Fallback execution without agents SDK
                print(f"  Using fallback execution: {agent_error}")
                
                # Simulate step execution based on action content
                action_lower = action.lower()
                
                if "determine" in action_lower and "file" in action_lower:
                    output = "Determined file should be 'test_file.txt' in current directory"
                elif "create" in action_lower and "file" in action_lower:
                    # Actually create a simple test file
                    try:
                        with open("test_file.txt", "w") as f:
                            f.write("Hello World!\nThis is a test file created by the main solving loop.\n")
                        output = "Successfully created test_file.txt"
                    except Exception as file_error:
                        return {
                            "status": "FAILURE",
                            "error": f"Failed to create file: {file_error}",
                            "step": step
                        }
                elif "verify" in action_lower and "file" in action_lower:
                    # Check if file exists
                    import os
                    if os.path.exists("test_file.txt"):
                        output = "File verification successful - test_file.txt exists"
                    else:
                        output = "File verification failed - test_file.txt not found"
                elif "define" in action_lower and "function" in action_lower:
                    output = "Defined function signature: def hello_world() -> str"
                elif "implement" in action_lower and "function" in action_lower:
                    # Create a simple Python file with hello world function
                    try:
                        with open("hello_world.py", "w") as f:
                            f.write("""def hello_world() -> str:
    \"\"\"Return a hello world greeting.\"\"\"
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
""")
                        output = "Successfully implemented hello_world function in hello_world.py"
                    except Exception as func_error:
                        return {
                            "status": "FAILURE",
                            "error": f"Failed to implement function: {func_error}",
                            "step": step
                        }
                elif "test" in action_lower and "function" in action_lower:
                    # Test the function
                    try:
                        import subprocess
                        result = subprocess.run(["python3", "hello_world.py"], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            output = f"Function test successful: {result.stdout.strip()}"
                        else:
                            output = f"Function test failed: {result.stderr}"
                    except Exception as test_error:
                        output = f"Function test error: {test_error}"
                else:
                    # Generic fallback
                    output = f"Simulated execution of: {action}"
                
                return {
                    "status": "SUCCESS",
                    "output": output,
                    "step": step,
                    "fallback": True
                }
                
        except Exception as e:
            return {
                "status": "FAILURE",
                "error": str(e),
                "step": step
            }
    
    def is_transient_failure(self, execution_result: Dict[str, Any]) -> bool:
        """Check if execution failure is transient"""
        if execution_result.get("status") != "FAILURE":
            return False
        
        error = execution_result.get("error", "").lower()
        transient_errors = ["rate_limited", "timeout", "network_error", "temporary"]
        return any(te in error for te in transient_errors)
    
    async def backoff(self, retry_attempts: int, backoff_factor: float) -> None:
        """Implement exponential backoff"""
        delay = backoff_factor * (2 ** retry_attempts)
        await asyncio.sleep(delay)
    
    async def review_execution(self, execution_result: Dict[str, Any], constraints: ResourceBounds) -> str:
        """Review execution results"""
        if execution_result.get("status") == "SUCCESS":
            return "PASSED"
        else:
            return "FAILED"
    
    async def forward_dependencies(self, goal: GoalNode, execution_result: Dict[str, Any]) -> None:
        """Forward results to dependent goals"""
        # Simplified dependency forwarding
        pass
    
    def mark_goal_complete(self, goal: GoalNode) -> None:
        """Mark goal as complete"""
        goal.status = 'completed'
        goal.meta['completion_time'] = datetime.now().isoformat()
    
    async def analyze_failure(self, execution_result: Dict[str, Any], review_result: str) -> Dict[str, Any]:
        """Analyze failure root cause"""
        return {
            "root_cause": execution_result.get("error", "unknown"),
            "review_result": review_result
        }
    
    async def adjust_plan(self, plan: Plan, root_cause: Dict[str, Any]) -> Plan:
        """Adjust plan based on failure analysis"""
        # Simplified plan adjustment
        return plan
    
    async def is_still_too_difficult(self, adjusted_plan: Plan) -> bool:
        """Check if adjusted plan is still too difficult"""
        return await self.is_too_difficult(adjusted_plan)
    
    def final_status(self, goal_tree: GoalTree, resource_bounds: ResourceBounds, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final status report"""
        return {
            "completed_goals": len(goal_tree.completed_goals),
            "failed_goals": len(goal_tree.failed_goals),
            "remaining_goals": len(goal_tree.root_goals),
            "resource_usage": self.current_usage,
            "telemetry": telemetry
        }
    
    async def main_solving_loop(self, user_objectives: List[str], 
                              org_policy: Dict[str, Any] = None,
                              cost_limits: float = 100.0,
                              time_limits: timedelta = timedelta(hours=1),
                              sensitivity_levels: str = "MEDIUM",
                              user_checkpoints: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main solving loop implementation (pseudocode: MainSolvingLoop)"""
        
        # Phase 1: Initialization
        framework = self.select_agent_framework("MEDIUM", False, sensitivity_levels, "local")
        goal_tree = self.construct_goal_tree(user_objectives)
        resource_bounds = self.assign_resource_bounds(org_policy or {}, cost_limits, time_limits, sensitivity_levels)
        
        # Register user checkpoints
        if user_checkpoints:
            resource_bounds.user_checkpoints = self.register_user_checkpoints(user_checkpoints, resource_bounds)
        
        iteration_count = 0
        last_progress_tick = time.time()
        max_iterations = resource_bounds.max_iterations
        
        print(f"Starting main solving loop with {len(goal_tree.root_goals)} goals")
        print(f"Framework: {framework}")
        print(f"Resource bounds: max_iterations={max_iterations}, time_limit={resource_bounds.time_limit}")
        
        # Phase 2: Main execution loop
        while self.has_remaining_goals(goal_tree):
            start_time = time.time()
            self.current_usage['iterations'] = iteration_count
            self.current_usage['time_elapsed'] = start_time - last_progress_tick
            
            self.manage_resource_bounds(resource_bounds, self.current_usage)
            
            if self.check_stop_conditions({}, resource_bounds):
                print("Stop conditions met, breaking loop")
                break
            
            if max_iterations is not None and iteration_count >= max_iterations:
                self.escalate("max_iterations_reached")
                break
            
            # User checkpoint at loop iteration start
            decision = self.evaluate_user_checkpoints("loop_iteration_start",
                                                     {"goal_tree": goal_tree, "iteration_count": iteration_count},
                                                     resource_bounds.user_checkpoints, resource_bounds)
            if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
                break
            
            current_goal = self.select_next_goal(goal_tree)
            
            if current_goal is None:
                print("No more executable goals found")
                break
            
            print(f"Iteration {iteration_count}: Executing goal - {current_goal.objective}")
            
            # User checkpoint on goal selection
            decision = self.evaluate_user_checkpoints("goal_selected", {"current_goal": current_goal},
                                                     resource_bounds.user_checkpoints, resource_bounds)
            if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
                break
            
            current_goal.status = 'in_progress'
            result = await self.execute_goal_loop(current_goal, framework, resource_bounds, 0)
            result = self.normalize_result(result)
            
            if result.status == ResultStatus.STOP_AND_WAIT or result.status == ResultStatus.NEEDS_CLARIFICATION:
                self.queue_human_followups(result)
                break
            elif result.status == ResultStatus.FAILURE:
                self.handle_failure(current_goal, result)
                if self.check_stop_conditions({}, resource_bounds):
                    break
            
            # User checkpoint after goal execution
            decision = self.evaluate_user_checkpoints("after_goal_execution",
                                                     {"current_goal": current_goal, "result": result},
                                                     resource_bounds.user_checkpoints, resource_bounds)
            if decision in [CheckpointDecision.REJECTED, CheckpointDecision.TIMEOUT]:
                break
            
            progress_made = self.update_goal_tree(goal_tree, current_goal, result)
            if progress_made:
                last_progress_tick = time.time()
            elif self.has_exceeded_no_progress_window(last_progress_tick, resource_bounds.no_progress_timeout):
                self.escalate("no_progress")
                break
            
            iteration_count += 1
            print(f"Completed iteration {iteration_count}, progress_made: {progress_made}")
        
        # Generate final status
        telemetry_snapshot = {"iterations": iteration_count, "final_time": time.time()}
        final_status = self.final_status(goal_tree, resource_bounds, telemetry_snapshot)
        
        print("Main solving loop completed")
        print(f"Final status: {json.dumps(final_status, indent=2)}")
        
        return final_status


async def main():
    """Main entry point"""
    # Get objectives from environment or use defaults
    objectives_str = os.environ.get("MAIN_SOLVER_OBJECTIVES", "Implement example feature end-to-end")
    objectives = [obj.strip() for obj in objectives_str.split(",")]
    
    # Example user checkpoints configuration
    user_checkpoints = [
        {
            "event": "loop_iteration_start",
            "mode": "require_approval",
            "timeout": 300
        },
        {
            "event": "goal_selected", 
            "mode": "require_approval"
        },
        {
            "event": "pre_execution",
            "mode": "pause"
        }
    ]
    
    # Create and run main solving loop
    solver = MainSolvingLoop()
    
    try:
        result = await solver.main_solving_loop(
            user_objectives=objectives,
            org_policy={"max_iterations": 50, "max_depth": 5},
            cost_limits=100.0,
            time_limits=timedelta(hours=2),
            sensitivity_levels="MEDIUM",
            user_checkpoints=user_checkpoints
        )
        
        print("\n" + "="*50)
        print("MAIN SOLVING LOOP COMPLETED")
        print("="*50)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error in main solving loop: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())