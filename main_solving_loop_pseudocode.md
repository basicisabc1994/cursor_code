# Main Solving Loop - Pseudocode Algorithm

## Primary Algorithm Structure

```pseudocode
ALGORITHM MainSolvingLoop
BEGIN
    // Phase 1: Initialization
    framework = SelectAgentFramework(task_complexity, collaboration_need, safety_requirements, deployment_constraints)
    goal_tree = ConstructGoalTree(user_objectives, inferred_subgoals)
    resource_bounds = AssignResourceBounds(org_policy, cost_limits, time_limits, sensitivity_levels)
    
    // Phase 2: Main execution loop
    WHILE HasRemainingGoals(goal_tree) DO
        current_goal = SelectNextGoal(goal_tree, yield_feasibility_criteria)
        
        IF current_goal IS NULL THEN
            BREAK  // No progress possible or all done
        END IF
        
        result = ExecuteGoalLoop(current_goal, framework, resource_bounds)
        
        IF result = STOP_AND_WAIT THEN
            BREAK  // Wait for user input
        END IF
        
        UpdateGoalTree(goal_tree, current_goal, result)
    END WHILE
    
    RETURN FinalStatus(goal_tree, resource_bounds)
END
```

## Core Subroutines

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
FUNCTION ExecuteGoalLoop(goal, framework, bounds)
BEGIN
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
            ExecuteGoalLoop(subgoal, framework, bounds)
        END FOR
        RETURN SUCCESS
    END IF
    
    // Execution Setup
    constraints = SetConstraints(plan, bounds)
    tools = SelectTools(plan, constraints)
    workflow = SelectWorkflow(plan, framework)
    context = GetContext(workspace, state, artifacts)
    research_data = RetrieveRAGData(plan, context)
    
    // Final validation
    IF NOT FinalCheck(plan, constraints, tools, workflow) THEN
        human_tasks = EmitHumanTasks(plan)
        RETURN NEEDS_CLARIFICATION
    END IF
    
    // Execution Phase
    execution_result = ExecutePlan(plan, tools, workflow, constraints)
    
    // Review Phase
    review_result = ReviewExecution(execution_result, constraints)
    
    IF review_result = PASSED THEN
        ForwardDependencies(goal, execution_result)
        MarkGoalComplete(goal)
        RETURN SUCCESS
    ELSE
        root_cause = AnalyzeFailure(execution_result, review_result)
        adjusted_plan = AdjustPlan(plan, root_cause)
        
        IF IsStillTooDifficult(adjusted_plan) THEN
            RETURN DecomposePlan(adjusted_plan)
        ELSE
            RETURN ExecutePlan(adjusted_plan, tools, workflow, constraints)
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
    
    FOR EACH step IN plan.steps DO
        IF RequiresHumanVerification(step) THEN
            EmitApprovalTask(step)
            WaitForApproval()
        END IF
        
        step_result = ExecuteStep(step, tools, constraints)
        
        IF step_result = FAILURE THEN
            RETURN ExecutionFailure(step, step_result)
        END IF
        
        LogTelemetry(step, step_result)
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