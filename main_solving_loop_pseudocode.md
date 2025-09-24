# Main Solving Loop - Pseudocode Algorithm

## Primary Algorithm Structure

```pseudocode
ALGORITHM MainSolvingLoop
BEGIN
    // Phase 1: Initialization
    framework = SelectAgentFramework(task_complexity, collaboration_need, safety_requirements, deployment_constraints)
    goal_tree = ConstructGoalTree(user_objectives, inferred_subgoals)
    resource_bounds = AssignResourceBounds(org_policy, cost_limits, time_limits, sensitivity_levels)
    iteration_count = 0
    last_progress_tick = Now()
    max_iterations = resource_bounds.max_iterations
    
    // Phase 2: Main execution loop
    WHILE HasRemainingGoals(goal_tree) DO
        ManageResourceBounds(resource_bounds, CurrentUsage())
        IF CheckStopConditions(CurrentState(), resource_bounds) THEN
            BREAK
        END IF

        IF max_iterations IS NOT NULL AND iteration_count >= max_iterations THEN
            Escalate("max_iterations_reached")
            BREAK
        END IF

        current_goal = SelectNextGoal(goal_tree, yield_feasibility_criteria)
        
        IF current_goal IS NULL THEN
            BREAK  // No progress possible or all done
        END IF
        
        result = ExecuteGoalLoop(current_goal, framework, resource_bounds, 0)
        result = NormalizeResult(result)
        
        IF result.status = STOP_AND_WAIT OR result.status = NEEDS_CLARIFICATION THEN
            QueueHumanFollowUps(result)
            BREAK  // Wait for user input
        ELSE IF result.status = FAILURE THEN
            HandleFailure(current_goal, result)
            IF CheckStopConditions(CurrentState(), resource_bounds) THEN
                BREAK
            END IF
        END IF
        
        progress_made = UpdateGoalTree(goal_tree, current_goal, result)
        IF progress_made THEN
            last_progress_tick = Now()
        ELSE IF HasExceededNoProgressWindow(last_progress_tick, resource_bounds.no_progress_timeout) THEN
            Escalate("no_progress")
            BREAK
        END IF

        iteration_count = iteration_count + 1
    END WHILE
    
    RETURN FinalStatus(goal_tree, resource_bounds, TelemetrySnapshot())
END
```

## Core Subroutines

### Result Type and Statuses

```pseudocode
TYPE Result {
    status,        // one of: SUCCESS | FAILURE | STOP_AND_WAIT | NEEDS_CLARIFICATION
    data,          // optional payload/artifacts
    error,         // optional error object or reason
    meta           // optional metadata: evidence, retries, costs, timings
}

FUNCTION NormalizeResult(value)
BEGIN
    IF IsResultObject(value) THEN
        RETURN value
    END IF

    // Backward-compat: wrap legacy constants
    IF value IN [SUCCESS, FAILURE, STOP_AND_WAIT, NEEDS_CLARIFICATION] THEN
        RETURN { status: value }
    END IF

    RETURN { status: FAILURE, error: "unknown_result_type", meta: { raw: value } }
END
```

### 1. Agent Framework Selection

```pseudocode
FUNCTION SelectAgentFramework(complexity, collaboration, safety, deployment)
BEGIN
    IF complexity = HIGH AND collaboration = TRUE THEN
        RETURN "autogen"
    ELSE IF complexity = MEDIUM AND safety = HIGH THEN
        RETURN "agentsdk"
    ELSE
        RETURN "low-abstraction"
    END IF
END
```

### 2. Goal Tree Construction

```pseudocode
FUNCTION ConstructGoalTree(objectives, subgoals)
BEGIN
    tree = InitializeTree()
    
    FOR EACH objective IN objectives DO
        goal_node = CreateGoalNode(objective)
        dependencies = InferDependencies(objective, subgoals)
        acceptance_criteria = DefineAcceptanceCriteria(objective)
        
        AddToTree(tree, goal_node, dependencies, acceptance_criteria)
    END FOR
    
    PrioritizeTree(tree, yield_feasibility_criteria)
    RETURN tree
END
```

### 3. Main Goal Execution Loop

