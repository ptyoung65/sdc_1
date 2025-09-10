"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  MessageSquare, 
  Plus, 
  MoreHorizontal, 
  Trash2, 
  Edit, 
  Archive,
  Search,
  Filter,
  Clock,
  Star,
  X,
  ChevronLeft,
  ChevronRight
} from "lucide-react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

import { cn, truncate } from "@/lib/utils"
import { Conversation } from "@/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"

// Hydration 이슈 해결을 위한 클라이언트 전용 날짜 표시 컴포넌트
const DateDisplay = ({ updatedAt }: { updatedAt: string }) => {
  const [formattedDate, setFormattedDate] = React.useState<string>("")

  React.useEffect(() => {
    try {
      const formatted = new Intl.DateTimeFormat('ko-KR', {
        month: 'short',
        day: 'numeric'
      }).format(new Date(updatedAt))
      setFormattedDate(formatted)
    } catch (error) {
      // 날짜 파싱 실패 시 기본값
      setFormattedDate("날짜 오류")
    }
  }, [updatedAt])

  return <span>{formattedDate}</span>
}

interface SidebarProps {
  conversations?: Conversation[]
  currentConversationId?: string
  onSelectConversation?: (conversationId: string) => void
  onNewConversation?: () => void
  onDeleteConversation?: (conversationId: string) => void
  onArchiveConversation?: (conversationId: string) => void
  isCollapsed?: boolean
  onToggleCollapsed?: () => void
  className?: string
}

