"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Activity,
  DollarSign,
  Clock,
  Database,
  MemoryStick,
  Zap,
  TrendingUp,
  Brain,
  Target,
  CheckCircle,
} from "lucide-react"
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"

interface TelemetryData {
  tokensPerMinute: number
  totalCost: number
  systemMemory: number
  executionTime: number
  learningProgress: number
  toolsUsed: number
}

interface CostBreakdown {
  task: string
  cost: number
  tokens: number
  percentage: number
}

interface SystemMemory {
  episodic: number
  semantic: number
  procedural: number
  working: number
}

interface LearningMetric {
  timestamp: string
  accuracy: number
  confidence: number
  adaptability: number
}

const PERFORMANCE_DATA = [
  { time: "00:00", tokens: 120, cost: 0.024, memory: 45 },
  { time: "00:05", tokens: 145, cost: 0.029, memory: 52 },
  { time: "00:10", tokens: 167, cost: 0.033, memory: 48 },
  { time: "00:15", tokens: 189, cost: 0.038, memory: 61 },
  { time: "00:20", tokens: 203, cost: 0.041, memory: 58 },
  { time: "00:25", tokens: 178, cost: 0.036, memory: 55 },
  { time: "00:30", tokens: 195, cost: 0.039, memory: 63 },
]

const COST_BREAKDOWN: CostBreakdown[] = [
  { task: "Chat Processing", cost: 0.156, tokens: 7800, percentage: 45 },
  { task: "Worker Agent", cost: 0.089, tokens: 4450, percentage: 26 },
  { task: "Memory Operations", cost: 0.067, tokens: 3350, percentage: 19 },
  { task: "Learning Updates", cost: 0.034, tokens: 1700, percentage: 10 },
]

const LEARNING_DATA: LearningMetric[] = [
  { timestamp: "10:00", accuracy: 78, confidence: 82, adaptability: 65 },
  { timestamp: "10:15", accuracy: 81, confidence: 85, adaptability: 68 },
  { timestamp: "10:30", accuracy: 84, confidence: 87, adaptability: 72 },
  { timestamp: "10:45", accuracy: 87, confidence: 89, adaptability: 75 },
  { timestamp: "11:00", accuracy: 89, confidence: 91, adaptability: 78 },
]

const MEMORY_DISTRIBUTION = [
  { name: "Episodic", value: 35, color: "#8b5cf6" },
  { name: "Semantic", value: 28, color: "#06b6d4" },
  { name: "Procedural", value: 22, color: "#10b981" },
  { name: "Working", value: 15, color: "#f59e0b" },
]

const TOOL_USAGE = [
  { name: "Search", uses: 45, efficiency: 92 },
  { name: "Analysis", uses: 38, efficiency: 87 },
  { name: "Generation", uses: 52, efficiency: 94 },
  { name: "Reasoning", uses: 29, efficiency: 89 },
  { name: "Memory", uses: 67, efficiency: 96 },
]

