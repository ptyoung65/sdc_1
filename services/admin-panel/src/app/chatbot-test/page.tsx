'use client'

import React, { useState } from 'react'
import ChatbotTester from '../../components/ChatbotTester'
import TestHistory from '../../components/TestHistory'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'

export default function ChatbotTestPage() {
  const [activeTab, setActiveTab] = useState('test')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            챗봇 테스트 & 히스토리
          </h1>
          <p className="text-gray-600">
            Korean RAG 시스템의 챗봇 기능을 테스트하고 사용된 문서 청크를 확인하며, 테스트 히스토리를 관리할 수 있습니다.
          </p>
        </div>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="test">챗봇 테스트</TabsTrigger>
            <TabsTrigger value="history">테스트 히스토리</TabsTrigger>
          </TabsList>
          
          <TabsContent value="test">
            <ChatbotTester />
          </TabsContent>
          
          <TabsContent value="history">
            <TestHistory />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}