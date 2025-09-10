"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { MessageSquare, Plus, Trash2, ChevronLeft, ChevronRight } from "lucide-react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { apiService, type Conversation } from "@/services/api"

interface ConversationSidebarProps {
  currentConversationId?: string
  onSelectConversation: (conversationId: string) => void
  onNewConversation: () => void
  userId: string
  className?: string
}

export function ConversationSidebar({
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  userId,
  className
}: ConversationSidebarProps) {
  const [conversations, setConversations] = React.useState<Conversation[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [currentPage, setCurrentPage] = React.useState(1)
  const [totalConversations, setTotalConversations] = React.useState(0)
  const [isCollapsed, setIsCollapsed] = React.useState(false)

  const itemsPerPage = 5
  const totalPages = Math.ceil(totalConversations / itemsPerPage)

  const fetchConversations = async (page: number = 1) => {
    setIsLoading(true)
    try {
      const offset = (page - 1) * itemsPerPage
      const response = await apiService.getUserConversations(userId, itemsPerPage, offset)
      setConversations(response)
      
      // Get total count from first page response
      if (page === 1) {
        // Make a request to get total count
        const totalResponse = await apiService.getUserConversations(userId, 1000, 0)
        setTotalConversations(totalResponse.length)
      }
    } catch (error) {
      console.error("Failed to fetch conversations:", error)
      setConversations([])
    } finally {
      setIsLoading(false)
    }
  }

  React.useEffect(() => {
    fetchConversations(currentPage)
  }, [userId, currentPage])

  const handleDeleteConversation = async (conversationId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      const success = await apiService.deleteConversation(conversationId, userId)
      if (success) {
        fetchConversations(currentPage)
        // If current conversation was deleted, start new conversation
        if (conversationId === currentConversationId) {
          onNewConversation()
        }
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error)
    }
  }

  const formatConversationTitle = (conversation: Conversation) => {
    if (conversation.title && conversation.title !== "New Chat") {
      return conversation.title
    }
    return `대화 ${format(new Date(conversation.created_at), "MM/dd HH:mm", { locale: ko })}`
  }

  const formatConversationTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) {
      return format(date, "HH:mm", { locale: ko })
    } else if (days < 7) {
      return `${days}일 전`
    } else {
      return format(date, "MM/dd", { locale: ko })
    }
  }

  if (isCollapsed) {
    return (
      <motion.div
        initial={{ width: 280 }}
        animate={{ width: 60 }}
        className={cn("border-r bg-muted/20 flex flex-col", className)}
      >
        <div className="p-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(false)}
            className="w-full"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ width: 60 }}
      animate={{ width: 280 }}
      className={cn("border-r bg-muted/20 flex flex-col", className)}
    >
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-sm">대화 목록</h2>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={onNewConversation}
              className="h-8 w-8"
            >
              <Plus className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsCollapsed(true)}
              className="h-8 w-8"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Conversation List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="h-16 bg-muted animate-pulse rounded-md"
                />
              ))}
            </div>
          ) : conversations.length > 0 ? (
            <AnimatePresence>
              {conversations.map((conversation, index) => (
                <motion.div
                  key={conversation.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card
                    className={cn(
                      "p-3 mb-2 cursor-pointer hover:bg-accent/50 transition-colors group",
                      currentConversationId === conversation.id && "bg-accent border-primary"
                    )}
                    onClick={() => onSelectConversation(conversation.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <MessageSquare className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                          <span className="text-xs text-muted-foreground">
                            {conversation.message_count}개 메시지
                          </span>
                        </div>
                        <h3 className="font-medium text-sm truncate">
                          {formatConversationTitle(conversation)}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatConversationTime(conversation.updated_at)}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => handleDeleteConversation(conversation.id, e)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">아직 대화가 없습니다</p>
              <p className="text-xs mt-1">새 대화를 시작해보세요</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-4 border-t">
          <div className="flex items-center justify-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="h-8 w-8 p-0"
            >
              <ChevronLeft className="h-3 w-3" />
            </Button>
            
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = i + Math.max(1, currentPage - 2)
              if (page > totalPages) return null
              
              return (
                <Button
                  key={page}
                  variant={currentPage === page ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCurrentPage(page)}
                  className="h-8 w-8 p-0 text-xs"
                >
                  {page}
                </Button>
              )
            })}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="h-8 w-8 p-0"
            >
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
          <p className="text-xs text-center text-muted-foreground mt-2">
            {currentPage} / {totalPages} 페이지
          </p>
        </div>
      )}
    </motion.div>
  )
}