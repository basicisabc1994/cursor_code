"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  FolderOpen,
  File,
  FileText,
  FileCode,
  FileImage,
  FileVideo,
  FileAudio,
  Download,
  Eye,
  MoreVertical,
  Search,
  Filter,
  Calendar,
  User,
  HardDrive,
  Trash2,
  Share,
  Copy,
} from "lucide-react"

interface Asset {
  id: string
  name: string
  type: "document" | "code" | "image" | "video" | "audio" | "data"
  size: number
  createdAt: Date
  createdBy: "chat-agent" | "worker-agent" | "user"
  description: string
  tags: string[]
  status: "active" | "archived" | "processing"
}

const SAMPLE_ASSETS: Asset[] = [
  {
    id: "1",
    name: "conversation-summary.md",
    type: "document",
    size: 15420,
    createdAt: new Date("2024-01-15T10:30:00"),
    createdBy: "chat-agent",
    description: "Comprehensive summary of user interactions and key insights",
    tags: ["summary", "insights", "conversation"],
    status: "active",
  },
  {
    id: "2",
    name: "reasoning-chain.json",
    type: "data",
    size: 8934,
    createdAt: new Date("2024-01-15T11:15:00"),
    createdBy: "worker-agent",
    description: "Detailed reasoning chain for complex problem solving",
    tags: ["reasoning", "logic", "analysis"],
    status: "active",
  },
  {
    id: "3",
    name: "user-preferences.py",
    type: "code",
    size: 5672,
    createdAt: new Date("2024-01-15T09:45:00"),
    createdBy: "chat-agent",
    description: "Generated code for user preference management system",
    tags: ["code", "preferences", "python"],
    status: "active",
  },
  {
    id: "4",
    name: "learning-visualization.png",
    type: "image",
    size: 234567,
    createdAt: new Date("2024-01-15T12:00:00"),
    createdBy: "worker-agent",
    description: "Visual representation of learning progress and patterns",
    tags: ["visualization", "learning", "chart"],
    status: "active",
  },
  {
    id: "5",
    name: "memory-dump.txt",
    type: "document",
    size: 45123,
    createdAt: new Date("2024-01-15T08:20:00"),
    createdBy: "worker-agent",
    description: "Complete memory state dump for debugging purposes",
    tags: ["memory", "debug", "system"],
    status: "archived",
  },
  {
    id: "6",
    name: "api-integration.js",
    type: "code",
    size: 12890,
    createdAt: new Date("2024-01-15T13:30:00"),
    createdBy: "chat-agent",
    description: "JavaScript code for external API integration",
    tags: ["api", "integration", "javascript"],
    status: "processing",
  },
]

const getFileIcon = (type: Asset["type"]) => {
  switch (type) {
    case "document":
      return <FileText className="h-4 w-4" />
    case "code":
      return <FileCode className="h-4 w-4" />
    case "image":
      return <FileImage className="h-4 w-4" />
    case "video":
      return <FileVideo className="h-4 w-4" />
    case "audio":
      return <FileAudio className="h-4 w-4" />
    case "data":
      return <File className="h-4 w-4" />
    default:
      return <File className="h-4 w-4" />
  }
}

const getCreatorBadge = (creator: Asset["createdBy"]) => {
  switch (creator) {
    case "chat-agent":
      return (
        <Badge variant="default" className="text-xs">
          Chat Agent
        </Badge>
      )
    case "worker-agent":
      return (
        <Badge variant="secondary" className="text-xs">
          Worker Agent
        </Badge>
      )
    case "user":
      return (
        <Badge variant="outline" className="text-xs">
          User
        </Badge>
      )
  }
}

