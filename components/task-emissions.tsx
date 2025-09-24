"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Star,
  MessageSquare,
  Settings,
  Save,
  Edit3,
  Eye,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface TaskEmission {
  id: string
  timestamp: Date
  title: string
  description: string
  category: "decision" | "analysis" | "action" | "learning" | "error"
  priority: "low" | "medium" | "high" | "critical"
  status: "pending" | "reviewed" | "approved" | "rejected"
  confidence: number
  reasoning: string
  suggestedAction?: string
  humanRating?: number
  humanFeedback?: string
  reviewedAt?: Date
  reviewedBy?: string
}

interface Constraints {
  maxEmissionsPerHour: number
  minConfidenceThreshold: number
  requireHumanApproval: boolean
  autoApproveHighConfidence: boolean
  escalationThreshold: number
}

const SAMPLE_EMISSIONS: Omit<TaskEmission, "id" | "timestamp">[] = [
  {
    title: "Detected Potential Security Vulnerability",
    description:
      "Analysis of user input patterns suggests possible injection attempt. Recommend implementing additional validation layers.",
    category: "decision",
    priority: "critical",
    status: "pending",
    confidence: 0.89,
    reasoning:
      "Pattern matching indicates SQL injection signatures in recent queries. Cross-referencing with known attack vectors shows 89% similarity.",
    suggestedAction: "Implement parameterized queries and input sanitization",
  },
  {
    title: "Learning Pattern Optimization Opportunity",
    description:
      "User interaction data suggests preference for concise responses. Adjusting response generation parameters.",
    category: "learning",
    priority: "medium",
    status: "reviewed",
    confidence: 0.76,
    reasoning:
      "Analysis of 247 recent interactions shows 73% preference for responses under 150 words. Confidence interval: 68-84%.",
    humanRating: 4,
    humanFeedback: "Good insight, but consider context-dependent preferences",
    reviewedAt: new Date(Date.now() - 3600000),
    reviewedBy: "Human Reviewer",
  },
  {
    title: "Anomalous Resource Usage Detected",
    description:
      "Memory consumption has increased 34% over baseline. Investigating potential memory leaks in reasoning modules.",
    category: "analysis",
    priority: "high",
    status: "pending",
    confidence: 0.92,
    reasoning:
      "Continuous monitoring shows steady increase in memory allocation without corresponding deallocation. Heap analysis indicates retention in episodic memory structures.",
    suggestedAction: "Implement garbage collection for old episodic memories",
  },
  {
    title: "Successful Task Completion Strategy",
    description:
      "Multi-step reasoning approach yielded 23% better outcomes than single-pass analysis for complex queries.",
    category: "learning",
    priority: "low",
    status: "approved",
    confidence: 0.84,
    reasoning:
      "Comparative analysis of 156 complex queries shows significant improvement with iterative refinement approach.",
    humanRating: 5,
    humanFeedback: "Excellent finding! Please implement this as default for complex queries.",
    reviewedAt: new Date(Date.now() - 7200000),
    reviewedBy: "Human Reviewer",
  },
]