```pseudocode
FUNCTION ExecuteGoalLoop(goal, framework, bounds, depth = 0)
BEGIN
    IF bounds.max_depth IS NOT NULL AND depth > bounds.max_depth THEN
        RETURN { status: STOP_AND_WAIT, error: "max_depth_exceeded", meta: { goal } }
    END IF

    // Planning Phase
    plan = CreatePlan(goal)
    
    IF NOT IsWellDefined(plan) THEN
        info_result = GatherInformation(goal, plan)
        IF info_result = INSUFFICIENT THEN
            RETURN STOP_AND_WAIT
        END IF
        plan = UpdatePlan(plan, info_result)
    END IF
    
    IF NOT HasTrustedSources(plan) OR NOT HasWorkedExamples(plan) THEN
        examples = RequestExamples(goal, plan)
        ValidateUnderstanding(plan, examples)
    END IF
    
    // Complexity Assessment
    IF IsTooDifficult(plan) THEN
        subgoals = DecomposePlan(plan)
        FOR EACH subgoal IN subgoals DO
            sub_result = ExecuteGoalLoop(subgoal, framework, bounds, depth + 1)
            sub_result = NormalizeResult(sub_result)
            IF sub_result.status = FAILURE THEN
                RETURN sub_result
            ELSE IF sub_result.status IN [STOP_AND_WAIT, NEEDS_CLARIFICATION] THEN
                RETURN sub_result
            END IF
        END FOR
        RETURN { status: SUCCESS }
    END IF
    
    // Execution Setup
    constraints = SetConstraints(plan, bounds)
    tools = SelectTools(plan, constraints)
    workflow = SelectWorkflow(plan, framework)
    context = GetContext(workspace, state, artifacts)
    research_data = RetrieveRAGData(plan, context)
    IF NOT ValidateRAGData(research_data, constraints) THEN
        RETURN { status: NEEDS_CLARIFICATION, error: "invalid_or_untrusted_rag" }
    END IF
    
    // Final validation
    IF NOT FinalCheck(plan, constraints, tools, workflow) THEN
        human_tasks = EmitHumanTasks(plan)
        RETURN { status: NEEDS_CLARIFICATION, data: human_tasks }
    END IF
    
    // Execution Phase
    retry_attempts = 0
    execution_result = ExecutePlan(plan, tools, workflow, constraints)
    WHILE IsTransientFailure(execution_result) AND retry_attempts < bounds.retry_limit DO
        Backoff(retry_attempts, bounds.retry_backoff)
        retry_attempts = retry_attempts + 1
        execution_result = ExecutePlan(plan, tools, workflow, constraints)
    END WHILE
    
    // Review Phase
    review_result = ReviewExecution(execution_result, constraints)
    
    IF review_result = PASSED THEN
        ForwardDependencies(goal, execution_result)
        MarkGoalComplete(goal)
        RETURN { status: SUCCESS, data: execution_result }
    ELSE
        root_cause = AnalyzeFailure(execution_result, review_result)
        adjusted_plan = AdjustPlan(plan, root_cause)
        
        IF IsStillTooDifficult(adjusted_plan) THEN
            RETURN { status: NEEDS_CLARIFICATION, data: DecomposePlan(adjusted_plan) }
        ELSE
            adjusted_result = ExecutePlan(adjusted_plan, tools, workflow, constraints)
            RETURN NormalizeResult(adjusted_result)
        END IF
    END IF
END
```

### 4. Information Gathering and Validation

```pseudocode
FUNCTION GatherInformation(goal, plan)
BEGIN
    IF auto_mode = TRUE THEN
        next_task = FindHighestYieldActionableSubtask(plan)
        RETURN ExecuteSubtask(next_task)
    ELSE
        clarifications = RequestMinimalClarifications(goal, plan)
        RETURN ProcessClarifications(clarifications)
    END IF
END

FUNCTION ValidateUnderstanding(plan, examples)
BEGIN
    trusted_sources = GatherTrustedSources(plan)
    worked_examples = AnalyzeExamples(examples, trusted_sources)
    
    IF NOT SufficientValidation(trusted_sources, worked_examples) THEN
        RequestAdditionalExamples(plan)
    END IF
    
    RETURN ValidationResult(trusted_sources, worked_examples)
END
```

### 5. Execution and Review

