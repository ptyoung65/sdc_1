"use client"

import * as React from "react"
import { ChatInterface } from '@/components/chat/chat-interface'
import { SimpleConversationSidebar } from '@/components/chat/simple-conversation-sidebar'
import { Header } from '@/components/layout/header'
import { apiService } from '@/services/api'
import { Message, MessageRole } from '@/types'

// Convert API message format to frontend message format
const convertApiMessageToFrontend = (apiMessage: any): Message => {
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

export function HomePage() {
  const [currentConversationId, setCurrentConversationId] = React.useState<string | null>(null)
  const [conversationMessages, setConversationMessages] = React.useState<Message[]>([])
  const [isLoadingMessages, setIsLoadingMessages] = React.useState(false)
  const userId = "default_user"

  // Load messages for selected conversation
  const loadConversationMessages = React.useCallback(async (conversationId: string) => {
    setIsLoadingMessages(true)
    try {
      const apiMessages = await apiService.getConversationMessages(conversationId)
      const frontendMessages = apiMessages.map(msg => ({
        ...convertApiMessageToFrontend(msg),
        conversationId: conversationId
      }))
      setConversationMessages(frontendMessages)
      setCurrentConversationId(conversationId)
    } catch (error) {
      console.error('Failed to load conversation messages:', error)
      setConversationMessages([])
    } finally {
      setIsLoadingMessages(false)
    }
  }, [])

  const handleSelectConversation = React.useCallback((conversationId: string) => {
    if (conversationId !== currentConversationId) {
      loadConversationMessages(conversationId)
    }
  }, [currentConversationId, loadConversationMessages])

  const handleNewConversation = React.useCallback(() => {
    setCurrentConversationId(null)
    setConversationMessages([])
  }, [])

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar - Conversations Only */}
      <div className="flex-shrink-0 w-80 border-r border-border bg-background/95 backdrop-blur-sm flex flex-col">
        {/* Conversations Section */}
        <div className="flex-1 min-h-0">
          <SimpleConversationSidebar userId={userId} />
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <div className="flex-shrink-0">
          <Header />
        </div>
        
        {/* Chat Interface */}
        <main className="flex-1 overflow-hidden">
          <ChatInterface
            conversation={currentConversationId ? {
              id: currentConversationId,
              title: `대화 ${currentConversationId.slice(0, 8)}`,
              userId: userId,
              messages: conversationMessages,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString()
            } : null}
          />
        </main>
      </div>
    </div>
  )
}