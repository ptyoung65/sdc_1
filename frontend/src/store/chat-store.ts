import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { Message, Conversation, MessageRole, ChatState } from '@/types'
import { generateId } from '@/lib/utils'

interface ChatStore extends ChatState {
  // Actions
  createConversation: () => void
  selectConversation: (id: string) => void
  sendMessage: (content: string, files?: File[]) => Promise<void>
  deleteConversation: (id: string) => void
  updateConversation: (id: string, updates: Partial<Conversation>) => void
  archiveConversation: (id: string) => void
  clearCurrentConversation: () => void
  addMessage: (conversationId: string, message: Message) => void
  updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => void
  deleteMessage: (conversationId: string, messageId: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | undefined) => void
  clearError: () => void
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // Initial state
      conversations: [],
      currentConversation: null,
      isLoading: false,

      // Actions
      createConversation: () => {
        const newConversation: Conversation = {
          id: generateId(),
          title: '새로운 대화',
          userId: 'current-user', // TODO: Get from auth store
          messages: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          tags: [],
        }

        set((state) => ({
          conversations: [newConversation, ...state.conversations],
          currentConversation: newConversation,
        }))
      },

      selectConversation: (id: string) => {
        const conversation = get().conversations.find(c => c.id === id)
        if (conversation) {
          set({ currentConversation: conversation })
        }
      },

      sendMessage: async (content: string, files?: File[]) => {
        try {
          const { currentConversation, conversations } = get()
          let conversation = currentConversation

          // Create new conversation if none exists
          if (!conversation) {
            get().createConversation()
            conversation = get().currentConversation!
          }

          // Create user message
          const userMessage: Message = {
            id: generateId(),
            content,
            role: MessageRole.USER,
            timestamp: new Date().toISOString(),
            conversationId: conversation.id,
            ...(files && files.length > 0 && {
              metadata: {
                attachments: files.map(file => ({
                  name: file.name,
                  size: file.size,
                  type: file.type,
                }))
              }
            })
          }

          // Add user message
          get().addMessage(conversation.id, userMessage)
          set({ isLoading: true })

          // Generate conversation title if it's the first message
          if (conversation.messages.length === 0) {
            const title = content.length > 50 
              ? content.substring(0, 47) + '...' 
              : content
            
            get().updateConversation(conversation.id, { 
              title,
              updatedAt: new Date().toISOString()
            })
          }

          // TODO: Replace with actual API call to backend
          // const response = await chatApi.sendMessage({
          //   conversationId: conversation.id,
          //   message: content,
          //   files: files
          // })

          // Mock API response
          await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))

          // Generate mock AI response
          const aiResponse = generateMockAIResponse(content)
          
          const assistantMessage: Message = {
            id: generateId(),
            content: aiResponse.content,
            role: MessageRole.ASSISTANT,
            timestamp: new Date().toISOString(),
            conversationId: conversation.id,
            metadata: {
              model: 'sdc-demo-v1',
              processingTime: aiResponse.processingTime,
              confidence: aiResponse.confidence,
              tokens: aiResponse.tokens,
            },
            sources: aiResponse.sources,
          }

