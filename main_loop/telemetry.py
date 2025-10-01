"""Telemetry collection and learning subsystem for the main solving loop."""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.config import settings


@dataclass
class TelemetryEvent:
    """A single telemetry event."""
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: float = field(default_factory=time.time)
    event_type: str = ""
    session_id: str = ""
    
    # Event data
    step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    # Metrics
    tokens_used: int = 0
    cost: float = 0.0
    duration: float = 0.0
    success: bool = True
    confidence: float = 1.0
    
    # Context
    goal_id: Optional[str] = None
    iteration: int = 0
    depth: int = 0
    
    # Performance metrics
    latency: float = 0.0
    memory_usage: float = 0.0
    
    # Learning data
    tool_usage: Dict[str, int] = field(default_factory=dict)
    error_type: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "step": self.step,
            "result": self.result,
            "metrics": {
                "tokens_used": self.tokens_used,
                "cost": self.cost,
                "duration": self.duration,
                "success": self.success,
                "confidence": self.confidence,
                "latency": self.latency,
                "memory_usage": self.memory_usage
            },
            "context": {
                "goal_id": self.goal_id,
                "iteration": self.iteration,
                "depth": self.depth
            },
            "learning": {
                "tool_usage": self.tool_usage,
                "error_type": self.error_type,
                "retry_count": self.retry_count
            }
        }


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics."""
    total_events: int = 0
    success_rate: float = 0.0
    average_cost: float = 0.0
    average_duration: float = 0.0
    average_tokens: float = 0.0
    average_confidence: float = 0.0
    
    # Error analysis
    error_rates: Dict[str, float] = field(default_factory=dict)
    common_failures: List[str] = field(default_factory=list)
    
    # Tool effectiveness
    tool_success_rates: Dict[str, float] = field(default_factory=dict)
    most_used_tools: List[str] = field(default_factory=list)
    
    # Time analysis
    peak_hours: List[int] = field(default_factory=list)
    average_session_length: float = 0.0


@dataclass
class LearningMemory:
    """Stores learned patterns and preferences."""
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # Explicit memories
    facts: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Episodic traces
    successful_patterns: List[Dict[str, Any]] = field(default_factory=list)
    failure_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tool effectiveness
    tool_success_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Example bank
    worked_examples: List[Dict[str, Any]] = field(default_factory=list)
    
    # Root cause analysis outcomes
    rca_outcomes: List[Dict[str, Any]] = field(default_factory=list)


class TelemetryCollector:
    """Collects and manages telemetry data."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid4())
        self.events: List[TelemetryEvent] = []
        self.session_start = time.time()
        
        # Storage paths
        self.telemetry_dir = Path("./data/telemetry")
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_file = self.telemetry_dir / f"session_{self.session_id}.json"
        self.metrics_file = self.telemetry_dir / "metrics.json"
    
    def log_event(self, event_type: str, **kwargs) -> TelemetryEvent:
        """Log a telemetry event."""
        event = TelemetryEvent(
            event_type=event_type,
            session_id=self.session_id,
            **kwargs
        )
        
        self.events.append(event)
        
        # Auto-save if enabled
        if settings.enable_telemetry:
            self._save_event(event)
        
        return event
    
    def log_step_execution(self, step: str, result: Dict[str, Any]) -> TelemetryEvent:
        """Log a step execution event."""
        return self.log_event(
            event_type="step_execution",
            step=step,
            result=result,
            tokens_used=result.get("resources_used", {}).get("tokens", 0),
            cost=result.get("resources_used", {}).get("cost", 0.0),
            duration=result.get("duration", 0.0),
            success=result.get("status") == "success",
            confidence=result.get("confidence", 1.0),
            tool_usage=result.get("tool_usage", {})
        )
    
    def log_goal_completion(self, goal_id: str, success: bool, **kwargs) -> TelemetryEvent:
        """Log a goal completion event."""
        return self.log_event(
            event_type="goal_completion",
            goal_id=goal_id,
            success=success,
            **kwargs
        )
    
    def log_checkpoint(self, checkpoint_type: str, decision: str, **kwargs) -> TelemetryEvent:
        """Log a checkpoint event."""
        return self.log_event(
            event_type="checkpoint",
            step=checkpoint_type,
            result={"decision": decision},
            **kwargs
        )
    
    def log_escalation(self, reason: str, details: Dict[str, Any]) -> TelemetryEvent:
        """Log an escalation event."""
        return self.log_event(
            event_type="escalation",
            step=reason,
            result=details,
            success=False
        )
    
    def _save_event(self, event: TelemetryEvent) -> None:
        """Save a single event to storage."""
        try:
            # Append to session file
            events_data = []
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    events_data = json.load(f)
            
            events_data.append(event.to_dict())
            
            with open(self.session_file, 'w') as f:
                json.dump(events_data, f, indent=2)
        
        except Exception as e:
            print(f"Failed to save telemetry event: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session."""
        if not self.events:
            return {"session_id": self.session_id, "events": 0}
        
        total_cost = sum(e.cost for e in self.events)
        total_tokens = sum(e.tokens_used for e in self.events)
        total_duration = sum(e.duration for e in self.events)
        success_count = sum(1 for e in self.events if e.success)
        
        return {
            "session_id": self.session_id,
            "session_duration": time.time() - self.session_start,
            "total_events": len(self.events),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "total_duration": total_duration,
            "success_rate": success_count / len(self.events) if self.events else 0,
            "average_confidence": sum(e.confidence for e in self.events) / len(self.events) if self.events else 0
        }


class LearningSystem:
    """Manages learning and memory for the solving loop."""
    
    def __init__(self):
        self.memory = LearningMemory()
        self.telemetry_collector = TelemetryCollector()
        
        # Storage paths
        self.learning_dir = Path("./data/learning")
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_file = self.learning_dir / "memory.json"
        self.examples_file = self.learning_dir / "examples.json"
        
        # Load existing memory
        self._load_memory()
    
    def _load_memory(self) -> None:
        """Load existing memory from storage."""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                
                self.memory.facts = data.get("facts", {})
                self.memory.preferences = data.get("preferences", {})
                self.memory.successful_patterns = data.get("successful_patterns", [])
                self.memory.failure_patterns = data.get("failure_patterns", [])
                self.memory.tool_success_stats = data.get("tool_success_stats", {})
                self.memory.worked_examples = data.get("worked_examples", [])
                self.memory.rca_outcomes = data.get("rca_outcomes", [])
        
        except Exception as e:
            print(f"Failed to load learning memory: {e}")
    
    def _save_memory(self) -> None:
        """Save memory to storage."""
        try:
            data = {
                "facts": self.memory.facts,
                "preferences": self.memory.preferences,
                "successful_patterns": self.memory.successful_patterns,
                "failure_patterns": self.memory.failure_patterns,
                "tool_success_stats": self.memory.tool_success_stats,
                "worked_examples": self.memory.worked_examples,
                "rca_outcomes": self.memory.rca_outcomes,
                "updated_at": time.time()
            }
            
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            print(f"Failed to save learning memory: {e}")
    
    def store_explicit_memory(self, key: str, value: Any, memory_type: str = "fact") -> None:
        """Store an explicit memory (fact or preference)."""
        if memory_type == "fact":
            self.memory.facts[key] = value
        elif memory_type == "preference":
            self.memory.preferences[key] = value
        
        self.memory.updated_at = time.time()
        self._save_memory()
    
    def record_episodic_trace(self, step: str, result: Dict[str, Any]) -> None:
        """Record an episodic trace of execution."""
        trace = {
            "step": step,
            "result": result,
            "timestamp": time.time(),
            "success": result.get("status") == "success"
        }
        
        if trace["success"]:
            self.memory.successful_patterns.append(trace)
            # Keep only recent successful patterns
            if len(self.memory.successful_patterns) > 100:
                self.memory.successful_patterns = self.memory.successful_patterns[-100:]
        else:
            self.memory.failure_patterns.append(trace)
            # Keep only recent failure patterns
            if len(self.memory.failure_patterns) > 50:
                self.memory.failure_patterns = self.memory.failure_patterns[-50:]
        
        self.memory.updated_at = time.time()
        self._save_memory()
    
    def update_tool_success_stats(self, tools: List[str], result: Dict[str, Any]) -> None:
        """Update tool success statistics."""
        success = result.get("status") == "success"
        
        for tool in tools:
            if tool not in self.memory.tool_success_stats:
                self.memory.tool_success_stats[tool] = {
                    "total_uses": 0,
                    "successes": 0,
                    "failures": 0,
                    "average_cost": 0.0,
                    "average_duration": 0.0
                }
            
            stats = self.memory.tool_success_stats[tool]
            stats["total_uses"] += 1
            
            if success:
                stats["successes"] += 1
            else:
                stats["failures"] += 1
            
            # Update averages
            cost = result.get("resources_used", {}).get("cost", 0.0)
            duration = result.get("duration", 0.0)
            
            stats["average_cost"] = (stats["average_cost"] * (stats["total_uses"] - 1) + cost) / stats["total_uses"]
            stats["average_duration"] = (stats["average_duration"] * (stats["total_uses"] - 1) + duration) / stats["total_uses"]
        
        self.memory.updated_at = time.time()
        self._save_memory()
    
    def update_example_bank(self, step: str, result: Dict[str, Any]) -> None:
        """Update the bank of worked examples."""
        if result.get("status") == "success":
            example = {
                "step": step,
                "result": result,
                "timestamp": time.time(),
                "context": result.get("context", {}),
                "tools_used": result.get("tools_used", [])
            }
            
            self.memory.worked_examples.append(example)
            
            # Keep only recent examples
            if len(self.memory.worked_examples) > 200:
                self.memory.worked_examples = self.memory.worked_examples[-200:]
            
            self.memory.updated_at = time.time()
            self._save_memory()
    
    def perform_root_cause_analysis(self, step: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform root cause analysis on a failure."""
        if result.get("status") == "success":
            return {"analysis": "No failure to analyze"}
        
        # Simple RCA based on patterns
        rca = {
            "step": step,
            "failure_type": result.get("error", "unknown"),
            "timestamp": time.time(),
            "similar_failures": 0,
            "suggested_fixes": []
        }
        
        # Look for similar failures in memory
        error_type = result.get("error", "")
        for pattern in self.memory.failure_patterns:
            if error_type in pattern.get("result", {}).get("error", ""):
                rca["similar_failures"] += 1
        
        # Generate suggestions based on tool success stats
        tools_used = result.get("tools_used", [])
        for tool in tools_used:
            stats = self.memory.tool_success_stats.get(tool, {})
            success_rate = stats.get("successes", 0) / max(stats.get("total_uses", 1), 1)
            
            if success_rate < 0.5:
                rca["suggested_fixes"].append(f"Consider alternative to {tool} (success rate: {success_rate:.2f})")
        
        # Store RCA outcome
        self.memory.rca_outcomes.append(rca)
        if len(self.memory.rca_outcomes) > 50:
            self.memory.rca_outcomes = self.memory.rca_outcomes[-50:]
        
        self.memory.updated_at = time.time()
        self._save_memory()
        
        return rca
    
    def get_recommendations(self, step: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations based on learned patterns."""
        recommendations = {
            "preferred_tools": [],
            "avoid_patterns": [],
            "success_factors": [],
            "estimated_success_rate": 0.5
        }
        
        # Analyze tool success rates
        tool_recommendations = []
        for tool, stats in self.memory.tool_success_stats.items():
            success_rate = stats.get("successes", 0) / max(stats.get("total_uses", 1), 1)
            if success_rate > 0.7:
                tool_recommendations.append((tool, success_rate))
        
        # Sort by success rate
        tool_recommendations.sort(key=lambda x: x[1], reverse=True)
        recommendations["preferred_tools"] = [tool for tool, _ in tool_recommendations[:5]]
        
        # Identify patterns to avoid
        for pattern in self.memory.failure_patterns[-10:]:  # Recent failures
            if pattern.get("step") == step:
                recommendations["avoid_patterns"].append({
                    "pattern": pattern.get("result", {}).get("error", ""),
                    "frequency": 1  # Simplified
                })
        
        # Identify success factors
        for pattern in self.memory.successful_patterns[-20:]:  # Recent successes
            if pattern.get("step") == step:
                tools_used = pattern.get("result", {}).get("tools_used", [])
                recommendations["success_factors"].extend(tools_used)
        
        return recommendations
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learned knowledge."""
        return {
            "memory_age": time.time() - self.memory.created_at,
            "facts_count": len(self.memory.facts),
            "preferences_count": len(self.memory.preferences),
            "successful_patterns": len(self.memory.successful_patterns),
            "failure_patterns": len(self.memory.failure_patterns),
            "tools_analyzed": len(self.memory.tool_success_stats),
            "worked_examples": len(self.memory.worked_examples),
            "rca_outcomes": len(self.memory.rca_outcomes),
            "last_updated": self.memory.updated_at
        }


# Global instances
_telemetry_collector: Optional[TelemetryCollector] = None
_learning_system: Optional[LearningSystem] = None


def get_telemetry_collector() -> TelemetryCollector:
    """Get the global telemetry collector instance."""
    global _telemetry_collector
    if _telemetry_collector is None:
        _telemetry_collector = TelemetryCollector()
    return _telemetry_collector


def get_learning_system() -> LearningSystem:
    """Get the global learning system instance."""
    global _learning_system
    if _learning_system is None:
        _learning_system = LearningSystem()
    return _learning_system


def log_telemetry(step: str, result: Dict[str, Any]) -> None:
    """Convenience function to log telemetry."""
    if settings.enable_telemetry:
        collector = get_telemetry_collector()
        collector.log_step_execution(step, result)


def update_learning(step: str, result: Dict[str, Any]) -> None:
    """Convenience function to update learning system."""
    learning = get_learning_system()
    
    # Record episodic trace
    learning.record_episodic_trace(step, result)
    
    # Update tool success stats
    tools_used = result.get("tools_used", [])
    if tools_used:
        learning.update_tool_success_stats(tools_used, result)
    
    # Update example bank
    learning.update_example_bank(step, result)
    
    # Perform RCA if failure
    if result.get("status") != "success":
        learning.perform_root_cause_analysis(step, result)


def feed_into_future_planning(rca_outcome: Dict[str, Any]) -> None:
    """Feed RCA outcomes into future planning."""
    learning = get_learning_system()
    
    # Store as a preference to avoid similar failures
    failure_type = rca_outcome.get("failure_type", "unknown")
    key = f"avoid_pattern_{failure_type}"
    
    learning.store_explicit_memory(
        key, 
        {
            "pattern": failure_type,
            "suggested_fixes": rca_outcome.get("suggested_fixes", []),
            "confidence": 0.8
        },
        memory_type="preference"
    )