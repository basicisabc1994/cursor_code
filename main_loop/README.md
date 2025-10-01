# Main Solving Loop Implementation

This directory contains a complete implementation of the Main Solving Loop algorithm based on the pseudocode specification. The implementation follows the structured approach outlined in `main_solving_loop_pseudocode.md` and integrates with the existing OpenAI Agents SDK and RAG pipeline.

## Architecture Overview

The implementation consists of several key components:

### Core Components

1. **`main_solver.py`** - Main solving loop implementation
   - Primary algorithm structure following the pseudocode
   - Agent framework selection and management
   - Goal execution orchestration
   - Integration with all subsystems

2. **`goal_tree.py`** - Goal tree management
   - Goal node data structures with status tracking
   - Dependency management and resolution
   - Priority-based goal selection
   - Acceptance criteria validation

3. **`resource_bounds.py`** - Resource management and checkpoints
   - Resource usage tracking and limits
   - User-defined checkpoint system
   - Escalation handling and safety controls
   - Approval workflows and timeouts

4. **`tools.py`** - Comprehensive tool set
   - Goal management tools
   - Information gathering and validation
   - Plan creation and execution
   - File operations and system commands
   - Review and failure analysis
   - Telemetry collection

5. **`telemetry.py`** - Learning and telemetry subsystem
   - Event logging and metrics collection
   - Performance analysis and optimization
   - Learning from execution patterns
   - Root cause analysis for failures

## Key Features

### 🎯 Goal-Oriented Execution
- Hierarchical goal trees with dependencies
- Priority-based goal selection
- Automatic progress tracking
- Failure recovery mechanisms

### 🛡️ Safety and Governance
- Resource bounds enforcement
- User-defined checkpoints
- Dry-run capabilities
- Sandbox mode for safe execution
- Audit logging and compliance

### 🧠 Learning and Adaptation
- Episodic memory of successful patterns
- Tool effectiveness tracking
- Root cause analysis for failures
- Continuous improvement through learning

### 🔧 Flexible Agent Framework
- Support for multiple agent frameworks (OpenAI Agents SDK, AutoGen, low-abstraction)
- Configurable LLM backends (Ollama, OpenRouter, OpenAI)
- Tool permission management
- Context-aware execution

### 📊 Comprehensive Telemetry
- Real-time performance monitoring
- Cost and resource tracking
- Success rate analysis
- Detailed execution logs

## Usage Examples

### Basic Usage

```python
from main_loop.main_solver import main_solving_loop

# Simple objectives
objectives = ["Create a Python script", "Test the script", "Document the code"]

result = await main_solving_loop(
    user_objectives=objectives
)

print(f"Status: {result['status']}")
print(f"Goals completed: {result['telemetry']['goals_completed']}")
```

### Advanced Configuration

```python
from main_loop.main_solver import main_solving_loop
from main_loop.resource_bounds import ResourceBounds

# Complex project with resource limits and checkpoints
objectives = [
    "Design REST API for user management",
    "Implement authentication system", 
    "Create comprehensive tests",
    "Deploy to staging environment"
]

# Custom resource bounds
resource_bounds = ResourceBounds(
    max_iterations=20,
    cost_limit=10.0,  # $10 limit
    time_limit=3600,  # 1 hour
    enable_dry_runs=True,
    sandbox_mode=True
)

# User-defined checkpoints
user_checkpoints = [
    {
        "event": "goal_selected",
        "mode": "require_approval", 
        "condition": "'deploy' in ctx.get('current_goal', {}).get('description', '').lower()",
        "description": "Deployment requires approval"
    }
]

result = await main_solving_loop(
    user_objectives=objectives,
    user_checkpoints=user_checkpoints,
    resource_bounds=resource_bounds
)
```

### CLI Integration

```bash
# Interactive mode
python cli.py solve --interactive

# Direct objectives
python cli.py solve -o "Analyze project structure" -o "Generate report"

# With resource limits
python cli.py solve -o "Complete task" --max-iterations 10 --cost-limit 2.0
```

## Configuration

The system uses the enhanced configuration in `src/config.py`:

```python
# LLM Backend Configuration
LLM_BACKEND=ollama  # ollama | openrouter | openai
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Agent Framework
AGENT_FRAMEWORK=agentsdk  # agentsdk | autogen | low-abstraction

# Resource Bounds
MAX_ITERATIONS=50
COST_LIMIT=10.0
TIME_LIMIT=3600
ENABLE_DRY_RUNS=true
SANDBOX_MODE=true

# Telemetry
ENABLE_TELEMETRY=true
ENABLE_AUDIT_LOGGING=true
```

## File Structure

