"""Resource bounds and checkpoint management for the main solving loop."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from src.config import settings


class CheckpointDecision(Enum):
    """Possible decisions from checkpoint evaluation."""
    CONTINUE = "continue"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    PAUSE = "pause"


class EscalationReason(Enum):
    """Reasons for escalation."""
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    NO_PROGRESS = "no_progress"
    COST_LIMIT_EXCEEDED = "cost_limit_exceeded"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"
    SAFETY_VIOLATION = "safety_violation"
    USER_REQUESTED = "user_requested"


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""
    iterations: int = 0
    depth: int = 0
    cost: float = 0.0  # USD
    tokens: int = 0
    start_time: float = field(default_factory=time.time)
    last_progress_time: float = field(default_factory=time.time)
    
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def time_since_progress(self) -> float:
        """Get time since last progress in seconds."""
        return time.time() - self.last_progress_time
    
    def update_progress(self) -> None:
        """Update the last progress timestamp."""
        self.last_progress_time = time.time()


@dataclass
class UserCheckpoint:
    """User-defined checkpoint configuration."""
    id: str = field(default_factory=lambda: str(uuid4()))
    event: str = ""  # Event name to trigger on
    mode: str = "continue"  # "continue", "require_approval", "pause"
    condition: Optional[str] = None  # Python expression to evaluate
    timeout: Optional[int] = None  # Timeout in seconds
    description: str = ""
    enabled: bool = True
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """Check if this checkpoint should trigger given the context."""
        if not self.enabled:
            return False
        
        if not self.condition:
            return True
        
        try:
            # Safely evaluate the condition
            # In production, this should use a restricted evaluator
            return eval(self.condition, {"__builtins__": {}}, context)
        except Exception:
            return False
    
    def should_halt(self) -> bool:
        """Check if this checkpoint should halt execution."""
        return self.mode in ["require_approval", "pause"]


@dataclass
class ResourceBounds:
    """Resource bounds and constraints for execution."""
    # Iteration limits
    max_iterations: Optional[int] = None
    max_depth: Optional[int] = None
    
    # Resource limits
    cost_limit: Optional[float] = None  # USD
    time_limit: Optional[int] = None  # seconds
    token_limit: Optional[int] = None
    
    # Retry configuration
    retry_limit: int = 3
    retry_backoff: float = 1.0  # seconds
    
    # Progress tracking
    no_progress_timeout: int = 300  # seconds
    
    # Approval and checkpoint configuration
    approval_timeout: int = 300  # seconds
    user_checkpoints: List[UserCheckpoint] = field(default_factory=list)
    
    # Safety configuration
    enable_dry_runs: bool = True
    enable_rollback: bool = True
    sandbox_mode: bool = True
    
    # Tool permissions
    tool_permissions: List[str] = field(default_factory=list)
    
    # Escalation rules
    escalation_rules: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_settings(cls) -> "ResourceBounds":
        """Create resource bounds from application settings."""
        return cls(
            max_iterations=settings.max_iterations,
            max_depth=settings.max_depth,
            cost_limit=settings.cost_limit,
            time_limit=settings.time_limit,
            token_limit=settings.token_limit,
            retry_limit=settings.retry_limit,
            retry_backoff=settings.retry_backoff,
            no_progress_timeout=settings.no_progress_timeout,
            approval_timeout=settings.approval_timeout,
            enable_dry_runs=settings.enable_dry_runs,
            enable_rollback=settings.enable_rollback,
            sandbox_mode=settings.sandbox_mode,
            tool_permissions=["echo", "list_goals", "emit_summary"],  # Default safe tools
            escalation_rules={
                "cost_spike_threshold": 2.0,  # 2x expected cost
                "time_spike_threshold": 1.5,  # 1.5x expected time
                "auto_halt_conditions": ["low_confidence", "safety_violation"]
            }
        )


class ResourceManager:
    """Manages resource usage and bounds checking."""
    
    def __init__(self, bounds: ResourceBounds):
        self.bounds = bounds
        self.usage = ResourceUsage()
        self.escalations: List[Dict[str, Any]] = []
        self.approval_queue: List[Dict[str, Any]] = []
    
    def check_stop_conditions(self, current_state: Dict[str, Any]) -> bool:
        """Check if any stop conditions are met."""
        # Check iteration limits
        if (self.bounds.max_iterations is not None and 
            self.usage.iterations >= self.bounds.max_iterations):
            self.escalate(EscalationReason.MAX_ITERATIONS_REACHED)
            return True
        
        # Check resource limits
        if (self.bounds.cost_limit is not None and 
            self.usage.cost >= self.bounds.cost_limit):
            self.escalate(EscalationReason.COST_LIMIT_EXCEEDED)
            return True
        
        if (self.bounds.time_limit is not None and 
            self.usage.elapsed_time() >= self.bounds.time_limit):
            self.escalate(EscalationReason.TIME_LIMIT_EXCEEDED)
            return True
        
        if (self.bounds.token_limit is not None and 
            self.usage.tokens >= self.bounds.token_limit):
            self.escalate(EscalationReason.TOKEN_LIMIT_EXCEEDED)
            return True
        
        # Check progress timeout
        if self.usage.time_since_progress() >= self.bounds.no_progress_timeout:
            self.escalate(EscalationReason.NO_PROGRESS)
            return True
        
        # Check custom stop conditions
        if self._check_custom_stop_conditions(current_state):
            return True
        
        return False
    
    def _check_custom_stop_conditions(self, current_state: Dict[str, Any]) -> bool:
        """Check custom stop conditions from escalation rules."""
        auto_halt_conditions = self.bounds.escalation_rules.get("auto_halt_conditions", [])
        
        for condition in auto_halt_conditions:
            if condition == "low_confidence":
                confidence = current_state.get("confidence", 1.0)
                if confidence < 0.5:
                    self.escalate(EscalationReason.SAFETY_VIOLATION, 
                                {"reason": "low_confidence", "confidence": confidence})
                    return True
            
            elif condition == "safety_violation":
                if current_state.get("safety_violation", False):
                    self.escalate(EscalationReason.SAFETY_VIOLATION,
                                {"reason": "safety_violation_detected"})
                    return True
        
        return False
    
    def manage_resource_bounds(self, current_usage: Dict[str, Any]) -> None:
        """Update resource usage and check for violations."""
        # Update usage tracking
        self.usage.iterations = current_usage.get("iterations", self.usage.iterations)
        self.usage.depth = current_usage.get("depth", self.usage.depth)
        self.usage.cost = current_usage.get("cost", self.usage.cost)
        self.usage.tokens = current_usage.get("tokens", self.usage.tokens)
        
        # Check for resource spikes
        self._check_resource_spikes(current_usage)
    
    def _check_resource_spikes(self, current_usage: Dict[str, Any]) -> None:
        """Check for unexpected resource usage spikes."""
        expected_cost = current_usage.get("expected_cost", 0)
        if expected_cost > 0:
            cost_ratio = self.usage.cost / expected_cost
            threshold = self.bounds.escalation_rules.get("cost_spike_threshold", 2.0)
            if cost_ratio > threshold:
                self.escalate(EscalationReason.COST_LIMIT_EXCEEDED,
                            {"reason": "cost_spike", "ratio": cost_ratio})
        
        expected_time = current_usage.get("expected_time", 0)
        if expected_time > 0:
            time_ratio = self.usage.elapsed_time() / expected_time
            threshold = self.bounds.escalation_rules.get("time_spike_threshold", 1.5)
            if time_ratio > threshold:
                self.escalate(EscalationReason.TIME_LIMIT_EXCEEDED,
                            {"reason": "time_spike", "ratio": time_ratio})
    
    def escalate(self, reason: EscalationReason, details: Optional[Dict[str, Any]] = None) -> None:
        """Record an escalation event."""
        escalation = {
            "reason": reason.value,
            "timestamp": time.time(),
            "usage": {
                "iterations": self.usage.iterations,
                "depth": self.usage.depth,
                "cost": self.usage.cost,
                "tokens": self.usage.tokens,
                "elapsed_time": self.usage.elapsed_time()
            },
            "details": details or {}
        }
        self.escalations.append(escalation)
    
    def evaluate_user_checkpoints(self, event: str, context: Dict[str, Any]) -> CheckpointDecision:
        """Evaluate user-defined checkpoints for an event."""
        if not self.bounds.user_checkpoints:
            return CheckpointDecision.CONTINUE
        
        # Find matching checkpoints
        matching_checkpoints = [
            cp for cp in self.bounds.user_checkpoints 
            if cp.event == event and cp.should_trigger(context)
        ]
        
        if not matching_checkpoints:
            return CheckpointDecision.CONTINUE
        
        # Process checkpoints that require halting
        halt_checkpoints = [cp for cp in matching_checkpoints if cp.should_halt()]
        
        if halt_checkpoints:
            # Emit checkpoint prompts
            for cp in halt_checkpoints:
                self._emit_checkpoint_prompt(cp, context)
            
            # Wait for approval if required
            if any(cp.mode == "require_approval" for cp in halt_checkpoints):
                return self._wait_for_approval_or_timeout()
            else:
                return CheckpointDecision.PAUSE
        
        # Process non-halting checkpoints
        for cp in matching_checkpoints:
            self._emit_checkpoint_prompt(cp, context)
        
        return CheckpointDecision.CONTINUE
    
    def _emit_checkpoint_prompt(self, checkpoint: UserCheckpoint, context: Dict[str, Any]) -> None:
        """Emit a checkpoint prompt for human review."""
        prompt = {
            "type": "checkpoint",
            "checkpoint_id": checkpoint.id,
            "event": checkpoint.event,
            "description": checkpoint.description,
            "context": context,
            "timestamp": time.time(),
            "mode": checkpoint.mode
        }
        self.approval_queue.append(prompt)
    
    def _wait_for_approval_or_timeout(self) -> CheckpointDecision:
        """Wait for approval or timeout."""
        # In a real implementation, this would integrate with a UI or notification system
        # For now, we simulate immediate approval for non-blocking operation
        timeout = self.bounds.approval_timeout
        
        # Simulate waiting (in practice, this would be async)
        # For demo purposes, we'll return APPROVED to continue execution
        return CheckpointDecision.APPROVED
    
    def has_tool_permission(self, tool_name: str) -> bool:
        """Check if a tool is permitted for use."""
        if not self.bounds.tool_permissions:
            return True  # No restrictions
        return tool_name in self.bounds.tool_permissions
    
    def add_tool_permission(self, tool_name: str) -> None:
        """Add a tool permission."""
        if tool_name not in self.bounds.tool_permissions:
            self.bounds.tool_permissions.append(tool_name)
    
    def remove_tool_permission(self, tool_name: str) -> None:
        """Remove a tool permission."""
        if tool_name in self.bounds.tool_permissions:
            self.bounds.tool_permissions.remove(tool_name)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of current resource usage."""
        return {
            "iterations": self.usage.iterations,
            "depth": self.usage.depth,
            "cost": self.usage.cost,
            "tokens": self.usage.tokens,
            "elapsed_time": self.usage.elapsed_time(),
            "time_since_progress": self.usage.time_since_progress(),
            "escalations": len(self.escalations),
            "pending_approvals": len(self.approval_queue)
        }


