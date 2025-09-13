"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { User, Bot, Copy, Check, MoreVertical } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

import { cn, copyToClipboard } from "@/lib/utils"
import { Message, MessageRole } from "@/types"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { CompactMessageRating } from "./message-rating"
import { MultiRAGResponse } from "./multi-rag-response"
import type { RAGResult } from "@/services/api"

interface MessageBubbleProps {
  message: Message
  showAvatar?: boolean
  isLast?: boolean
  className?: string
  onRate?: (rating: number, feedback?: string) => void
  currentUserId?: string
}

// 클라이언트 전용 시간 표시 컴포넌트
function TimeDisplay({ timestamp }: { timestamp: string }) {
  const [mounted, setMounted] = React.useState(false)
  
  React.useEffect(() => {
    setMounted(true)
  }, [])
  
  if (!mounted) {
    // 서버/첫 렌더링에서는 절대 시간 표시
    const d = new Date(timestamp)
    return (
      <span suppressHydrationWarning>
        {new Intl.DateTimeFormat('ko-KR', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }).format(d)}
      </span>
    )
  }
  
  // 클라이언트에서는 상대 시간 표시
  const d = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  let timeString = ''
  if (days > 7) {
    timeString = new Intl.DateTimeFormat('ko-KR', {
      month: 'short',
      day: 'numeric',
    }).format(d)
  } else if (days > 0) {
    timeString = `${days}일 전`
  } else if (hours > 0) {
    timeString = `${hours}시간 전`
  } else if (minutes > 0) {
    timeString = `${minutes}분 전`
  } else {
    timeString = '방금 전'
  }
  
  return <span>{timeString}</span>
}

export function MessageBubble({
  message,
  showAvatar = true,
  isLast = false,
  className,
  onRate,
  currentUserId
}: MessageBubbleProps) {
  const [copied, setCopied] = React.useState(false)
  const [isVisible, setIsVisible] = React.useState(false)
  
  const isUser = message.role === MessageRole.USER
  const isAssistant = message.role === MessageRole.ASSISTANT
  const isSystem = message.role === MessageRole.SYSTEM

  React.useEffect(() => {
    setIsVisible(true)
  }, [])

  const handleCopy = async () => {
    const success = await copyToClipboard(message.content)
    if (success) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const messageVariants = {
    initial: { 
      opacity: 0, 
      y: 20, 
      scale: 0.95 
    },
    animate: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: {
        duration: 0.3,
        ease: "easeOut"
      }
    }
  }

  if (isSystem) {
    return (
      <motion.div
        variants={messageVariants}
        initial="initial"
        animate="animate"
        className={cn(
          "flex justify-center my-4",
          className
        )}
      >
        <div className="px-4 py-2 bg-muted rounded-lg text-sm text-muted-foreground">
          {message.content}
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      variants={messageVariants}
      initial="initial"
      animate={isVisible ? "animate" : "initial"}
      className={cn(
        "group flex gap-3 px-4 py-3 hover:bg-muted/30 transition-colors",
        isUser && "justify-end",
        className
      )}
    >
      {/* Avatar - Only show for assistant messages or when specifically requested */}
      {showAvatar && !isUser && (
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      {/* Message Content */}
      <div className={cn(
        "flex flex-col gap-1 max-w-[80%]",
        isUser && "items-end"
      )}>
        {/* Message Bubble */}
        <Card className={cn(
          "px-4 py-3 shadow-sm border-0",
          isUser 
            ? "bg-primary text-primary-foreground rounded-2xl rounded-br-sm" 
            : "bg-card rounded-2xl rounded-bl-sm",
          message.error && "bg-destructive/10 border border-destructive/20"
        )}>
          {message.error ? (
            <div className="text-destructive text-sm">
              <p className="font-medium">오류가 발생했습니다</p>
              <p className="mt-1 opacity-90">{message.error}</p>
            </div>
          ) : (
            <div className={cn(
              "chat-message text-sm",
              isUser ? "text-primary-foreground" : "text-foreground"
            )}>
              {isUser ? (
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    code: ({ node, inline, className, children, ...props }: any) => (
                      <code
                        className={cn(
                          inline 
                            ? "bg-muted px-1.5 py-0.5 rounded text-xs font-mono" 
                            : "block bg-muted p-4 rounded-md text-xs font-mono overflow-x-auto",
                          className
                        )}
                        {...props}
                      >
                        {children}
                      </code>
                    ),
                    p: ({ children }) => (
                      <p className="mb-2 last:mb-0">{children}</p>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              )}
            </div>
          )}

          {/* Multi-RAG Results - Hidden for now */}
          {false && isAssistant && message.metadata?.hasMultiRAG && message.metadata?.ragResults && (
            <div className="mt-3 pt-3 border-t border-border/50">
              <MultiRAGResponse
                ragResults={message.metadata?.ragResults as RAGResult[] || []}
                finalResponse={message.content}
                className="text-xs"
              />
            </div>
          )}

          {/* Sources - Only for assistant messages */}
          {isAssistant && message.sources && message.sources.length > 0 && !message.metadata?.hasMultiRAG && (
            <div className="mt-3 pt-3 border-t border-border/50">
              <p className="text-xs font-medium mb-2 opacity-70">참고 문서:</p>
              <div className="space-y-1">
                {message.sources.map((source, index) => (
                  <div
                    key={`${source.id}-${index}`}
                    className="text-xs p-2 bg-muted/50 rounded text-muted-foreground hover:bg-muted/70 transition-colors cursor-pointer"
                  >
                    <div className="font-medium truncate">{source.title}</div>
                    {source.snippet && (
                      <div className="mt-1 opacity-80 line-clamp-2">
                        {source.snippet}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Message Footer */}
        <div className={cn(
          "flex items-center gap-2 text-xs text-muted-foreground px-2",
          isUser && "justify-end"
        )}>
          <TimeDisplay timestamp={message.timestamp} />
          
          {/* Message metadata */}
          {message.metadata && (
            <>
              {message.metadata.model && (
                <span>• {message.metadata.model}</span>
              )}
              {message.metadata.processingTime && (
                <span>• {message.metadata.processingTime.toFixed(1)}초</span>
              )}
              {message.metadata.confidence && (
                <span>• 신뢰도 {Math.round(message.metadata.confidence * 100)}%</span>
              )}
            </>
          )}

          {/* Actions */}
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {/* Rating - Only for assistant messages */}
            {isAssistant && onRate && currentUserId && (
              <CompactMessageRating
                messageId={message.id}
                userId={currentUserId}
                currentRating={message.rating || 0}
                onRate={onRate}
                className="mr-1"
              />
            )}
            
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleCopy}
            >
              {copied ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <MoreVertical className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleCopy}>
                  복사하기
                </DropdownMenuItem>
                <DropdownMenuItem>
                  다시 생성
                </DropdownMenuItem>
                <DropdownMenuItem className="text-destructive">
                  삭제
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* User Avatar */}
      {showAvatar && isUser && (
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className="bg-secondary">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  )
}