```
main_loop/
├── README.md                           # This file
├── main_solving_loop_pseudocode.md     # Original pseudocode specification
├── main_solver.py                      # Main solving loop implementation
├── goal_tree.py                        # Goal tree management
├── resource_bounds.py                  # Resource bounds and checkpoints
├── tools.py                           # Comprehensive tool set
├── telemetry.py                       # Telemetry and learning system
├── example_main_solver.py             # Comprehensive examples
└── goal-loop.mmd                      # Mermaid flowchart
```

## Integration Points

### RAG Pipeline Integration
The solver automatically integrates with the existing RAG pipeline for information gathering:

```python
# Automatic RAG integration
rag_pipeline = RAGPipeline(use_local_embeddings=True)
research_data = await retrieve_rag_data_internal(plan, context, rag_pipeline)
```

### CLI Integration
Extended the existing CLI with a new `solve` command:

```bash
python cli.py solve --help
```

### Demo UI Integration
The solver can be integrated into the demo UI through the existing agent components.

## Testing

Run the comprehensive integration tests:

```bash
# Run all tests
python test_main_solver.py

# Run with cleanup
python test_main_solver.py --cleanup

# Skip test data setup
python test_main_solver.py --no-setup
```

Test categories:
- Basic functionality
- Complex scenarios with multiple objectives
- Failure handling and recovery
- Goal tree operations
- Telemetry and learning systems
- Tool system functionality
- Agent framework selection

## Monitoring and Debugging

### Telemetry Data
Telemetry data is stored in `./data/telemetry/`:
- Session logs with detailed execution traces
- Performance metrics and resource usage
- Error analysis and failure patterns

### Learning Data
Learning data is stored in `./data/learning/`:
- Episodic memory of execution patterns
- Tool effectiveness statistics
- Root cause analysis outcomes
- Worked examples for future reference

### Log Files
Execution logs provide detailed information about:
- Goal selection and execution
- Checkpoint evaluations
- Resource usage and escalations
- Tool invocations and results

## Performance Considerations

### Resource Management
- Configurable limits prevent runaway execution
- Progress tracking ensures forward momentum
- Escalation mechanisms handle edge cases

### Optimization
- Tool success statistics guide future selections
- Learning system improves over time
- Dry-run capabilities reduce risk

### Scalability
- Modular architecture supports extension
- Pluggable agent frameworks
- Configurable tool permissions

## Security and Safety

### Sandbox Mode
- Restricted tool access in sandbox mode
- Safe command execution with allowlists
- File system access controls

### Approval Workflows
- User-defined checkpoints for sensitive operations
- Timeout mechanisms prevent hanging
- Audit trails for compliance

### Error Handling
- Graceful failure recovery
- Root cause analysis for learning
- Escalation to human operators

## Extending the System

### Adding New Tools
```python
@function_tool
def my_custom_tool(param: str) -> Dict[str, Any]:
    """Custom tool description."""
    # Implementation
    return {"result": "success"}

# Add to AVAILABLE_TOOLS
AVAILABLE_TOOLS.append(my_custom_tool)
```

### Custom Agent Frameworks
```python
def build_custom_agent(instructions: str, tools: List[Any]):
    # Custom agent implementation
    return custom_agent

# Register in build_agent function
```

### Custom Checkpoints
```python
user_checkpoints = [
    {
        "event": "custom_event",
        "mode": "require_approval",
        "condition": "custom_condition(ctx)",
        "description": "Custom checkpoint"
    }
]
```

## Troubleshooting

### Common Issues

1. **OpenAI Agents SDK not available**
   ```bash
   pip install git+https://github.com/openai/openai-agents-python.git
   ```

2. **RAG pipeline errors**
   - Check NOMIC_API_KEY configuration
   - Ensure PDF documents are available
   - Use local embeddings as fallback

3. **Resource limit exceeded**
   - Adjust resource bounds in configuration
   - Check for infinite loops in goal execution
   - Review escalation logs

4. **Tool permission denied**
   - Update tool_permissions in resource bounds
   - Use sandbox mode for safe execution
   - Check tool categorization (safe vs restricted)

### Debug Mode
Enable debug logging:
```bash
python cli.py solve --debug
```

### Telemetry Analysis
Review telemetry data for performance insights:
```python
from main_loop.telemetry import get_telemetry_collector
collector = get_telemetry_collector()
summary = collector.get_session_summary()
```

## Contributing

When contributing to the main solver:

1. Follow the pseudocode specification
2. Add comprehensive tests for new features
3. Update telemetry collection for new events
4. Document configuration options
5. Ensure backward compatibility

## License

This implementation follows the same license as the parent project.