export function Sidebar({
  conversations = [],
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onArchiveConversation,
  isCollapsed = false,
  onToggleCollapsed,
  className
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [filter, setFilter] = React.useState<"all" | "starred" | "archived">("all")

  // Mock conversations for demo
  const mockConversations: Conversation[] = React.useMemo(() => [
    {
      id: "1",
      title: "SDC Gen AI 프로젝트에 대해서",
      userId: "user1",
      messages: [],
      createdAt: "2024-01-15T10:30:00Z",
      updatedAt: "2024-01-15T11:45:00Z",
      tags: ["프로젝트", "AI"]
    },
    {
      id: "2", 
      title: "Next.js 14 새로운 기능들",
      userId: "user1",
      messages: [],
      createdAt: "2024-01-14T09:15:00Z",
      updatedAt: "2024-01-14T09:30:00Z",
      tags: ["개발", "React"]
    },
    {
      id: "3",
      title: "한국어 임베딩 모델 KURE-v1 성능 비교",
      userId: "user1", 
      messages: [],
      createdAt: "2024-01-13T16:20:00Z",
      updatedAt: "2024-01-13T16:45:00Z",
      tags: ["AI", "한국어"]
    },
    {
      id: "4",
      title: "Docker와 Podman의 차이점",
      userId: "user1",
      messages: [],
      createdAt: "2024-01-12T14:10:00Z", 
      updatedAt: "2024-01-12T14:25:00Z",
      tags: ["DevOps", "컨테이너"]
    }
  ], [])

  const displayConversations = conversations.length > 0 ? conversations : mockConversations

  // Filter conversations based on search query and filter
  const filteredConversations = React.useMemo(() => {
    let filtered = displayConversations

    if (searchQuery) {
      filtered = filtered.filter(conv => 
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    if (filter === "starred") {
      // filtered = filtered.filter(conv => conv.isStarred)
    } else if (filter === "archived") {
      filtered = filtered.filter(conv => conv.isArchived)
    } else {
      filtered = filtered.filter(conv => !conv.isArchived)
    }

    return filtered.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
  }, [displayConversations, searchQuery, filter])

  const handleNewConversation = () => {
    onNewConversation?.()
  }

  const handleSelectConversation = (conversationId: string) => {
    onSelectConversation?.(conversationId)
  }

  const handleDeleteConversation = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onDeleteConversation?.(conversationId)
  }

  const handleArchiveConversation = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onArchiveConversation?.(conversationId)
  }

  const sidebarVariants = {
    expanded: { width: "280px" },
    collapsed: { width: "60px" }
  }

  const contentVariants = {
    expanded: { opacity: 1, x: 0 },
    collapsed: { opacity: 0, x: -10 }
  }

  return (
    <motion.aside
      variants={sidebarVariants}
      animate={isCollapsed ? "collapsed" : "expanded"}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className={cn(
        "border-r bg-card flex flex-col overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <AnimatePresence>
          {!isCollapsed && (
            <motion.h2
              variants={contentVariants}
              initial="collapsed"
              animate="expanded"
              exit="collapsed"
              className="font-medium text-sm text-foreground/80"
            >
              대화
            </motion.h2>
          )}
        </AnimatePresence>
        
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size={isCollapsed ? "icon" : "sm"}
            onClick={handleNewConversation}
            className="shrink-0 h-7 w-7 p-0"
          >
            <Plus className="h-3.5 w-3.5" />
            {!isCollapsed && <span className="ml-1 text-xs">새 대화</span>}
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapsed}
            className="shrink-0 h-7 w-7 p-0"
          >
            {isCollapsed ? (
              <ChevronRight className="h-3.5 w-3.5" />
            ) : (
              <ChevronLeft className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </div>

      {/* Search Only */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            variants={contentVariants}
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            className="px-4 pb-4"
          >
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
              <Input
                type="search"
                placeholder="검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-7 text-xs bg-muted/50 border-0"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Conversations List */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-2">
            <AnimatePresence>
              {filteredConversations.map((conversation, index) => (
                <motion.div
                  key={conversation.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn(
                    "group relative flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors mb-2",
                    "hover:bg-muted/50",
                    currentConversationId === conversation.id && "bg-primary/10 border border-primary/20"
                  )}
                  onClick={() => handleSelectConversation(conversation.id)}
                >
                  {/* Icon */}
                  <div className="shrink-0">
                    <div className="h-8 w-8 bg-muted rounded-lg flex items-center justify-center">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>

                  <AnimatePresence>
                    {!isCollapsed && (
                      <motion.div
                        variants={contentVariants}
                        initial="collapsed"
                        animate="expanded"
                        exit="collapsed"
                        className="flex-1 min-w-0"
                      >
                        {/* Title */}
                        <h3 className="font-medium text-sm truncate mb-1">
                          {truncate(conversation.title, 25)}
                        </h3>
                        
                        {/* Metadata */}
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <DateDisplay updatedAt={conversation.updatedAt} />
                          {conversation.messages.length > 0 && (
                            <>
                              <span>•</span>
                              <span>{conversation.messages.length}개 메시지</span>
                            </>
                          )}
                        </div>

                        {/* Tags */}
                        {conversation.tags && conversation.tags.length > 0 && (
                          <div className="flex gap-1 mt-2">
                            {conversation.tags.slice(0, 2).map(tag => (
                              <Badge
                                key={tag}
                                variant="secondary"
                                className="text-xs px-2 py-0 h-5"
                              >
                                {tag}
                              </Badge>
                            ))}
                            {conversation.tags.length > 2 && (
                              <Badge variant="outline" className="text-xs px-2 py-0 h-5">
                                +{conversation.tags.length - 2}
                              </Badge>
                            )}
                          </div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Actions */}
                  <AnimatePresence>
                    {!isCollapsed && (
                      <motion.div
                        variants={contentVariants}
                        initial="collapsed"
                        animate="expanded"
                        exit="collapsed"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-6 w-6">
                              <MoreHorizontal className="h-3 w-3" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Edit className="mr-2 h-4 w-4" />
                              이름 변경
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Star className="mr-2 h-4 w-4" />
                              즐겨찾기 추가
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => handleArchiveConversation(conversation.id, e)}
                            >
                              <Archive className="mr-2 h-4 w-4" />
                              보관
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={(e) => handleDeleteConversation(conversation.id, e)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              삭제
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Empty State */}
            {filteredConversations.length === 0 && !isCollapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center py-12 text-center"
              >
                <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mb-4">
                  <MessageSquare className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground mb-2">
                  {searchQuery ? "검색 결과가 없습니다" : "대화가 없습니다"}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNewConversation}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  새 대화 시작
                </Button>
              </motion.div>
            )}
          </div>
        </ScrollArea>
      </div>
    </motion.aside>
  )
}