export function TelemetryDashboard() {
  const [telemetryData, setTelemetryData] = useState<TelemetryData>({
    tokensPerMinute: 195,
    totalCost: 0.346,
    systemMemory: 63,
    executionTime: 1847,
    learningProgress: 78,
    toolsUsed: 231,
  })

  const [systemMemory] = useState<SystemMemory>({
    episodic: 35,
    semantic: 28,
    procedural: 22,
    working: 15,
  })

  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetryData((prev) => ({
        ...prev,
        tokensPerMinute: Math.floor(Math.random() * 50) + 150,
        totalCost: prev.totalCost + Math.random() * 0.01,
        systemMemory: Math.floor(Math.random() * 20) + 50,
        executionTime: prev.executionTime + 1,
        learningProgress: Math.min(100, prev.learningProgress + Math.random() * 0.5),
        toolsUsed: prev.toolsUsed + Math.floor(Math.random() * 3),
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-effect">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tokens/Min</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">{telemetryData.tokensPerMinute}</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 mr-1" />
              +12% from last hour
            </p>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-accent">${telemetryData.totalCost.toFixed(3)}</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 mr-1" />
              $0.024/hour avg
            </p>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Memory</CardTitle>
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-chart-3">{telemetryData.systemMemory}%</div>
            <Progress value={telemetryData.systemMemory} className="mt-2 h-2" />
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Execution Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-chart-4">
              {Math.floor(telemetryData.executionTime / 60)}m {telemetryData.executionTime % 60}s
            </div>
            <p className="text-xs text-muted-foreground">Session duration</p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 bg-card/50 backdrop-blur-sm">
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
          <TabsTrigger value="learning">Learning</TabsTrigger>
          <TabsTrigger value="tools">Tools</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="glass-effect">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  Token Usage Over Time
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={PERFORMANCE_DATA}>
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.22 0.04 264)" />
                    <XAxis dataKey="time" stroke="oklch(0.65 0.02 264)" />
                    <YAxis stroke="oklch(0.65 0.02 264)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "oklch(0.12 0.03 264)",
                        border: "1px solid oklch(0.22 0.04 264)",
                        borderRadius: "8px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="tokens"
                      stroke="oklch(0.65 0.25 264)"
                      fill="oklch(0.65 0.25 264 / 0.2)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="glass-effect">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-accent" />
                  Memory Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={MEMORY_DISTRIBUTION}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {MEMORY_DISTRIBUTION.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="grid grid-cols-2 gap-2 mt-4">
                  {MEMORY_DISTRIBUTION.map((item) => (
                    <div key={item.name} className="flex items-center gap-2 text-sm">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-muted-foreground">{item.name}</span>
                      <span className="font-medium ml-auto">{item.value}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="glass-effect">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-accent" />
                  Cost Breakdown by Task
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {COST_BREAKDOWN.map((item) => (
                    <div key={item.task} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">{item.task}</span>
                        <div className="text-right">
                          <div className="text-sm font-bold">${item.cost.toFixed(3)}</div>
                          <div className="text-xs text-muted-foreground">{item.tokens.toLocaleString()} tokens</div>
                        </div>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className="h-2 rounded-full gradient-primary transition-all duration-300"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="glass-effect">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-chart-3" />
                  Cost Trend
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={PERFORMANCE_DATA}>
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.22 0.04 264)" />
                    <XAxis dataKey="time" stroke="oklch(0.65 0.02 264)" />
                    <YAxis stroke="oklch(0.65 0.02 264)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "oklch(0.12 0.03 264)",
                        border: "1px solid oklch(0.22 0.04 264)",
                        borderRadius: "8px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="cost"
                      stroke="oklch(0.55 0.22 180)"
                      strokeWidth={2}
                      dot={{ fill: "oklch(0.55 0.22 180)", strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="learning" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card className="glass-effect">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-primary" />
                  Learning Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-primary mb-2">
                      {telemetryData.learningProgress.toFixed(1)}%
                    </div>
                    <Progress value={telemetryData.learningProgress} className="h-3" />
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Explicit Memories</span>
                      <span className="font-medium">1,247</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Pattern Recognition</span>
                      <span className="font-medium">94%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Adaptation Rate</span>
                      <span className="font-medium">+15%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2 glass-effect">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-chart-3" />
                  Learning Metrics Over Time
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={LEARNING_DATA}>
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.22 0.04 264)" />
                    <XAxis dataKey="timestamp" stroke="oklch(0.65 0.02 264)" />
                    <YAxis stroke="oklch(0.65 0.02 264)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "oklch(0.12 0.03 264)",
                        border: "1px solid oklch(0.22 0.04 264)",
                        borderRadius: "8px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="accuracy"
                      stroke="oklch(0.65 0.25 264)"
                      strokeWidth={2}
                      name="Accuracy"
                    />
                    <Line
                      type="monotone"
                      dataKey="confidence"
                      stroke="oklch(0.55 0.22 180)"
                      strokeWidth={2}
                      name="Confidence"
                    />
                    <Line
                      type="monotone"
                      dataKey="adaptability"
                      stroke="oklch(0.75 0.15 120)"
                      strokeWidth={2}
                      name="Adaptability"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="tools" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="glass-effect">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-chart-4" />
                  Tool Usage Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {TOOL_USAGE.map((tool) => (
                    <div key={tool.name} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">{tool.name}</span>
                        <div className="text-right">
                          <div className="text-sm font-bold">{tool.uses} uses</div>
                          <div className="text-xs text-muted-foreground">{tool.efficiency}% efficiency</div>
                        </div>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className="h-2 rounded-full gradient-accent transition-all duration-300"
                          style={{ width: `${tool.efficiency}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="glass-effect">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-400" />
                  System Health
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-400" />
                      <span className="text-sm font-medium">All Systems Operational</span>
                    </div>
                    <Badge variant="outline" className="text-green-400 border-green-400/30">
                      Healthy
                    </Badge>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">CPU Usage</span>
                      <span className="font-medium">23%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Memory Usage</span>
                      <span className="font-medium">67%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Network Latency</span>
                      <span className="font-medium">45ms</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Error Rate</span>
                      <span className="font-medium text-green-400">0.02%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
