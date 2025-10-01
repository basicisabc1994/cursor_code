"""Goal tree management for the main solving loop."""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4


class GoalStatus(Enum):
    """Status of a goal in the tree."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class GoalPriority(Enum):
    """Priority levels for goals."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AcceptanceCriteria:
    """Acceptance criteria for a goal."""
    description: str
    test_function: Optional[str] = None  # Python code to evaluate
    validation_rules: List[str] = field(default_factory=list)
    success_threshold: float = 1.0  # 0.0 to 1.0


@dataclass
class GoalNode:
    """A node in the goal tree."""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    status: GoalStatus = GoalStatus.PENDING
    priority: GoalPriority = GoalPriority.MEDIUM
    
    # Tree structure
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Goal IDs this depends on
    
    # Execution details
    acceptance_criteria: List[AcceptanceCriteria] = field(default_factory=list)
    estimated_effort: Optional[float] = None  # hours
    actual_effort: Optional[float] = None  # hours
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Execution results
    execution_results: List[Dict[str, Any]] = field(default_factory=list)
    failure_reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "dependencies": self.dependencies,
            "acceptance_criteria": [
                {
                    "description": ac.description,
                    "test_function": ac.test_function,
                    "validation_rules": ac.validation_rules,
                    "success_threshold": ac.success_threshold
                }
                for ac in self.acceptance_criteria
            ],
            "estimated_effort": self.estimated_effort,
            "actual_effort": self.actual_effort,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "tags": self.tags,
            "metadata": self.metadata,
            "execution_results": self.execution_results,
            "failure_reasons": self.failure_reasons
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalNode":
        """Create from dictionary."""
        node = cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=GoalStatus(data["status"]),
            priority=GoalPriority(data["priority"]),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            dependencies=data.get("dependencies", []),
            estimated_effort=data.get("estimated_effort"),
            actual_effort=data.get("actual_effort"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            completed_at=data.get("completed_at"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            execution_results=data.get("execution_results", []),
            failure_reasons=data.get("failure_reasons", [])
        )
        
        # Reconstruct acceptance criteria
        for ac_data in data.get("acceptance_criteria", []):
            ac = AcceptanceCriteria(
                description=ac_data["description"],
                test_function=ac_data.get("test_function"),
                validation_rules=ac_data.get("validation_rules", []),
                success_threshold=ac_data.get("success_threshold", 1.0)
            )
            node.acceptance_criteria.append(ac)
        
        return node


class GoalTree:
    """Manages a tree of goals with dependencies and execution tracking."""
    
    def __init__(self):
        self.nodes: Dict[str, GoalNode] = {}
        self.root_ids: List[str] = []
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def add_goal(self, goal: GoalNode, parent_id: Optional[str] = None) -> str:
        """Add a goal to the tree."""
        if parent_id:
            if parent_id not in self.nodes:
                raise ValueError(f"Parent goal {parent_id} not found")
            goal.parent_id = parent_id
            self.nodes[parent_id].children_ids.append(goal.id)
        else:
            self.root_ids.append(goal.id)
        
        self.nodes[goal.id] = goal
        self.updated_at = time.time()
        return goal.id
    
    def get_goal(self, goal_id: str) -> Optional[GoalNode]:
        """Get a goal by ID."""
        return self.nodes.get(goal_id)
    
    def update_goal_status(self, goal_id: str, status: GoalStatus) -> None:
        """Update the status of a goal."""
        if goal_id not in self.nodes:
            raise ValueError(f"Goal {goal_id} not found")
        
        goal = self.nodes[goal_id]
        goal.status = status
        goal.updated_at = time.time()
        
        if status == GoalStatus.COMPLETED:
            goal.completed_at = time.time()
        
        self.updated_at = time.time()
    
    def get_ready_goals(self) -> List[GoalNode]:
        """Get goals that are ready to be executed (dependencies satisfied)."""
        ready_goals = []
        
        for goal in self.nodes.values():
            if goal.status != GoalStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            dependencies_satisfied = True
            for dep_id in goal.dependencies:
                dep_goal = self.nodes.get(dep_id)
                if not dep_goal or dep_goal.status != GoalStatus.COMPLETED:
                    dependencies_satisfied = False
                    break
            
            if dependencies_satisfied:
                ready_goals.append(goal)
        
        # Sort by priority (highest first)
        ready_goals.sort(key=lambda g: g.priority.value, reverse=True)
        return ready_goals
    
    def get_blocked_goals(self) -> List[GoalNode]:
        """Get goals that are blocked by failed dependencies."""
        blocked_goals = []
        
        for goal in self.nodes.values():
            if goal.status not in [GoalStatus.PENDING, GoalStatus.BLOCKED]:
                continue
            
            # Check if any dependencies have failed
            has_failed_dependency = False
            for dep_id in goal.dependencies:
                dep_goal = self.nodes.get(dep_id)
                if dep_goal and dep_goal.status == GoalStatus.FAILED:
                    has_failed_dependency = True
                    break
            
            if has_failed_dependency:
                goal.status = GoalStatus.BLOCKED
                blocked_goals.append(goal)
        
        return blocked_goals
    
    def has_remaining_goals(self) -> bool:
        """Check if there are any goals that haven't been completed or failed."""
        for goal in self.nodes.values():
            if goal.status in [GoalStatus.PENDING, GoalStatus.IN_PROGRESS]:
                return True
        return False
    
    def get_completion_stats(self) -> Dict[str, int]:
        """Get completion statistics."""
        stats = {status.value: 0 for status in GoalStatus}
        for goal in self.nodes.values():
            stats[goal.status.value] += 1
        return stats
    
    def select_next_goal(self, feasibility_criteria: Optional[Dict[str, Any]] = None) -> Optional[GoalNode]:
        """Select the next goal to execute based on priority and feasibility."""
        ready_goals = self.get_ready_goals()
        
        if not ready_goals:
            return None
        
        # Apply feasibility criteria if provided
        if feasibility_criteria:
            feasible_goals = []
            for goal in ready_goals:
                if self._is_feasible(goal, feasibility_criteria):
                    feasible_goals.append(goal)
            ready_goals = feasible_goals
        
        return ready_goals[0] if ready_goals else None
    
    def _is_feasible(self, goal: GoalNode, criteria: Dict[str, Any]) -> bool:
        """Check if a goal meets feasibility criteria."""
        # Example feasibility checks
        max_effort = criteria.get("max_effort")
        if max_effort and goal.estimated_effort and goal.estimated_effort > max_effort:
            return False
        
        required_tags = criteria.get("required_tags", [])
        if required_tags and not any(tag in goal.tags for tag in required_tags):
            return False
        
        excluded_tags = criteria.get("excluded_tags", [])
        if excluded_tags and any(tag in goal.tags for tag in excluded_tags):
            return False
        
        return True
    
    def add_execution_result(self, goal_id: str, result: Dict[str, Any]) -> None:
        """Add an execution result to a goal."""
        if goal_id not in self.nodes:
            raise ValueError(f"Goal {goal_id} not found")
        
        goal = self.nodes[goal_id]
        goal.execution_results.append(result)
        goal.updated_at = time.time()
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tree to dictionary for serialization."""
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "root_ids": self.root_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalTree":
        """Create tree from dictionary."""
        tree = cls()
        tree.root_ids = data.get("root_ids", [])
        tree.created_at = data.get("created_at", time.time())
        tree.updated_at = data.get("updated_at", time.time())
        
        # Reconstruct nodes
        for node_id, node_data in data.get("nodes", {}).items():
            node = GoalNode.from_dict(node_data)
            tree.nodes[node_id] = node
        
        return tree
    
    def save_to_file(self, filepath: str) -> None:
        """Save tree to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "GoalTree":
        """Load tree from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def construct_goal_tree(objectives: List[str], inferred_subgoals: Optional[List[Dict[str, Any]]] = None) -> GoalTree:
    """Construct a goal tree from objectives and inferred subgoals."""
    tree = GoalTree()
    
    # Create root goals from objectives
    for i, objective in enumerate(objectives):
        goal = GoalNode(
            title=f"Objective {i+1}",
            description=objective,
            priority=GoalPriority.HIGH,
            tags=["objective", "root"]
        )
        
        # Add basic acceptance criteria
        criteria = AcceptanceCriteria(
            description=f"Successfully complete: {objective}",
            success_threshold=0.8
        )
        goal.acceptance_criteria.append(criteria)
        
        tree.add_goal(goal)
    
    # Add inferred subgoals if provided
    if inferred_subgoals:
        for subgoal_data in inferred_subgoals:
            subgoal = GoalNode(
                title=subgoal_data.get("title", "Subgoal"),
                description=subgoal_data.get("description", ""),
                priority=GoalPriority(subgoal_data.get("priority", 2)),
                tags=subgoal_data.get("tags", ["subgoal"])
            )
            
            parent_id = subgoal_data.get("parent_id")
            dependencies = subgoal_data.get("dependencies", [])
            subgoal.dependencies = dependencies
            
            tree.add_goal(subgoal, parent_id)
    
    return tree


def infer_dependencies(objective: str, subgoals: List[Dict[str, Any]]) -> List[str]:
    """Infer dependencies between goals based on content analysis."""
    # This is a simplified implementation
    # In practice, this would use NLP or LLM analysis
    dependencies = []
    
    # Simple keyword-based dependency inference
    setup_keywords = ["setup", "install", "configure", "initialize"]
    if any(keyword in objective.lower() for keyword in setup_keywords):
        # Setup tasks typically come first
        dependencies = []
    else:
        # Other tasks might depend on setup tasks
        for subgoal in subgoals:
            if any(keyword in subgoal.get("description", "").lower() for keyword in setup_keywords):
                dependencies.append(subgoal.get("id", ""))
    
    return [dep for dep in dependencies if dep]


def define_acceptance_criteria(objective: str) -> List[AcceptanceCriteria]:
    """Define acceptance criteria for an objective."""
    criteria = []
    
    # Basic completion criteria
    criteria.append(AcceptanceCriteria(
        description=f"Objective completed: {objective}",
        success_threshold=0.8
    ))
    
    # Add specific criteria based on objective type
    if "test" in objective.lower():
        criteria.append(AcceptanceCriteria(
            description="All tests pass",
            validation_rules=["test_results.passed >= test_results.total * 0.95"],
            success_threshold=0.95
        ))
    
    if "deploy" in objective.lower():
        criteria.append(AcceptanceCriteria(
            description="Deployment successful and accessible",
            validation_rules=["deployment.status == 'active'", "health_check.status == 'healthy'"],
            success_threshold=1.0
        ))
    
    if "implement" in objective.lower():
        criteria.append(AcceptanceCriteria(
            description="Implementation complete and functional",
            validation_rules=["code_quality.score >= 0.8", "functionality_tests.passed == True"],
            success_threshold=0.9
        ))
    
    return criteria