          // Add AI response
          get().addMessage(conversation.id, assistantMessage)
          set({ isLoading: false })

        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : '메시지 전송 중 오류가 발생했습니다.'
          })
          throw error
        }
      },

      deleteConversation: (id: string) => {
        set((state) => ({
          conversations: state.conversations.filter(c => c.id !== id),
          currentConversation: state.currentConversation?.id === id ? null : state.currentConversation,
        }))
      },

      updateConversation: (id: string, updates: Partial<Conversation>) => {
        set((state) => {
          const updatedConversations = state.conversations.map(c =>
            c.id === id ? { ...c, ...updates } : c
          )
          
          const updatedCurrentConversation = state.currentConversation?.id === id
            ? { ...state.currentConversation, ...updates }
            : state.currentConversation

          return {
            conversations: updatedConversations,
            currentConversation: updatedCurrentConversation,
          }
        })
      },

      archiveConversation: (id: string) => {
        get().updateConversation(id, { 
          isArchived: true,
          updatedAt: new Date().toISOString()
        })
      },

      clearCurrentConversation: () => {
        set({ currentConversation: null })
      },

      addMessage: (conversationId: string, message: Message) => {
        set((state) => {
          const updatedConversations = state.conversations.map(c =>
            c.id === conversationId
              ? { 
                  ...c, 
                  messages: [...c.messages, message],
                  updatedAt: new Date().toISOString()
                }
              : c
          )

          const updatedCurrentConversation = state.currentConversation?.id === conversationId
            ? {
                ...state.currentConversation,
                messages: [...state.currentConversation.messages, message],
                updatedAt: new Date().toISOString()
              }
            : state.currentConversation

          return {
            conversations: updatedConversations,
            currentConversation: updatedCurrentConversation,
          }
        })
      },

      updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => {
        set((state) => {
          const updatedConversations = state.conversations.map(c =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.map(m =>
                    m.id === messageId ? { ...m, ...updates } : m
                  )
                }
              : c
          )

          const updatedCurrentConversation = state.currentConversation?.id === conversationId
            ? {
                ...state.currentConversation,
                messages: state.currentConversation.messages.map(m =>
                  m.id === messageId ? { ...m, ...updates } : m
                )
              }
            : state.currentConversation

          return {
            conversations: updatedConversations,
            currentConversation: updatedCurrentConversation,
          }
        })
      },

      deleteMessage: (conversationId: string, messageId: string) => {
        set((state) => {
          const updatedConversations = state.conversations.map(c =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.filter(m => m.id !== messageId)
                }
              : c
          )

          const updatedCurrentConversation = state.currentConversation?.id === conversationId
            ? {
                ...state.currentConversation,
                messages: state.currentConversation.messages.filter(m => m.id !== messageId)
              }
            : state.currentConversation

          return {
            conversations: updatedConversations,
            currentConversation: updatedCurrentConversation,
          }
        })
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },

      setError: (error: string | undefined) => {
        if (error !== undefined) {
          set({ error } as Partial<ChatStore>)
        } else {
          const state = get()
          delete (state as any).error
          set(state)
        }
      },

      clearError: () => {
        const state = get()
        delete (state as any).error
        set(state)
      },
    }),
    {
      name: 'sdc-chat-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        conversations: state.conversations,
      }),
    }
  )
)

