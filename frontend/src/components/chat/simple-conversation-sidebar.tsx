"use client"

import * as React from "react"
import { MessageSquare, Plus, Trash2, Star, ChevronLeft, ChevronRight } from "lucide-react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Pagination, PaginationInfo } from "@/components/ui/pagination"
import { apiService, type Conversation } from "@/services/api"
import { ConversationViewer } from "./conversation-viewer"
import { truncate } from "@/lib/utils"

interface SimpleConversationSidebarProps {
  userId: string
  className?: string
}

// 대화와 첫 번째 질문을 포함한 확장 타입
interface ConversationWithPreview {
  id: string
  title?: string
  created_at: string
  updated_at: string
  message_count: number
  firstQuestion?: string
  isPreviewLoading?: boolean
  averageRating?: number
  isRatingLoading?: boolean
}

export function SimpleConversationSidebar({ userId, className }: SimpleConversationSidebarProps) {
  const [conversations, setConversations] = React.useState<ConversationWithPreview[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [selectedConversationId, setSelectedConversationId] = React.useState<string | null>(null)
  const [isViewerOpen, setIsViewerOpen] = React.useState(false)
  
  // 사이드바 접기/펼치기 상태
  const [isCollapsed, setIsCollapsed] = React.useState(false)
  const [isMobile, setIsMobile] = React.useState(false)
  
  // 페이지네이션 상태
  const [currentPage, setCurrentPage] = React.useState(1)
  const [totalPages, setTotalPages] = React.useState(1)
  const [totalItems, setTotalItems] = React.useState(0)
  const itemsPerPage = 7

  // 반응형 처리
  React.useEffect(() => {
    const checkMobile = () => {
      const width = window.innerWidth
      const newIsMobile = width < 768 // md breakpoint
      setIsMobile(newIsMobile)
      
      // 모바일에서는 자동으로 사이드바 접기
      if (newIsMobile && !isCollapsed) {
        setIsCollapsed(true)
      }
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [isCollapsed])

  const fetchConversations = React.useCallback(async (page: number = 1) => {
    setIsLoading(true)
    try {
      console.log('Fetching conversations for user:', userId, 'page:', page)
      const offset = (page - 1) * itemsPerPage
      
      let response
      try {
        response = await apiService.getUserConversations(userId, itemsPerPage, offset)
        console.log('API Response:', response)
      } catch (apiError) {
        console.error('API 서버 연결 실패:', apiError)
        // API 서버가 연결되지 않을 때 fallback 데이터 생성
        response = Array.from({ length: 3 }, (_, i) => ({
          id: `fallback-conv-${i + 1}`,
          title: i === 0 ? "API 연결 오류 - 샘플 대화" : `Fallback 대화 ${i + 1}`,
          created_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
          message_count: 2
        }))
      }
      
      // 총 아이템 수 계산 (실제 API에서 total을 제공하지 않는 경우 추정)
      const actualTotal = response.length < itemsPerPage && page === 1 
        ? response.length 
        : response.length === itemsPerPage 
          ? (page * itemsPerPage) + 1 // 다음 페이지가 있을 수 있음을 추정
          : (page - 1) * itemsPerPage + response.length
      
      setTotalItems(actualTotal)
      setTotalPages(Math.ceil(actualTotal / itemsPerPage))
      
      // ConversationWithPreview 타입으로 변환
      const conversationsWithPreview = response.map((conv, index) => ({
        id: conv.id,
        title: conv.title,
        created_at: conv.created_at,
        updated_at: conv.updated_at,
        message_count: conv.message_count,
        firstQuestion: undefined as string | undefined, // 실제 API에서 가져올 예정
        isPreviewLoading: false as boolean,
        averageRating: undefined as number | undefined,
        isRatingLoading: false as boolean
      })) as ConversationWithPreview[]
      
      setConversations(conversationsWithPreview)
      
      // 실제 API 데이터인 경우 질문 미리보기 로드
      if (!response.some(conv => conv.id.startsWith('fallback-'))) {
        loadQuestionPreviews(conversationsWithPreview)
      } else {
        // fallback 데이터의 경우 간단한 미리보기 설정
        setConversations(prev => prev.map((c, idx) => ({
          ...c,
          firstQuestion: idx === 0 
            ? "API 연결이 복구되면 실제 대화를 볼 수 있습니다."
            : `Fallback 대화 ${idx + 1}의 미리보기입니다.`
        })))
      }
    } catch (error) {
      console.error("Failed to fetch conversations:", error)
      setConversations([])
      setTotalItems(0)
      setTotalPages(1)
    } finally {
      setIsLoading(false)
    }
  }, [userId, itemsPerPage])
  
  // 질문 미리보기를 비동기로 로드하는 함수 (성능 최적화)
  const loadQuestionPreviews = async (convs: ConversationWithPreview[]) => {
    // 각 대화의 첫 번째 메시지만 가져와서 질문 미리보기로 설정
    convs.forEach(async (conv) => {
      try {
        setConversations(prev => prev.map(c => 
          c.id === conv.id ? { ...c, isPreviewLoading: true } : c
        ))
        
        const messages = await apiService.getConversationMessages(conv.id)
        const firstUserMessage = messages.find(msg => msg.role === 'user')
        
        setConversations(prev => prev.map(c => 
          c.id === conv.id 
            ? { 
                ...c, 
                firstQuestion: firstUserMessage ? truncate(firstUserMessage.content, 35) : '질문 없음',
                isPreviewLoading: false,
                // 평점은 일단 기본값으로 설정 (나중에 필요시 로드)
                averageRating: undefined,
                isRatingLoading: false
              } as unknown as ConversationWithPreview
            : c
        ))
      } catch (error) {
        console.error('Failed to load preview for conversation:', conv.id, error)
        setConversations(prev => prev.map(c => 
          c.id === conv.id 
            ? { 
                ...c, 
                firstQuestion: '미리보기를 불러올 수 없음', 
                isPreviewLoading: false,
                averageRating: undefined,
                isRatingLoading: false
              } as unknown as ConversationWithPreview
            : c
        ))
      }
    })
  }

  // 특정 대화의 평점을 지연 로드하는 함수
  const loadRatingForConversation = async (conversationId: string) => {
    try {
      setConversations(prev => prev.map(c => 
        c.id === conversationId ? { ...c, isRatingLoading: true } : c
      ))
      
      const messages = await apiService.getConversationMessages(conversationId)
      const assistantMessages = messages.filter(msg => msg.role === 'assistant')
      
      if (assistantMessages.length === 0) {
        setConversations(prev => prev.map(c => 
          c.id === conversationId ? { ...c, averageRating: undefined, isRatingLoading: false } as unknown as ConversationWithPreview : c
        ))
        return
      }
      
      // 첫 번째 assistant 메시지의 평점만 가져오기 (성능 최적화)
      const firstAssistantMessage = assistantMessages[0]
      if (!firstAssistantMessage) return
      const ratingData = await apiService.getMessageRating(firstAssistantMessage.id, userId)
      
      setConversations(prev => prev.map(c => 
        c.id === conversationId 
          ? { ...c, averageRating: ratingData?.rating || undefined, isRatingLoading: false } as ConversationWithPreview
          : c
      ))
    } catch (error) {
      console.error('Failed to load rating for conversation:', conversationId, error)
      setConversations(prev => prev.map(c => 
        c.id === conversationId ? { ...c, averageRating: undefined, isRatingLoading: false } as unknown as ConversationWithPreview : c
      ))
    }
  }

  // 페이지 변경 핸들러
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    fetchConversations(page)
  }

  React.useEffect(() => {
    fetchConversations(currentPage)
  }, [fetchConversations, currentPage])

  const formatConversationTitle = (conversation: any) => {
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

  // 평점 표시 컴포넌트 (성능 최적화: 기본적으로는 평점 숨김)
  const RatingDisplay = ({ rating, isLoading }: { rating: number | undefined, isLoading: boolean }) => {
    // 성능 최적화를 위해 평점 섹션을 임시로 숨김
    return null
    
    /* 평점 기능이 필요할 때 아래 코드 활성화
    if (isLoading) {
      return (
        <div className="flex items-center gap-1">
          <Star className="h-3 w-3 text-muted-foreground animate-pulse" />
          <span className="text-xs text-muted-foreground animate-pulse">...</span>
        </div>
      )
    }
    
    if (rating === undefined || rating === null) {
      return null // 평점이 없으면 표시하지 않음
    }
    
    return (
      <div className="flex items-center gap-1">
        <Star className={`h-3 w-3 ${rating >= 4 ? 'text-yellow-500 fill-current' : rating >= 3 ? 'text-yellow-500' : 'text-muted-foreground'}`} />
        <span className={`text-xs ${rating >= 4 ? 'text-yellow-600' : rating >= 3 ? 'text-yellow-600' : 'text-muted-foreground'}`}>
          {rating.toFixed(1)}
        </span>
      </div>
    )
    */
  }

  return (
    <div className={`relative transition-all duration-300 ease-in-out ${
      isCollapsed ? 'w-12' : 'w-70 sm:w-70'
    } flex-shrink-0 border-r border-border bg-background/95 backdrop-blur-sm flex flex-col min-h-0 shadow-sm overflow-hidden`} 
    style={{
      width: isCollapsed ? '48px' : '280px', 
      maxWidth: isCollapsed ? '48px' : '280px'
    }}>
      {/* Header */}
      <div className="p-3 border-b">
        <div className="flex items-center justify-between">
          {!isCollapsed && <h2 className="font-semibold text-sm">대화 목록</h2>}
          <div className="flex gap-1">
            {!isCollapsed && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => window.location.reload()}
                className="h-8 w-8"
              >
                <Plus className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Collapse/Expand Button */}
      <div className="absolute -right-3 top-4 z-10">
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="h-6 w-6 rounded-full bg-background shadow-md hover:shadow-lg transition-all duration-200"
        >
          {isCollapsed ? (
            <ChevronRight className="h-3 w-3" />
          ) : (
            <ChevronLeft className="h-3 w-3" />
          )}
        </Button>
      </div>

      {/* Conversation List */}
      {isCollapsed ? (
        // 접혔을 때 최소 UI
        <div className="flex-1 flex flex-col items-center justify-center py-4">
          <div className="space-y-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => window.location.reload()}
              className="h-8 w-8"
              title="새 대화"
            >
              <Plus className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              title="대화 목록"
            >
              <MessageSquare className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ) : (
        <ScrollArea className="flex-1 overflow-hidden">
          <div className="p-2 max-w-full overflow-hidden">
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
            <>
              {conversations.map((conversation) => (
                <Card
                  key={conversation.id}
                  className="p-2.5 mb-2 cursor-pointer hover:bg-accent/50 transition-colors group overflow-hidden max-w-full"
                  style={{maxWidth: '264px'}} // 280px - 16px padding = 264px
                  onClick={() => {
                    console.log('Selected conversation:', conversation.id)
                    setSelectedConversationId(conversation.id)
                    setIsViewerOpen(true)
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      {/* 상단: 메시지 수와 시간 */}
                      <div className="flex items-center gap-1 mb-1 overflow-hidden">
                        <MessageSquare className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        <span className="text-xs text-muted-foreground truncate">
                          {conversation.message_count}개
                        </span>
                        <span className="text-xs text-muted-foreground flex-shrink-0">
                          • {formatConversationTime(conversation.updated_at)}
                        </span>
                      </div>
                      
                      {/* 중단: 제목 */}
                      <h3 className="font-medium text-sm truncate mb-1">
                        {formatConversationTitle(conversation)}
                      </h3>
                      
                      {/* 하단: 질문 미리보기 */}
                      <div className="text-xs text-muted-foreground overflow-hidden">
                        {conversation.isPreviewLoading ? (
                          <span className="animate-pulse">로딩...</span>
                        ) : conversation.firstQuestion ? (
                          <span className="italic line-clamp-2 break-words">"{conversation.firstQuestion}"</span>
                        ) : (
                          <span className="opacity-50">미리보기 없음</span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                      onClick={(e) => {
                        e.stopPropagation()
                        console.log('Delete conversation:', conversation.id)
                        // TODO: Implement conversation deletion
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </Card>
              ))}
            </>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm font-medium mb-1">대화 목록 불러오는 중...</p>
              <p className="text-xs">잠시만 기다려주세요</p>
            </div>
          )}
        </div>
        </ScrollArea>
      )}

      {/* Pagination and Info - 접혔을 때는 숨김 */}
      {!isCollapsed && (
      <div className="border-t max-w-full overflow-hidden">
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-3 border-b max-w-full overflow-hidden">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
              className="justify-center max-w-full overflow-hidden"
            />
          </div>
        )}
        
        {/* Info */}
        <div className="p-3 max-w-full overflow-hidden">
          <PaginationInfo
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalItems}
            itemsPerPage={itemsPerPage}
            className="text-center max-w-full overflow-hidden"
          />
        </div>
      </div>
      )}

      {/* Conversation Viewer Modal */}
      <ConversationViewer
        conversationId={selectedConversationId}
        isOpen={isViewerOpen}
        onOpenChange={setIsViewerOpen}
        userId={userId}
      />
    </div>
  )
}