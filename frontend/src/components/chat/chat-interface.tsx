"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Bot } from "lucide-react"

import { Message, MessageRole, Conversation, DocumentType } from "@/types"
import { generateId } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageBubble } from "./message-bubble"
import { MessageInput } from "./message-input"
import { TypingIndicator } from "./typing-indicator"
import { WelcomeScreen } from "./welcome-screen"
import { MultiRAGResponse } from "./multi-rag-response"
import { apiService, LLMProvider, SearchEngine, type ChatResponse, type RAGResult } from "@/services/api"

interface ChatInterfaceProps {
  conversation?: Conversation | null
  className?: string
}

export function ChatInterface({ conversation, className }: ChatInterfaceProps) {
  const [messages, setMessages] = React.useState<Message[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [inputValue, setInputValue] = React.useState("")
  const [providers, setProviders] = React.useState<LLMProvider[]>([])
  const [selectedProvider, setSelectedProvider] = React.useState<string>('gemini')
  const [searchMode, setSearchMode] = React.useState<'documents' | 'web' | 'combined'>('documents')
  const [searchEngines, setSearchEngines] = React.useState<SearchEngine[]>([])
  const [selectedEngines, setSelectedEngines] = React.useState<string[]>(['google'])
  const [useAgenticRag, setUseAgenticRag] = React.useState(false)
  const [agenticComplexityThreshold, setAgenticComplexityThreshold] = React.useState(5)
  
  // Multi-RAG selection states
  const [enabledRAGTypes, setEnabledRAGTypes] = React.useState({
    vector: true,      // Korean Vector RAG (기본 활성)
    graph: true,       // Graph RAG (기본 활성)
    keyword: true,     // Keyword RAG (기본 활성)  
    database: true     // Text-to-SQL RAG (기본 활성)
  })
  const [currentUserId] = React.useState("default_user") // TODO: 실제 사용자 인증 구현
  const [currentConversationId, setCurrentConversationId] = React.useState<string | null>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = React.useState(true)
  const scrollAreaRef = React.useRef<HTMLDivElement>(null)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  // Load conversation messages
  React.useEffect(() => {
    if (conversation) {
      setMessages(conversation.messages)
    } else {
      setMessages([])
    }
  }, [conversation])

  // Load LLM providers
  React.useEffect(() => {
    const fetchProviders = async () => {
      try {
        const providerData = await apiService.getProviders()
        setProviders(providerData)
      } catch (error) {
        console.error('Failed to load providers:', error)
        setProviders([])
      }
    }
    fetchProviders()
  }, [])

  // Load search engines
  React.useEffect(() => {
    const fetchSearchEngines = async () => {
      try {
        const engineData = await apiService.getSearchEngines()
        setSearchEngines(engineData)
      } catch (error) {
        console.error('Failed to load search engines:', error)
        setSearchEngines([])
      }
    }
    fetchSearchEngines()
  }, [])

  // Auto scroll to bottom - only when shouldAutoScroll is true
  React.useEffect(() => {
    if (shouldAutoScroll) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
      }, 100)
    }
  }, [messages, isLoading, shouldAutoScroll])

  // Handle manual scrolling to disable auto-scroll
  React.useEffect(() => {
    const scrollArea = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]')
    if (!scrollArea) return

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollArea
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 50
      
      // If user scrolls away from bottom, disable auto-scroll
      if (!isAtBottom) {
        setShouldAutoScroll(false)
      }
    }

    scrollArea.addEventListener('scroll', handleScroll)
    return () => scrollArea.removeEventListener('scroll', handleScroll)
  }, [])

  const handleSendMessage = async (content: string, files?: File[]) => {
    if (!content.trim() && (!files || files.length === 0)) return

    const userMessage: Message = {
      id: generateId(),
      content,
      role: MessageRole.USER,
      timestamp: new Date().toISOString(),
      conversationId: conversation?.id || generateId(),
      ...(files && files.length > 0 && { 
        metadata: { 
          attachments: files.map(file => ({
            name: file.name,
            size: file.size,
            type: file.type
          }))
        }
      })
    }

    setMessages(prev => [...prev, userMessage])
    setShouldAutoScroll(true) // Enable auto-scroll when sending message
    setIsLoading(true)

    try {
      let useRAG = false
      let uploadedFiles: string[] = []

      // Upload files if provided
      if (files && files.length > 0) {
        for (const file of files) {
          try {
            const formData = new FormData()
            formData.append('file', file)
            
            const uploadResponse = await fetch('http://localhost:8000/api/v1/documents', {
              method: 'POST',
              body: formData
            })
            
            if (uploadResponse.ok) {
              const uploadResult = await uploadResponse.json()
              if (uploadResult.success) {
                uploadedFiles.push(uploadResult.data.filename)
                useRAG = true
              }
            }
          } catch (uploadError) {
            console.error(`Failed to upload file ${file.name}:`, uploadError)
          }
        }
      }

      // Prepare chat message with file context
      let finalContent = content
      if (uploadedFiles.length > 0) {
        finalContent = `[첨부파일: ${uploadedFiles.join(', ')}]\n\n${content}`
      }

      // Call API with selected provider and RAG options
      const response = await apiService.sendMessage({
        message: finalContent,
        provider: selectedProvider,
        use_rag: useRAG || searchMode === 'documents' || searchMode === 'combined',
        use_web_search: searchMode === 'web' || searchMode === 'combined',
        web_search_engines: selectedEngines,
        search_mode: searchMode,
        use_agentic_rag: useAgenticRag,
        agentic_complexity_threshold: agenticComplexityThreshold,
        user_id: currentUserId,
        conversation_id: currentConversationId || '',
        conversation_history: messages.map(m => ({
          role: m.role === MessageRole.USER ? 'user' : 'assistant',
          content: m.content
        })),
        // Multi-RAG configuration
        enabled_rag_types: enabledRAGTypes
      })

      // Check if response was successful
      if (!response.success) {
        throw new Error(response.error || 'Failed to get response from API')
      }

      // Update conversation ID from response if this is a new conversation
      if (response.conversation_id && !currentConversationId) {
        setCurrentConversationId(response.conversation_id)
      }

      const assistantMessage: Message = {
        id: response.message_id || generateId(),
        content: response.response,
        role: MessageRole.ASSISTANT,
        timestamp: new Date().toISOString(),
        conversationId: response.conversation_id || currentConversationId || generateId(),
        metadata: {
          model: response.model || selectedProvider,
          processingTime: 1.2,
          confidence: 0.95,
          ...(response.tokens && {
            tokens: {
              prompt: response.tokens.prompt || 0,
              completion: response.tokens.completion || 0,
              total: response.tokens.total || 0
            }
          }),
          ...(response.has_multi_rag && response.rag_results && {
            ragResults: response.rag_results,
            hasMultiRAG: true
          })
        },
        sources: (response.sources || []).map((source: any) => ({
          id: source.document_id || '',
          title: source.filename || 'Unknown',
          type: 'pdf' as DocumentType,
          relevance: source.score || 0,
          snippet: source.content_preview || ''
        }))
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error("Failed to send message:", error)
      
      const errorMessage: Message = {
        id: generateId(),
        content: "죄송합니다. 메시지를 처리하는 중에 오류가 발생했습니다.",
        role: MessageRole.ASSISTANT,
        timestamp: new Date().toISOString(),
        conversationId: conversation?.id || generateId(),
        error: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleEngineToggle = (engineId: string) => {
    setSelectedEngines(prev => {
      if (prev.includes(engineId)) {
        return prev.filter(id => id !== engineId).length > 0 
          ? prev.filter(id => id !== engineId)
          : [engineId] // 최소 하나는 선택되어야 함
      } else {
        return [...prev, engineId]
      }
    })
  }

  const handleSearchModeChange = (mode: 'documents' | 'web' | 'combined') => {
    setSearchMode(mode)
  }

  const handleRAGToggle = (ragType: keyof typeof enabledRAGTypes) => {
    setEnabledRAGTypes(prev => {
      const newState = { ...prev, [ragType]: !prev[ragType] }
      
      // 최소 하나는 활성화되어야 함
      const hasAnyEnabled = Object.values(newState).some(enabled => enabled)
      if (!hasAnyEnabled) {
        return { ...prev, [ragType]: true }
      }
      
      return newState
    })
  }

  const hasMessages = messages.length > 0

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Messages Area */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea ref={scrollAreaRef} className="h-full">
          <div className="flex flex-col">
            {/* Welcome Screen */}
            {!hasMessages && !isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="flex-1"
              >
                <WelcomeScreen onSendMessage={handleSendMessage} />
              </motion.div>
            )}

            {/* Messages */}
            <AnimatePresence>
              {messages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  showAvatar={true}
                  isLast={index === messages.length - 1}
                  onRate={async (rating: number, feedback?: string) => {
                    try {
                      await apiService.rateMessage({
                        message_id: message.id,
                        user_id: currentUserId,
                        rating,
                        feedback: feedback || ''
                      });
                    } catch (error) {
                      console.error("Failed to rate message:", error);
                    }
                  }}
                  currentUserId={currentUserId}
                />
              ))}
            </AnimatePresence>

            {/* Typing Indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="flex items-start gap-3 px-4 py-3"
              >
                <div className="h-8 w-8 shrink-0 rounded-full bg-primary flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary-foreground" />
                </div>
                <TypingIndicator />
              </motion.div>
            )}

            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* Input Area */}
      <div className="shrink-0 border-t bg-background/80 backdrop-blur-sm p-4">
        {/* Controls Row */}
        <div className="flex flex-col gap-3 mb-3">
          {/* LLM Provider Selector */}
          {providers.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">AI 모델:</span>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="px-3 py-1 text-sm rounded-md border bg-background"
              >
                {providers.filter(p => p.available).map(provider => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name} ({provider.model})
                  </option>
                ))}
              </select>
            </div>
          )}
          
          {/* Search Mode Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">검색 모드:</span>
            <div className="flex rounded-lg border bg-muted p-1">
              <button
                onClick={() => handleSearchModeChange('documents')}
                className={`px-2 py-1 text-xs rounded-md font-medium transition-colors ${
                  searchMode === 'documents'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                문서
              </button>
              <button
                onClick={() => handleSearchModeChange('web')}
                className={`px-2 py-1 text-xs rounded-md font-medium transition-colors ${
                  searchMode === 'web'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                웹
              </button>
              <button
                onClick={() => handleSearchModeChange('combined')}
                className={`px-2 py-1 text-xs rounded-md font-medium transition-colors ${
                  searchMode === 'combined'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                통합
              </button>
            </div>
          </div>

          {/* Multi-RAG Selection Toggles - Hidden for now */}
          {false && (searchMode === 'documents' || searchMode === 'combined') && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">RAG 유형:</span>
              <div className="flex gap-1">
                <button
                  onClick={() => handleRAGToggle('vector')}
                  className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                    enabledRAGTypes.vector
                      ? 'bg-blue-500 text-white'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
                  }`}
                  title="벡터 RAG - 한국어 문서 임베딩 기반 검색"
                >
                  벡터
                </button>
                <button
                  onClick={() => handleRAGToggle('graph')}
                  className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                    enabledRAGTypes.graph
                      ? 'bg-green-500 text-white'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
                  }`}
                  title="그래프 RAG - 관계형 정보 기반 검색"
                >
                  그래프
                </button>
                <button
                  onClick={() => handleRAGToggle('keyword')}
                  className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                    enabledRAGTypes.keyword
                      ? 'bg-orange-500 text-white'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
                  }`}
                  title="키워드 RAG - 전문 검색 엔진 기반 검색"
                >
                  키워드
                </button>
                <button
                  onClick={() => handleRAGToggle('database')}
                  className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                    enabledRAGTypes.database
                      ? 'bg-purple-500 text-white'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
                  }`}
                  title="DB RAG - 자연어를 SQL로 변환하여 데이터베이스 검색"
                >
                  데이터베이스
                </button>
              </div>
            </div>
          )}

          {/* Search Engines Selector - Only show when web or combined search is selected */}
          {(searchMode === 'web' || searchMode === 'combined') && searchEngines.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">검색엔진:</span>
              <div className="flex gap-1">
                {searchEngines.filter(engine => engine.available).map(engine => (
                  <button
                    key={engine.id}
                    onClick={() => handleEngineToggle(engine.id)}
                    className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                      selectedEngines.includes(engine.id)
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
                    }`}
                    title={engine.description}
                  >
                    {engine.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Agentic RAG Toggle - Hidden for now */}
          {false && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">고급 AI:</span>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useAgenticRag}
                  onChange={(e) => setUseAgenticRag(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300"
                />
                <span className="text-xs text-muted-foreground">
                  에이전틱 RAG {useAgenticRag ? '활성' : '비활성'}
                </span>
              </label>
              {useAgenticRag && (
                <div className="flex items-center gap-1 ml-2">
                  <span className="text-xs text-muted-foreground">복잡도:</span>
                  <select
                    value={agenticComplexityThreshold}
                    onChange={(e) => setAgenticComplexityThreshold(Number(e.target.value))}
                    className="px-2 py-1 text-xs rounded border bg-background"
                  >
                    <option value={3}>낮음 (3)</option>
                    <option value={5}>보통 (5)</option>
                    <option value={7}>높음 (7)</option>
                  </select>
                </div>
              )}
            </div>
          )}
        </div>
        <MessageInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSendMessage}
          disabled={isLoading}
          isLoading={isLoading}
          placeholder={
            hasMessages 
              ? `${
                searchMode === 'web' ? '웹에서 검색하여' :
                searchMode === 'combined' ? '문서와 웹에서 검색하여' :
                '문서에서 검색하여'
              } 답변할 질문을 입력하세요...` 
              : `SDC Gen AI에게 무엇이든 물어보세요... (${
                searchMode === 'web' ? '웹 검색' :
                searchMode === 'combined' ? '통합 검색' :
                '문서 검색'
              } 모드)`
          }
          enableFileUpload={searchMode === 'documents' || searchMode === 'combined'}
          enableVoiceInput={false}
        />
      </div>
    </div>
  )
}