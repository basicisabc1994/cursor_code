"use client"

import { useState } from "react"
import { ChatAgent } from "@/components/chat-agent"
import { WorkerAgent } from "@/components/worker-agent"
import { TelemetryDashboard } from "@/components/telemetry-dashboard"
import { AssetsManager } from "@/components/assets-manager"
import { TaskEmissions } from "@/components/task-emissions"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Brain, MessageSquare, Activity, FolderOpen, Zap, ClipboardList } from "lucide-react"

export default function AgenticAIInterface() {
  const [activeTab, setActiveTab] = useState("chat")

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/50 glass-effect sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg gradient-primary glow-effect">
                <Brain className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">Agentic AI</h1>
                <p className="text-sm text-muted-foreground">Advanced AI Interface</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-accent animate-pulse"></div>
                <span>Active</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-6 bg-card/50 backdrop-blur-sm">
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Chat Agent
            </TabsTrigger>
            <TabsTrigger value="worker" className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Worker Agent
            </TabsTrigger>
            <TabsTrigger value="emissions" className="flex items-center gap-2">
              <ClipboardList className="h-4 w-4" />
              Task Emissions
            </TabsTrigger>
            <TabsTrigger value="telemetry" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Telemetry
            </TabsTrigger>
            <TabsTrigger value="assets" className="flex items-center gap-2">
              <FolderOpen className="h-4 w-4" />
              Assets
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="space-y-6">
            <ChatAgent />
          </TabsContent>

          <TabsContent value="worker" className="space-y-6">
            <WorkerAgent />
          </TabsContent>

          <TabsContent value="emissions" className="space-y-6">
            <TaskEmissions />
          </TabsContent>

          <TabsContent value="telemetry" className="space-y-6">
            <TelemetryDashboard />
          </TabsContent>

          <TabsContent value="assets" className="space-y-6">
            <AssetsManager />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