const getStatusBadge = (status: Asset["status"]) => {
  switch (status) {
    case "active":
      return (
        <Badge variant="default" className="text-xs bg-green-500/20 text-green-300 border-green-500/30">
          Active
        </Badge>
      )
    case "archived":
      return (
        <Badge variant="secondary" className="text-xs">
          Archived
        </Badge>
      )
    case "processing":
      return (
        <Badge variant="outline" className="text-xs bg-yellow-500/20 text-yellow-300 border-yellow-500/30">
          Processing
        </Badge>
      )
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

export function AssetsManager() {
  const [assets, setAssets] = useState<Asset[]>(SAMPLE_ASSETS)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedType, setSelectedType] = useState<string>("all")
  const [selectedCreator, setSelectedCreator] = useState<string>("all")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")

  const filteredAssets = assets.filter((asset) => {
    const matchesSearch =
      asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesType = selectedType === "all" || asset.type === selectedType
    const matchesCreator = selectedCreator === "all" || asset.createdBy === selectedCreator

    return matchesSearch && matchesType && matchesCreator
  })

  const totalSize = assets.reduce((sum, asset) => sum + asset.size, 0)
  const activeAssets = assets.filter((asset) => asset.status === "active").length
  const typeDistribution = assets.reduce(
    (acc, asset) => {
      acc[asset.type] = (acc[asset.type] || 0) + 1
      return acc
    },
    {} as Record<string, number>,
  )

  return (
    <div className="space-y-6">
      {/* Assets Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-effect">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">{assets.length}</div>
            <p className="text-xs text-muted-foreground">{activeAssets} active</p>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-accent">{formatFileSize(totalSize)}</div>
            <p className="text-xs text-muted-foreground">Across all assets</p>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Most Common</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-chart-3">
              {Object.entries(typeDistribution).sort(([, a], [, b]) => b - a)[0]?.[0] || "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              {Object.entries(typeDistribution).sort(([, a], [, b]) => b - a)[0]?.[1] || 0} files
            </p>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-chart-4">
              {assets.filter((asset) => new Date().getTime() - asset.createdAt.getTime() < 24 * 60 * 60 * 1000).length}
            </div>
            <p className="text-xs text-muted-foreground">Created today</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="glass-effect">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search assets by name, description, or tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" className="flex items-center gap-2 bg-transparent">
                    <Filter className="h-4 w-4" />
                    Type: {selectedType === "all" ? "All" : selectedType}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => setSelectedType("all")}>All Types</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSelectedType("document")}>Documents</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSelectedType("code")}>Code</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSelectedType("image")}>Images</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSelectedType("data")}>Data</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" className="flex items-center gap-2 bg-transparent">
                    <User className="h-4 w-4" />
                    Creator: {selectedCreator === "all" ? "All" : selectedCreator}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => setSelectedCreator("all")}>All Creators</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSelectedCreator("chat-agent")}>Chat Agent</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSelectedCreator("worker-agent")}>Worker Agent</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSelectedCreator("user")}>User</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Assets Grid/List */}
      <Card className="glass-effect">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-primary" />
              Assets ({filteredAssets.length})
            </CardTitle>
            <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as "grid" | "list")}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="grid">Grid</TabsTrigger>
                <TabsTrigger value="list">List</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>
        <CardContent>
          {viewMode === "grid" ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredAssets.map((asset) => (
                <Card key={asset.id} className="glass-effect hover:bg-card/80 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {getFileIcon(asset.type)}
                        <span className="font-medium text-sm truncate">{asset.name}</span>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Eye className="h-4 w-4 mr-2" />
                            View
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Share className="h-4 w-4 mr-2" />
                            Share
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Copy className="h-4 w-4 mr-2" />
                            Copy Link
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-red-400">
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{asset.description}</p>

                    <div className="flex flex-wrap gap-1 mb-3">
                      {asset.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {asset.tags.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{asset.tags.length - 3}
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        {getCreatorBadge(asset.createdBy)}
                        {getStatusBadge(asset.status)}
                      </div>
                      <span>{formatFileSize(asset.size)}</span>
                    </div>

                    <div className="text-xs text-muted-foreground mt-2">
                      {asset.createdAt.toLocaleDateString()} {asset.createdAt.toLocaleTimeString()}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredAssets.map((asset) => (
                <div
                  key={asset.id}
                  className="flex items-center gap-4 p-3 rounded-lg bg-card/30 hover:bg-card/50 transition-colors"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {getFileIcon(asset.type)}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{asset.name}</div>
                      <div className="text-xs text-muted-foreground truncate">{asset.description}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {getCreatorBadge(asset.createdBy)}
                    {getStatusBadge(asset.status)}
                  </div>

                  <div className="text-xs text-muted-foreground text-right">
                    <div>{formatFileSize(asset.size)}</div>
                    <div>{asset.createdAt.toLocaleDateString()}</div>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Eye className="h-4 w-4 mr-2" />
                        View
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Share className="h-4 w-4 mr-2" />
                        Share
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Copy className="h-4 w-4 mr-2" />
                        Copy Link
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-red-400">
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </div>
          )}

          {filteredAssets.length === 0 && (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
              <div className="text-center">
                <FolderOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No assets found</p>
                <p className="text-sm">Try adjusting your search or filters</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
