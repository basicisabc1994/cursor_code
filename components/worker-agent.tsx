"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Progress } from "@/components/ui/progress"
import { Play, Pause, Square, Zap, Brain, Target, AlertTriangle, CheckCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface ThoughtAction {
  id: string
  timestamp: Date
  thought: string
  action: string
  status: "thinking" | "executing" | "completed" | "error"
  duration?: number
  confidence: number
  priority: "low" | "medium" | "high" | "critical"
}

interface WorkerState {
  isRunning: boolean
  currentTask: string
  progress: number
  thoughtsPerMinute: number
  actionsCompleted: number
  errorCount: number
}

const SAMPLE_THOUGHTS: Omit<ThoughtAction, "id" | "timestamp">[] = [
  {
    thought: "Analyzing user behavior patterns from recent interactions",
    action: "Scanning conversation history for preference indicators",
    status: "completed",
    duration: 1200,
    confidence: 0.87,
    priority: "medium",
  },
  {
    thought: "Detecting potential optimization opportunities in response generation",
    action: "Evaluating response quality metrics and user satisfaction",
    status: "executing",
    confidence: 0.92,
    priority: "high",
  },
  {
    thought: "Memory consolidation required for long-term learning",
    action: "Compressing episodic memories into semantic knowledge",
    status: "thinking",
    confidence: 0.78,
    priority: "low",
  },
  {
    thought: "Anomaly detected in reasoning chain - investigating logical inconsistency",
    action: "Backtracking through inference steps to identify error source",
    status: "error",
    confidence: 0.45,
    priority: "critical",
  },
  {
    thought: "Contextual understanding needs refinement for domain-specific queries",
    action: "Updating knowledge graph with specialized terminology",
    status: "completed",
    duration: 2100,
    confidence: 0.91,
    priority: "high",
  },
]

export function WorkerAgent() {
  const [workerState, setWorkerState] = useState<WorkerState>({
    isRunning: false,
    currentTask: "Idle - Ready to begin processing",
    progress: 0,
    thoughtsPerMinute: 0,
    actionsCompleted: 0,
    errorCount: 0,
  })
  const [thoughtStream, setThoughtStream] = useState<ThoughtAction[]>([])
  const [constraints, setConstraints] = useState({
    maxThoughtsPerMinute: 45,
    memoryLimit: 85,
    processingIntensity: 70,
  })
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const intervalRef = useRef<NodeJS.Timeout>()

  const generateThought = (): ThoughtAction => {
    const template = SAMPLE_THOUGHTS[Math.floor(Math.random() * SAMPLE_THOUGHTS.length)]
    return {
      ...template,
      id: Date.now().toString() + Math.random(),
      timestamp: new Date(),
      status: Math.random() > 0.1 ? (Math.random() > 0.3 ? "completed" : "executing") : "error",
    }
  }

  const startWorker = () => {
    setWorkerState((prev) => ({ ...prev, isRunning: true, currentTask: "Initializing continuous processing..." }))

    intervalRef.current = setInterval(
      () => {
        const newThought = generateThought()
        setThoughtStream((prev) => [newThought, ...prev.slice(0, 49)]) // Keep last 50 thoughts

        setWorkerState((prev) => ({
          ...prev,
          currentTask: newThought.thought,
          progress: Math.min(100, prev.progress + Math.random() * 5),
          thoughtsPerMinute: Math.floor(Math.random() * 20) + 25,
          actionsCompleted: prev.actionsCompleted + (newThought.status === "completed" ? 1 : 0),
          errorCount: prev.errorCount + (newThought.status === "error" ? 1 : 0),
        }))
      },
      Math.random() * 2000 + 1000,
    ) // Random interval between 1-3 seconds
  }

  const pauseWorker = () => {
    setWorkerState((prev) => ({ ...prev, isRunning: false, currentTask: "Paused - Processing suspended" }))
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
  }

  const stopWorker = () => {
    setWorkerState({
      isRunning: false,
      currentTask: "Stopped - All processing halted",
      progress: 0,
      thoughtsPerMinute: 0,
      actionsCompleted: 0,
      errorCount: 0,
    })
    setThoughtStream([])
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
  }

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = 0
    }
  }, [thoughtStream])

  const getStatusIcon = (status: ThoughtAction["status"]) => {
    switch (status) {
      case "thinking":
        return <Brain className="h-3 w-3 text-blue-400 animate-pulse" />
      case "executing":
        return <Zap className="h-3 w-3 text-yellow-400 animate-spin" />
      case "completed":
        return <CheckCircle className="h-3 w-3 text-green-400" />
      case "error":
        return <AlertTriangle className="h-3 w-3 text-red-400" />
    }
  }

  const getPriorityColor = (priority: ThoughtAction["priority"]) => {
    switch (priority) {
      case "low":
        return "bg-blue-500/20 text-blue-300 border-blue-500/30"
      case "medium":
        return "bg-yellow-500/20 text-yellow-300 border-yellow-500/30"
      case "high":
        return "bg-orange-500/20 text-orange-300 border-orange-500/30"
      case "critical":
        return "bg-red-500/20 text-red-300 border-red-500/30"
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
      {/* Worker Controls */}
      <div className="space-y-4">
        <Card className="glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Zap className="h-5 w-5 text-primary" />
              Worker Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                onClick={startWorker}
                disabled={workerState.isRunning}
                className="flex-1"
                variant={workerState.isRunning ? "secondary" : "default"}
              >
                <Play className="h-4 w-4 mr-2" />
                Start
              </Button>
              <Button
                onClick={pauseWorker}
                disabled={!workerState.isRunning}
                variant="outline"
                className="flex-1 bg-transparent"
              >
                <Pause className="h-4 w-4 mr-2" />
                Pause
              </Button>
              <Button onClick={stopWorker} variant="destructive" className="flex-1">
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                <Badge variant={workerState.isRunning ? "default" : "secondary"}>
                  {workerState.isRunning ? "Running" : "Stopped"}
                </Badge>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium">{Math.round(workerState.progress)}%</span>
                </div>
                <Progress value={workerState.progress} className="h-2" />
              </div>

              <div className="text-sm">
                <span className="text-muted-foreground">Current Task:</span>
                <p className="mt-1 text-foreground font-medium leading-relaxed">{workerState.currentTask}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Thoughts/min</span>
              <span className="font-medium text-accent">{workerState.thoughtsPerMinute}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Actions Completed</span>
              <span className="font-medium text-green-400">{workerState.actionsCompleted}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Errors</span>
              <span className="font-medium text-red-400">{workerState.errorCount}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Efficiency</span>
              <span className="font-medium">
                {workerState.actionsCompleted > 0
                  ? Math.round(
                      (workerState.actionsCompleted / (workerState.actionsCompleted + workerState.errorCount)) * 100,
                    )
                  : 0}
                %
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Constraints & Guardrails</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Max Thoughts/min</span>
                <span className="font-medium">{constraints.maxThoughtsPerMinute}</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-primary transition-all duration-300"
                  style={{ width: `${(workerState.thoughtsPerMinute / constraints.maxThoughtsPerMinute) * 100}%` }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Memory Usage</span>
                <span className="font-medium">{constraints.memoryLimit}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-yellow-500 transition-all duration-300"
                  style={{ width: `${constraints.memoryLimit}%` }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Processing Intensity</span>
                <span className="font-medium">{constraints.processingIntensity}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-orange-500 transition-all duration-300"
                  style={{ width: `${constraints.processingIntensity}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Continuous Stream of Consciousness */}
      <div className="lg:col-span-2">
        <Card className="h-full flex flex-col glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Brain className="h-5 w-5 text-primary" />
              Stream of Consciousness
              <Badge variant="secondary" className="ml-auto">
                {thoughtStream.length} thoughts
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            <ScrollArea className="flex-1 px-6" ref={scrollAreaRef}>
              <div className="space-y-3 pb-4">
                {thoughtStream.length === 0 ? (
                  <div className="flex items-center justify-center h-64 text-muted-foreground">
                    <div className="text-center">
                      <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Worker agent is idle</p>
                      <p className="text-sm">Start the worker to see the stream of consciousness</p>
                    </div>
                  </div>
                ) : (
                  thoughtStream.map((item) => (
                    <div
                      key={item.id}
                      className={cn(
                        "p-4 rounded-lg border transition-all duration-200",
                        item.status === "error" ? "bg-red-500/5 border-red-500/20" : "bg-card/30 border-border/50",
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1">{getStatusIcon(item.status)}</div>
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{item.timestamp.toLocaleTimeString()}</span>
                            <Badge variant="outline" className={cn("text-xs", getPriorityColor(item.priority))}>
                              {item.priority}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {Math.round(item.confidence * 100)}% confidence
                            </Badge>
                            {item.duration && (
                              <Badge variant="outline" className="text-xs">
                                {item.duration}ms
                              </Badge>
                            )}
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-start gap-2">
                              <Target className="h-3 w-3 text-blue-400 mt-0.5 flex-shrink-0" />
                              <p className="text-sm font-medium text-foreground leading-relaxed">
                                <span className="text-blue-400">Thought:</span> {item.thought}
                              </p>
                            </div>
                            <div className="flex items-start gap-2">
                              <Zap className="h-3 w-3 text-yellow-400 mt-0.5 flex-shrink-0" />
                              <p className="text-sm text-muted-foreground leading-relaxed">
                                <span className="text-yellow-400">Action:</span> {item.action}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