// Mock AI response generator
function generateMockAIResponse(userMessage: string) {
  const responses = [
    {
      trigger: ['안녕', 'hello', '안녕하세요'],
      content: `안녕하세요! SDC(Smart Document Chat)에 오신 것을 환영합니다.

저는 멀티 LLM 기반의 AI 어시스턴트로, 다음과 같은 기능을 제공합니다:

## 🚀 주요 기능
- **문서 분석**: PDF, DOCX 등 다양한 문서 분석
- **실시간 검색**: 최신 웹 정보 검색 및 제공
- **한국어 특화**: KURE-v1 모델로 정확한 한국어 처리
- **RAG 검색**: 신뢰할 수 있는 문서 기반 답변

무엇을 도와드릴까요?`,
      sources: [
        {
          id: 'welcome-guide',
          title: 'SDC 서비스 가이드',
          type: 'md' as any,
          relevance: 0.95,
          snippet: 'SDC는 멀티 LLM 기반 대화형 AI 서비스입니다...'
        }
      ]
    },
    {
      trigger: ['sdc', 'SDC', '프로젝트'],
      content: `SDC(Smart Document Chat)는 고급 RAG(Retrieval-Augmented Generation) 시스템을 기반으로 한 차세대 대화형 AI 서비스입니다.

## 🏗️ 시스템 아키텍처

### Layer 1: Frontend (Next.js)
- React 18 + TypeScript
- Tailwind CSS + Shadcn UI
- 반응형 디자인 및 다크 모드

### Layer 2: AI Core (LangGraph)
- 멀티 에이전트 RAG 파이프라인
- 환각 방지 검증 시스템
- KURE-v1 한국어 임베딩

### Layer 3: Database (Hybrid)
- PostgreSQL: 메타데이터 관리
- Milvus: 벡터 검색
- Elasticsearch: 키워드 검색

### Layer 4: Security & Monitoring
- Arther AI Guardrail
- ELK Stack + Grafana
- 다층적 보안 체계

### Layer 5: Infrastructure (Podman → K8s)
- 컨테이너화된 마이크로서비스
- CI/CD 파이프라인
- 확장 가능한 배포 전략

더 자세한 내용이 궁금하시면 언제든 질문해주세요!`,
      sources: [
        {
          id: 'architecture-doc',
          title: '시스템 아키텍처 문서',
          type: 'pdf' as any,
          relevance: 0.92,
          snippet: '5계층 아키텍처로 설계된 확장 가능한 AI 서비스...'
        },
        {
          id: 'tech-stack',
          title: '기술 스택 가이드',
          type: 'md' as any,
          relevance: 0.88,
          snippet: 'Next.js, LangGraph, PostgreSQL, Milvus를 활용한 현대적 기술 스택...'
        }
      ]
    },
    {
      trigger: ['도움말', '도움', 'help', '기능'],
      content: `SDC에서 사용할 수 있는 다양한 기능들을 안내해드리겠습니다.

## 💬 채팅 기능
- **텍스트 대화**: 자연어로 질문하고 답변받기
- **파일 업로드**: PDF, DOCX, TXT 파일 분석
- **실시간 검색**: 최신 웹 정보 검색
- **마크다운 지원**: 코드, 표, 링크 등 서식 지원

## 📁 문서 관리
- **다양한 형식 지원**: PDF, DOCX, TXT, MD
- **자동 청킹**: 문서를 적절한 크기로 분할
- **임베딩 생성**: 의미 기반 검색 최적화
- **메타데이터 추출**: 제목, 저자, 생성일 등

## 🔍 고급 검색
- **하이브리드 검색**: 키워드 + 벡터 검색
- **필터링**: 날짜, 태그, 파일 형식별 검색
- **인용 표시**: 답변 출처 명확히 표시

## 🎨 사용자 경험
- **다크/라이트 모드**: 취향에 맞는 테마 선택
- **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- **실시간 알림**: 처리 상태 및 결과 알림

궁금한 기능이 있으시면 구체적으로 질문해주세요!`,
      sources: []
    }
  ]

  // Find matching response
  const matchedResponse = responses.find(response =>
    response.trigger.some(trigger =>
      userMessage.toLowerCase().includes(trigger.toLowerCase())
    )
  )

  const selectedResponse = matchedResponse || {
    content: `"${userMessage}"에 대한 답변입니다.

현재 SDC는 개발 중인 데모 버전으로 실행되고 있습니다. 실제 AI 서비스가 연결되면 더욱 정확하고 유용한 답변을 제공할 것입니다.

## 현재 지원 중인 기능
- ✅ 실시간 채팅 인터페이스
- ✅ 다크/라이트 모드
- ✅ 파일 업로드 (개발 중)
- ✅ 마크다운 렌더링
- 🔄 RAG 기반 문서 검색 (개발 중)
- 🔄 실시간 웹 검색 (개발 중)

더 구체적인 질문을 해주시면 관련 정보를 찾아서 답변해드리겠습니다!`,
    sources: [
      {
        id: 'demo-info',
        title: 'SDC 데모 정보',
        type: 'txt' as any,
        relevance: 0.85,
        snippet: 'SDC 데모 버전의 현재 구현 상태와 계획된 기능들...'
      }
    ]
  }

  return {
    content: selectedResponse.content,
    processingTime: 0.8 + Math.random() * 2,
    confidence: 0.85 + Math.random() * 0.1,
    tokens: {
      prompt: Math.floor(userMessage.length / 4),
      completion: Math.floor(selectedResponse.content.length / 4),
      total: Math.floor((userMessage.length + selectedResponse.content.length) / 4),
    },
    sources: selectedResponse.sources,
  }
}