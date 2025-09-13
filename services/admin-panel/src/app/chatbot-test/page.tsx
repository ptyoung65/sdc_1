'use client'

import React from 'react'
import ChatbotTester from '../../components/ChatbotTester'

export default function ChatbotTestPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            챗봇 테스트
          </h1>
          <p className="text-gray-600">
            Korean RAG 시스템의 챗봇 기능을 테스트하고 사용된 문서 청크를 확인할 수 있습니다.
          </p>
        </div>
        
        <ChatbotTester />
      </div>
    </div>
  )
}