def register_user_checkpoints(user_defs: Optional[List[Dict[str, Any]]], 
                            bounds: ResourceBounds) -> List[UserCheckpoint]:
    """Register user-defined checkpoints."""
    if not user_defs:
        return []
    
    checkpoints = []
    for user_def in user_defs:
        checkpoint = UserCheckpoint(
            event=user_def.get("event", ""),
            mode=user_def.get("mode", "continue"),
            condition=user_def.get("condition"),
            timeout=user_def.get("timeout"),
            description=user_def.get("description", ""),
            enabled=user_def.get("enabled", True)
        )
        checkpoints.append(checkpoint)
    
    return checkpoints


def create_default_checkpoints() -> List[UserCheckpoint]:
    """Create default checkpoint configuration."""
    return [
        UserCheckpoint(
            event="loop_iteration_start",
            mode="require_approval",
            condition="ctx.get('iteration_count', 0) > 20",
            timeout=300,
            description="High iteration count reached"
        ),
        UserCheckpoint(
            event="goal_selected",
            mode="require_approval",
            condition="ctx.get('current_goal', {}).get('priority', 0) >= 4",
            description="Critical priority goal selected"
        ),
        UserCheckpoint(
            event="before_step",
            mode="pause",
            condition="'external' in ctx.get('step', {}).get('type', '')",
            description="External action about to be performed"
        ),
        UserCheckpoint(
            event="after_step",
            mode="require_approval",
            condition="ctx.get('step_result', {}).get('risk_level', 0) > 0.7",
            timeout=120,
            description="High-risk step result detected"
        )
    ]