```pseudocode
FUNCTION ExecutePlan(plan, tools, workflow, constraints)
BEGIN
    InitializeGuardrails(constraints)
    
    step_index = 0
    FOR EACH step IN plan.steps DO
        step_index = step_index + 1
        IF NOT HasToolPermissionForStep(step, constraints.tool_permissions) THEN
            RETURN ExecutionFailure(step, "permission_denied")
        END IF

        IF SupportsDryRun(step) AND constraints.enable_dry_runs THEN
            dry_run_outcome = DryRunStep(step, tools, constraints)
            IF IndicatesRisk(dry_run_outcome) THEN
                RETURN ExecutionFailure(step, "dry_run_risk_detected")
            END IF
        END IF

        rollback_action = PrepareRollbackAction(step, constraints)
        IF RequiresHumanVerification(step) THEN
            EmitApprovalTask(step)
            approval = WaitForApprovalOrTimeout(constraints.approval_timeout)
            IF approval != APPROVED THEN
                RETURN ExecutionFailure(step, "approval_not_granted")
            END IF
        END IF
        
        IF CheckStopConditions(CurrentState(), constraints) THEN
            RETURN ExecutionFailure(step, "stop_conditions_triggered")
        END IF

        step_result = ExecuteStep(step, tools, constraints)
        
        IF step_result = FAILURE THEN
            ExecuteRollback(rollback_action)
            RETURN ExecutionFailure(step, step_result)
        END IF
        
        LogTelemetry(step, step_result)

        IF IsCheckpoint(step, constraints) OR ShouldEmitPeriodicSummary(step_index, constraints) THEN
            EmitPeriodicSummary(plan, step, step_result)
        END IF
    END FOR
    
    RETURN ExecutionSuccess(plan)
END

FUNCTION ReviewExecution(result, constraints)
BEGIN
    test_results = RunAcceptanceTests(result, constraints)
    validation_results = ValidateAgainstCriteria(result, constraints)
    evidence = GatherEvidence(result, test_results, validation_results)
    
    IF AllTestsPassed(test_results) AND AllCriteriaMet(validation_results) THEN
        RETURN PASSED
    ELSE
        RETURN FAILED(test_results, validation_results, evidence)
    END IF
END
```

## Safety and Governance Subsystem

```pseudocode
FUNCTION InitializeGuardrails(constraints)
BEGIN
    EnforcePolicyControls(constraints.policies)
    SetupToolAccessControl(constraints.tool_permissions)
    ConfigureDataHandling(constraints.data_rules)
    SetupSandboxing(constraints.sandbox_config)
    InitializeRollbackPlans(constraints.rollback_strategy)
    SetupRateLimiters(constraints.rate_limits)
    EnableAuditLogging(constraints.audit_logging)
    ConfigureTimeouts(constraints.timeouts)
END

FUNCTION EmitApprovalTask(step)
BEGIN
    IF IsAmbiguousRequirement(step) OR 
       IsExternalWriteAction(step) OR 
       IsPolicyGate(step) OR 
       IsLargeResourceEscalation(step) OR 
       IsLowConfidenceDecision(step) THEN
        
        CreateHumanVerificationTask(step)
        AddToApprovalsQueue(step)
    END IF
END
```

## Utility Functions

```pseudocode
FUNCTION ValidateRAGData(data, constraints)
BEGIN
    IF data IS NULL THEN RETURN FALSE END IF
    IF NOT HasTrustedProvenance(data) THEN RETURN FALSE END IF
    IF IsStale(data, constraints.max_rag_age) THEN RETURN FALSE END IF
    RETURN TRUE
END

FUNCTION HasToolPermissionForStep(step, permissions)
BEGIN
    RETURN permissions CONTAINS StepToolPermission(step)
END

FUNCTION PrepareRollbackAction(step, constraints)
BEGIN
    RETURN DeriveRollback(step, constraints.rollback_strategy)
END

FUNCTION ExecuteRollback(action)
BEGIN
    IF action IS NOT NULL THEN PerformRollback(action) END IF
END

FUNCTION SupportsDryRun(step)
BEGIN
    RETURN ToolForStep(step) SUPPORTS "dry_run"
END

FUNCTION DryRunStep(step, tools, constraints)
BEGIN
    RETURN ExecuteStep(step, tools, Merge(constraints, { mode: "dry_run" }))
END

FUNCTION WaitForApprovalOrTimeout(timeout)
BEGIN
    start = Now()
    WHILE Now() - start < timeout DO
        decision = CheckApprovalQueue()
        IF decision IN [APPROVED, REJECTED] THEN RETURN decision END IF
        Sleep(SHORT_INTERVAL)
    END WHILE
    RETURN TIMEOUT
END

FUNCTION IsTransientFailure(execution_result)
BEGIN
    RETURN HasErrorCode(execution_result, ["rate_limited", "timeout", "network_error"])
END

FUNCTION IsCheckpoint(step, constraints)
BEGIN
    RETURN StepType(step) IN constraints.checkpoints
END

FUNCTION ShouldEmitPeriodicSummary(step_index, constraints)
BEGIN
    IF constraints.summary_every_n IS NULL THEN RETURN FALSE END IF
    RETURN step_index MOD constraints.summary_every_n = 0
END
```

