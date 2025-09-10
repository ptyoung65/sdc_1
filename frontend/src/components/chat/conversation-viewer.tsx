"use client"

import * as React from "react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"
import { MessageSquare, Loader2 } from "lucide-react"

import { apiService, type Message as ApiMessage } from "@/services/api"
import { Message, MessageRole } from "@/types"
import { MessageBubble } from "./message-bubble"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"

interface ConversationViewerProps {
  conversationId: string | null
  isOpen: boolean
  onOpenChange: (open: boolean) => void
  userId?: string
}

// Convert API message format to frontend message format
const convertApiMessageToFrontend = (apiMessage: ApiMessage): Message => {
  return {
    id: apiMessage.id,
    content: apiMessage.content,
    role: apiMessage.role === 'user' ? MessageRole.USER : MessageRole.ASSISTANT,
    timestamp: apiMessage.created_at,
    conversationId: '', // Will be set by parent
    ...(apiMessage.metadata && { metadata: apiMessage.metadata }),
    ...(apiMessage.sources && { sources: apiMessage.sources })
  }
}

export function ConversationViewer({
  conversationId,
  isOpen,
  onOpenChange,
  userId = "default_user"
}: ConversationViewerProps) {
  const [messages, setMessages] = React.useState<Message[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  // Load messages when conversation ID changes
  React.useEffect(() => {
    if (!conversationId || !isOpen) {
      setMessages([])
      setError(null)
      return
    }

    const loadMessages = async () => {
      setIsLoading(true)
      setError(null)
      
      try {
        console.log('Loading messages for conversation:', conversationId)
        
        try {
          const apiMessages = await apiService.getConversationMessages(conversationId)
          
          const frontendMessages = apiMessages.map(msg => ({
            ...convertApiMessageToFrontend(msg),
            conversationId: conversationId
          }))
          
          console.log('Loaded messages:', frontendMessages.length)
          setMessages(frontendMessages)
        } catch (apiError) {
          console.error('API 서버 연결 실패:', apiError)
          
          // API 실패 시 fallback 메시지 생성
          const fallbackMessages: Message[] = [
            {
              id: 'fallback-msg-1',
              content: 'API 서버에 연결할 수 없습니다.',
              role: MessageRole.USER,
              timestamp: new Date(Date.now() - 60000).toISOString(),
              conversationId: conversationId || ''
            },
            {
              id: 'fallback-msg-2',
              content: '죄송합니다. 현재 백엔드 서버와의 연결에 문제가 있어 대화 내용을 불러올 수 없습니다. 백엔드 서버가 정상 작동하면 실제 대화 내용을 확인하실 수 있습니다.',
              role: MessageRole.ASSISTANT,
              timestamp: new Date(Date.now() - 30000).toISOString(),
              conversationId: conversationId || '',
              error: '백엔드 API 연결 실패'
            }
          ]
          
          console.log('Loaded fallback messages:', fallbackMessages.length)
          setMessages(fallbackMessages)
        }
      } catch (error) {
        console.error('Failed to load conversation messages:', error)
        setError('대화를 불러오는 중 오류가 발생했습니다.')
        setMessages([])
      } finally {
        setIsLoading(false)
      }
    }

    loadMessages()
  }, [conversationId, isOpen])

  const handleRateMessage = async (rating: number, feedback?: string) => {
    // Rating functionality can be implemented if needed
    console.log('Rating message:', rating, feedback)
  }

  const formatConversationTitle = (conversationId: string) => {
    return `대화 ${conversationId.slice(0, 8)}...`
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh] w-[95vw] sm:w-[90vw] flex flex-col overflow-hidden">
        <DialogHeader className="flex-shrink-0 pb-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            {conversationId ? formatConversationTitle(conversationId) : '대화 히스토리'}
          </DialogTitle>
          <DialogDescription>
            과거 대화 내용을 확인할 수 있습니다.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span className="text-sm text-muted-foreground">대화를 불러오는 중...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <MessageSquare className="h-12 w-12 text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground mb-1">{error}</p>
              <p className="text-xs text-muted-foreground">
                잠시 후 다시 시도해주세요
              </p>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <MessageSquare className="h-12 w-12 text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground mb-1">메시지가 없습니다</p>
              <p className="text-xs text-muted-foreground">
                이 대화에는 아직 메시지가 없습니다
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[65vh] sm:h-[70vh] pr-4">
              <div className="space-y-3 pb-4">
                {messages.map((message, index) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    showAvatar={true}
                    isLast={index === messages.length - 1}
                    currentUserId={userId}
                  />
                ))}
              </div>
            </ScrollArea>
          )}
        </div>

        {messages.length > 0 && (
          <div className="flex-shrink-0 flex items-center justify-between pt-4 border-t text-xs text-muted-foreground bg-background">
            <span>{messages.length}개의 메시지</span>
            {messages.length > 0 && (
              <span className="hidden sm:inline">
                마지막 업데이트: {format(new Date(messages[messages.length - 1]!.timestamp), "yyyy년 MM월 dd일 HH:mm", { locale: ko })}
              </span>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}