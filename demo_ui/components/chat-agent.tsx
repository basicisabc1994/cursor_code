"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Send, Brain, User, Lightbulb, Database, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  reasoning?: string
  memory?: string[]
  confidence?: number
}

interface AgentCapabilities {
  memory: number
  reasoning: number
  learning: number
  agentic: number
}

export function ChatAgent() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your enhanced AI agent with advanced memory, reasoning, and learning capabilities. How can I assist you today?",
      timestamp: new Date(),
      confidence: 0.95,
      memory: ["Initial greeting", "System initialization"],
      reasoning: "User has just started the session, providing a welcoming introduction with capability overview.",
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [capabilities, setCapabilities] = useState<AgentCapabilities>({
    memory: 85,
    reasoning: 92,
    learning: 78,
    agentic: 88,
  })
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    // Simulate AI processing with enhanced capabilities
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `I understand you're asking about "${input}". Let me process this with my enhanced capabilities and provide a comprehensive response.`,
        timestamp: new Date(),
        confidence: Math.random() * 0.3 + 0.7,
        memory: [`User query: ${input}`, "Context analysis completed", "Previous conversation patterns identified"],
        reasoning: `Analyzing user intent: The query appears to be seeking information/assistance. Cross-referencing with memory banks and applying learned patterns to provide optimal response.`,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)

      // Update capabilities based on interaction
      setCapabilities((prev) => ({
        memory: Math.min(100, prev.memory + Math.random() * 2),
        reasoning: Math.min(100, prev.reasoning + Math.random() * 1.5),
        learning: Math.min(100, prev.learning + Math.random() * 3),
        agentic: Math.min(100, prev.agentic + Math.random() * 1),
      }))
    }, 2000)
  }

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-200px)]">
      {/* Main Chat Interface */}
      <div className="lg:col-span-3 flex flex-col">
        <Card className="flex-1 flex flex-col glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Brain className="h-5 w-5 text-primary" />
              Enhanced Chat Agent
              <Badge variant="secondary" className="ml-auto">
                {messages.length - 1} messages
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            <ScrollArea className="flex-1 px-6" ref={scrollAreaRef}>
              <div className="space-y-4 pb-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "flex gap-3 p-4 rounded-lg",
                      message.role === "user" ? "bg-primary/10 ml-12" : "bg-card/50 mr-12",
                    )}
                  >
                    <div className="flex-shrink-0">
                      {message.role === "user" ? (
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                          <User className="h-4 w-4 text-primary" />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center">
                          <Brain className="h-4 w-4 text-primary-foreground" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="font-medium">{message.role === "user" ? "You" : "AI Agent"}</span>
                        <span>•</span>
                        <span>{message.timestamp.toLocaleTimeString()}</span>
                        {message.confidence && (
                          <>
                            <span>•</span>
                            <Badge variant="outline" className="text-xs">
                              {Math.round(message.confidence * 100)}% confidence
                            </Badge>
                          </>
                        )}
                      </div>
                      <p className="text-foreground leading-relaxed">{message.content}</p>

                      {message.reasoning && (
                        <div className="mt-3 p-3 bg-accent/10 rounded-md border border-accent/20">
                          <div className="flex items-center gap-2 text-sm font-medium text-accent mb-1">
                            <Lightbulb className="h-3 w-3" />
                            Reasoning Process
                          </div>
                          <p className="text-sm text-muted-foreground">{message.reasoning}</p>
                        </div>
                      )}

                      {message.memory && message.memory.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {message.memory.map((mem, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              <Database className="h-2 w-2 mr-1" />
                              {mem}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3 p-4 rounded-lg bg-card/50 mr-12">
                    <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center">
                      <Brain className="h-4 w-4 text-primary-foreground animate-pulse" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                        <span className="font-medium">AI Agent</span>
                        <span>•</span>
                        <span>Processing...</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-primary rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-primary rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
            <Separator />
            <div className="p-4">
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything... I'll use my enhanced capabilities to help you."
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Capabilities Panel */}
      <div className="space-y-4">
        <Card className="glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Agent Capabilities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(capabilities).map(([key, value]) => (
              <div key={key} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="capitalize text-muted-foreground">{key}</span>
                  <span className="font-medium">{Math.round(value)}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="h-2 rounded-full gradient-primary transition-all duration-500"
                    style={{ width: `${value}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Session Stats</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Messages</span>
              <span className="font-medium">{messages.length}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Session Time</span>
              <span className="font-medium">12m 34s</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Memory Used</span>
              <span className="font-medium">2.4 MB</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Learning Rate</span>
              <span className="font-medium text-accent">+15%</span>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Recent Memories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                "User preferences learned",
                "Context patterns identified",
                "Response optimization",
                "Knowledge base updated",
              ].map((memory, idx) => (
                <div key={idx} className="text-xs text-muted-foreground p-2 bg-muted/20 rounded">
                  {memory}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