## Learning and Telemetry Subsystem

```pseudocode
FUNCTION LogTelemetry(step, result)
BEGIN
    RecordMetrics(tokens_per_minute, total_tokens, latency, cost)
    RecordResourceUsage(memory_usage, tool_usage)
    RecordPerformance(error_rates, confidence_scores)
    
    UpdateLearning(step, result)
END

FUNCTION UpdateLearning(step, result)
BEGIN
    StoreExplicitMemories(facts, preferences)
    RecordEpisodicTrace(step, result)
    UpdateToolSuccessStats(step.tools, result)
    UpdateExampleBank(step, result)
    
    IF result = FAILURE THEN
        rca_outcome = PerformRootCauseAnalysis(step, result)
        FeedIntoFuturePlanning(rca_outcome)
    END IF
END
```

## Resource Management and Stop Conditions

```pseudocode
FUNCTION CheckStopConditions(current_state, bounds)
BEGIN
    IF IsAmbiguityNotResolvable(current_state) OR
       IsUnsafeAction(current_state) OR
       AreResourcesExhausted(current_state, bounds) OR
       AreEvaluationsFailingWithoutCorrection(current_state) THEN
        
        RETURN TRUE
    END IF
    
    RETURN FALSE
END

FUNCTION ManageResourceBounds(bounds, current_usage)
BEGIN
    IF ExceedsTimeLimit(current_usage, bounds.time_limit) OR
       ExceedsCostLimit(current_usage, bounds.cost_limit) OR
       ExceedsTokenLimit(current_usage, bounds.token_limit) THEN
        
        TriggerEscalation(bounds.escalation_rules)
    END IF
END
```

## Learning-by-Doing Fallback

```pseudocode
FUNCTION AttemptLearningByDoing(partial_info, action)
BEGIN
    IF IsActionSafe(action) AND IsActionReversible(action) THEN
        IF GetSuccessLikelihood(action) = VERY_LOW THEN
            WarnUser(action, "Low success probability")
            IF NOT IsLowRisk(action) OR NOT IsBounded(action) THEN
                RETURN ABORT
            END IF
        END IF
        
        result = ExecuteSmallestStep(action)
        signal = GainSignalFromResult(result)
        RETURN signal
    ELSE
        RETURN ABORT
    END IF
END
```

## Example Implementation Patterns

### Example A: Deployment Problem (SME Support Agent)
```pseudocode
// Framework: agentsdk (single-agent, high abstraction)
framework = "agentsdk"
goal_tree = [
    "Deploy support agent" -> [
        "Ingest FAQ + KB",
        "Setup email + chat integration", 
        "Define guardrails + escalation",
        "Pilot with 10 tickets; success ≥85% CSAT"
    ]
]
bounds = {cost: "$30/day", time: "≤1h setup", policies: "no PII exfiltration"}
```

### Example B: Auto Mode Long-Horizon Task
```pseudocode
// Frictionless execution with periodic checkpoints
auto_mode = TRUE
guardrails = {
    approval_gates: ["external modifications"],
    periodic_summaries: EVERY_N_STEPS,
    auto_halt_conditions: ["low confidence", "cost spike"]
}
checkpoints = ["schema changes", "third-party calls", "policy-sensitive content"]
```

This pseudocode algorithm captures the complete flow and decision logic from your Mermaid flowchart and specification, organized into a structured, implementable format.