export function TaskEmissions() {
  const [emissions, setEmissions] = useState<TaskEmission[]>([])
  const [selectedEmission, setSelectedEmission] = useState<TaskEmission | null>(null)
  const [constraints, setConstraints] = useState<Constraints>({
    maxEmissionsPerHour: 12,
    minConfidenceThreshold: 0.7,
    requireHumanApproval: true,
    autoApproveHighConfidence: false,
    escalationThreshold: 0.9,
  })
  const [isEditingConstraints, setIsEditingConstraints] = useState(false)
  const [reviewFeedback, setReviewFeedback] = useState("")
  const [reviewRating, setReviewRating] = useState(0)

  // Generate sample emissions on component mount
  useEffect(() => {
    const generateEmissions = () => {
      const newEmissions = SAMPLE_EMISSIONS.map((template, index) => ({
        ...template,
        id: `emission-${Date.now()}-${index}`,
        timestamp: new Date(Date.now() - Math.random() * 86400000), // Random time in last 24h
      }))
      setEmissions(newEmissions)
    }

    generateEmissions()
  }, [])

  const getCategoryIcon = (category: TaskEmission["category"]) => {
    switch (category) {
      case "decision":
        return <AlertCircle className="h-4 w-4 text-orange-400" />
      case "analysis":
        return <Eye className="h-4 w-4 text-blue-400" />
      case "action":
        return <CheckCircle className="h-4 w-4 text-green-400" />
      case "learning":
        return <MessageSquare className="h-4 w-4 text-purple-400" />
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-400" />
    }
  }

  const getPriorityColor = (priority: TaskEmission["priority"]) => {
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

  const getStatusColor = (status: TaskEmission["status"]) => {
    switch (status) {
      case "pending":
        return "bg-yellow-500/20 text-yellow-300"
      case "reviewed":
        return "bg-blue-500/20 text-blue-300"
      case "approved":
        return "bg-green-500/20 text-green-300"
      case "rejected":
        return "bg-red-500/20 text-red-300"
    }
  }

  const handleReview = (emissionId: string, approved: boolean) => {
    setEmissions((prev) =>
      prev.map((emission) =>
        emission.id === emissionId
          ? {
              ...emission,
              status: approved ? "approved" : "rejected",
              humanRating: reviewRating || undefined,
              humanFeedback: reviewFeedback || undefined,
              reviewedAt: new Date(),
              reviewedBy: "Human Reviewer",
            }
          : emission,
      ),
    )
    setReviewFeedback("")
    setReviewRating(0)
    setSelectedEmission(null)
  }

  const renderStarRating = (rating: number, interactive = false, onChange?: (rating: number) => void) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={cn(
              "h-4 w-4",
              star <= rating ? "fill-yellow-400 text-yellow-400" : "text-gray-400",
              interactive && "cursor-pointer hover:text-yellow-400",
            )}
            onClick={() => interactive && onChange?.(star)}
          />
        ))}
      </div>
    )
  }

  const pendingEmissions = emissions.filter((e) => e.status === "pending")
  const reviewedEmissions = emissions.filter((e) => e.status !== "pending")

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
      {/* Emissions List */}
      <div className="lg:col-span-2 space-y-4">
        <Card className="glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <AlertCircle className="h-5 w-5 text-primary" />
              Task Emissions
              <Badge variant="secondary" className="ml-auto">
                {pendingEmissions.length} pending review
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[600px]">
              <div className="space-y-3 p-6">
                {/* Pending Emissions */}
                {pendingEmissions.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Pending Review ({pendingEmissions.length})
                    </h3>
                    {pendingEmissions.map((emission) => (
                      <Card
                        key={emission.id}
                        className={cn(
                          "cursor-pointer transition-all duration-200 hover:shadow-lg",
                          selectedEmission?.id === emission.id ? "ring-2 ring-primary" : "",
                          emission.priority === "critical" ? "border-red-500/50 bg-red-500/5" : "bg-card/30",
                        )}
                        onClick={() => setSelectedEmission(emission)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start gap-3">
                            {getCategoryIcon(emission.category)}
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4 className="font-medium text-foreground">{emission.title}</h4>
                                <Badge variant="outline" className={cn("text-xs", getPriorityColor(emission.priority))}>
                                  {emission.priority}
                                </Badge>
                                <Badge variant="outline" className={cn("text-xs", getStatusColor(emission.status))}>
                                  {emission.status}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {Math.round(emission.confidence * 100)}% confidence
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground leading-relaxed">{emission.description}</p>
                              <div className="text-xs text-muted-foreground">{emission.timestamp.toLocaleString()}</div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}

                {/* Reviewed Emissions */}
                {reviewedEmissions.length > 0 && (
                  <div className="space-y-3">
                    <Separator />
                    <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                      <CheckCircle className="h-4 w-4" />
                      Recently Reviewed ({reviewedEmissions.length})
                    </h3>
                    {reviewedEmissions.map((emission) => (
                      <Card
                        key={emission.id}
                        className={cn(
                          "cursor-pointer transition-all duration-200 hover:shadow-lg bg-card/20",
                          selectedEmission?.id === emission.id ? "ring-2 ring-primary" : "",
                        )}
                        onClick={() => setSelectedEmission(emission)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start gap-3">
                            {getCategoryIcon(emission.category)}
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4 className="font-medium text-foreground">{emission.title}</h4>
                                <Badge variant="outline" className={cn("text-xs", getStatusColor(emission.status))}>
                                  {emission.status}
                                </Badge>
                                {emission.humanRating && renderStarRating(emission.humanRating)}
                              </div>
                              <p className="text-sm text-muted-foreground leading-relaxed">{emission.description}</p>
                              {emission.humanFeedback && (
                                <p className="text-xs text-blue-300 bg-blue-500/10 p-2 rounded">
                                  "{emission.humanFeedback}"
                                </p>
                              )}
                              <div className="text-xs text-muted-foreground">
                                Reviewed {emission.reviewedAt?.toLocaleString()}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}

                {emissions.length === 0 && (
                  <div className="flex items-center justify-center h-64 text-muted-foreground">
                    <div className="text-center">
                      <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No task emissions yet</p>
                      <p className="text-sm">Agent emissions will appear here for review</p>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Review Panel & Constraints */}
      <div className="space-y-4">
        {/* Review Panel */}
        {selectedEmission && (
          <Card className="glass-effect">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Review Emission</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div>
                  <Label className="text-sm font-medium">Title</Label>
                  <p className="text-sm text-foreground mt-1">{selectedEmission.title}</p>
                </div>

                <div>
                  <Label className="text-sm font-medium">Reasoning</Label>
                  <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{selectedEmission.reasoning}</p>
                </div>

                {selectedEmission.suggestedAction && (
                  <div>
                    <Label className="text-sm font-medium">Suggested Action</Label>
                    <p className="text-sm text-blue-300 mt-1 leading-relaxed">{selectedEmission.suggestedAction}</p>
                  </div>
                )}

                {selectedEmission.status === "pending" && (
                  <>
                    <div>
                      <Label className="text-sm font-medium mb-2 block">Rating</Label>
                      {renderStarRating(reviewRating, true, setReviewRating)}
                    </div>

                    <div>
                      <Label htmlFor="feedback" className="text-sm font-medium">
                        Feedback (Optional)
                      </Label>
                      <Textarea
                        id="feedback"
                        placeholder="Provide feedback on this emission..."
                        value={reviewFeedback}
                        onChange={(e) => setReviewFeedback(e.target.value)}
                        className="mt-1 bg-background/50"
                        rows={3}
                      />
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button onClick={() => handleReview(selectedEmission.id, true)} className="flex-1" size="sm">
                        <ThumbsUp className="h-4 w-4 mr-2" />
                        Approve
                      </Button>
                      <Button
                        onClick={() => handleReview(selectedEmission.id, false)}
                        variant="destructive"
                        className="flex-1"
                        size="sm"
                      >
                        <ThumbsDown className="h-4 w-4 mr-2" />
                        Reject
                      </Button>
                    </div>
                  </>
                )}

                {selectedEmission.status !== "pending" && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Label className="text-sm font-medium">Status:</Label>
                      <Badge className={getStatusColor(selectedEmission.status)}>{selectedEmission.status}</Badge>
                    </div>
                    {selectedEmission.humanRating && (
                      <div className="flex items-center gap-2">
                        <Label className="text-sm font-medium">Rating:</Label>
                        {renderStarRating(selectedEmission.humanRating)}
                      </div>
                    )}
                    {selectedEmission.humanFeedback && (
                      <div>
                        <Label className="text-sm font-medium">Feedback:</Label>
                        <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
                          "{selectedEmission.humanFeedback}"
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Constraints & Guardrails */}
        <Card className="glass-effect">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-lg">
              <div className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-primary" />
                Constraints & Guardrails
              </div>
              <Button variant="ghost" size="sm" onClick={() => setIsEditingConstraints(!isEditingConstraints)}>
                <Edit3 className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Max Emissions/Hour</Label>
                {isEditingConstraints ? (
                  <Slider
                    value={[constraints.maxEmissionsPerHour]}
                    onValueChange={([value]) => setConstraints((prev) => ({ ...prev, maxEmissionsPerHour: value }))}
                    max={50}
                    min={1}
                    step={1}
                    className="mt-2"
                  />
                ) : (
                  <p className="text-sm text-muted-foreground mt-1">{constraints.maxEmissionsPerHour}</p>
                )}
              </div>

              <div>
                <Label className="text-sm font-medium">Min Confidence Threshold</Label>
                {isEditingConstraints ? (
                  <Slider
                    value={[constraints.minConfidenceThreshold * 100]}
                    onValueChange={([value]) =>
                      setConstraints((prev) => ({ ...prev, minConfidenceThreshold: value / 100 }))
                    }
                    max={100}
                    min={0}
                    step={5}
                    className="mt-2"
                  />
                ) : (
                  <p className="text-sm text-muted-foreground mt-1">
                    {Math.round(constraints.minConfidenceThreshold * 100)}%
                  </p>
                )}
              </div>

              <div>
                <Label className="text-sm font-medium">Escalation Threshold</Label>
                {isEditingConstraints ? (
                  <Slider
                    value={[constraints.escalationThreshold * 100]}
                    onValueChange={([value]) =>
                      setConstraints((prev) => ({ ...prev, escalationThreshold: value / 100 }))
                    }
                    max={100}
                    min={50}
                    step={5}
                    className="mt-2"
                  />
                ) : (
                  <p className="text-sm text-muted-foreground mt-1">
                    {Math.round(constraints.escalationThreshold * 100)}%
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Require Human Approval</Label>
                  {isEditingConstraints ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setConstraints((prev) => ({ ...prev, requireHumanApproval: !prev.requireHumanApproval }))
                      }
                    >
                      {constraints.requireHumanApproval ? "Enabled" : "Disabled"}
                    </Button>
                  ) : (
                    <Badge variant={constraints.requireHumanApproval ? "default" : "secondary"}>
                      {constraints.requireHumanApproval ? "Enabled" : "Disabled"}
                    </Badge>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Auto-approve High Confidence</Label>
                  {isEditingConstraints ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setConstraints((prev) => ({
                          ...prev,
                          autoApproveHighConfidence: !prev.autoApproveHighConfidence,
                        }))
                      }
                    >
                      {constraints.autoApproveHighConfidence ? "Enabled" : "Disabled"}
                    </Button>
                  ) : (
                    <Badge variant={constraints.autoApproveHighConfidence ? "default" : "secondary"}>
                      {constraints.autoApproveHighConfidence ? "Enabled" : "Disabled"}
                    </Badge>
                  )}
                </div>
              </div>

              {isEditingConstraints && (
                <Button onClick={() => setIsEditingConstraints(false)} className="w-full" size="sm">
                  <Save className="h-4 w-4 mr-2" />
                  Save Constraints
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
