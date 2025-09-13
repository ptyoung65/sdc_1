'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { TestHistoryStorage } from '../lib/testHistoryStorage'
import { ChunkDetail } from '../types/TestHistory'

interface ChatSource {
  chunk_id: string
  content: string
  similarity: number
  metadata: {
    user_id: string
    filename: string
    chunk_index: number
    total_chunks: number
    processed_at: string
    korean_features: any
    doc_type: string
  }
}

interface ChatTestResult {
  query: string
  response: string
  sources: ChatSource[]
  korean_analysis: {
    original_query: string
    processed_query: string
    tokenized: string[]
    keywords: string[]
  }
  processing_time: number
}

interface ChunkDetailsModalProps {
  source: ChatSource | null
  onClose: () => void
}

const ChunkDetailsModal: React.FC<ChunkDetailsModalProps> = ({ source, onClose }) => {
  if (!source) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto m-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">청크 상세 정보</h2>
          <Button variant="outline" size="sm" onClick={onClose}>
            닫기
          </Button>
        </div>
        
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-sm text-gray-600">청크 ID</h3>
              <p className="text-sm font-mono bg-gray-100 p-2 rounded">{source.chunk_id}</p>
            </div>
            <div>
              <h3 className="font-semibold text-sm text-gray-600">유사도 점수</h3>
              <Badge variant="secondary" className="text-sm">
                {(source.similarity * 100).toFixed(1)}%
              </Badge>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h3 className="font-semibold text-sm text-gray-600">파일명</h3>
              <p className="text-sm">{source.metadata.filename}</p>
            </div>
            <div>
              <h3 className="font-semibold text-sm text-gray-600">청크 위치</h3>
              <p className="text-sm">{source.metadata.chunk_index + 1} / {source.metadata.total_chunks}</p>
            </div>
            <div>
              <h3 className="font-semibold text-sm text-gray-600">처리 시간</h3>
              <p className="text-sm">{new Date(source.metadata.processed_at).toLocaleString('ko-KR')}</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-sm text-gray-600 mb-2">청크 내용</h3>
            <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
              <p className="text-sm whitespace-pre-wrap">{source.content}</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-sm text-gray-600 mb-2">메타데이터</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="text-xs overflow-x-auto">
                {JSON.stringify(source.metadata, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const ChatbotTester: React.FC = () => {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [testResult, setTestResult] = useState<ChatTestResult | null>(null)
  const [selectedChunk, setSelectedChunk] = useState<ChatSource | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [maxChunks, setMaxChunks] = useState(5)
  const [similarityThreshold, setSimilarityThreshold] = useState(0.1)

  const handleTest = async () => {
    if (!query.trim()) return

    setIsLoading(true)
    setError(null)
    const startTime = performance.now()
    
    try {
      const response = await fetch('http://localhost:8008/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          user_id: 'admin_test',
          max_chunks: maxChunks,
          similarity_threshold: similarityThreshold
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      const endTime = performance.now()
      const processingTime = (endTime - startTime) / 1000 // Convert to seconds
      
      // Map ChatSource to ChunkDetail format for history storage
      const historyChunks: ChunkDetail[] = data.sources.map((source: ChatSource) => ({
        chunk_id: source.chunk_id,
        content: source.content,
        similarity: source.similarity,
        metadata: source.metadata,
        korean_features: source.metadata.korean_features || {}
      }))

      // Save to test history
      try {
        const savedResult = TestHistoryStorage.saveTestResult({
          query: data.query,
          response: data.response,
          sources: historyChunks,
          korean_analysis: data.korean_analysis,
          processing_time: data.processing_time || processingTime,
          similarity_threshold: similarityThreshold,
          max_chunks: maxChunks,
          status: 'success'
        })
        console.log('Test result saved to history:', savedResult.id)
      } catch (historyError) {
        console.error('Failed to save test result to history:', historyError)
      }

      setTestResult(data)
    } catch (err) {
      const endTime = performance.now()
      const processingTime = (endTime - startTime) / 1000
      
      // Save error to test history
      try {
        TestHistoryStorage.saveTestResult({
          query: query,
          response: `오류 발생: ${err instanceof Error ? err.message : '알 수 없는 오류'}`,
          sources: [],
          korean_analysis: {
            original_query: query,
            processed_query: query,
            tokenized: [],
            keywords: []
          },
          processing_time: processingTime,
          similarity_threshold: similarityThreshold,
          max_chunks: maxChunks,
          status: 'error'
        })
      } catch (historyError) {
        console.error('Failed to save error to history:', historyError)
      }

      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleChunkClick = (source: ChatSource) => {
    setSelectedChunk(source)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>챗봇 테스트</CardTitle>
          <CardDescription>
            Korean RAG 시스템을 테스트하고 사용된 청크 정보를 확인할 수 있습니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="text-sm font-medium mb-2 block">테스트 쿼리</label>
              <Textarea
                placeholder="예: 한국어 문서 처리에 대해 알려주세요"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={3}
              />
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">최대 청크 수</label>
                <Input
                  type="number"
                  min="1"
                  max="10"
                  value={maxChunks}
                  onChange={(e) => setMaxChunks(parseInt(e.target.value) || 5)}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">유사도 임계값</label>
                <Input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={similarityThreshold}
                  onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value) || 0.1)}
                />
              </div>
            </div>
          </div>
          
          <Button 
            onClick={handleTest} 
            disabled={isLoading || !query.trim()}
            className="w-full md:w-auto"
          >
            {isLoading ? '테스트 중...' : '테스트 실행'}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-600 text-sm">❌ 오류: {error}</p>
          </CardContent>
        </Card>
      )}

      {testResult && (
        <Card>
          <CardHeader>
            <CardTitle>테스트 결과</CardTitle>
            <CardDescription>
              처리 시간: {(testResult.processing_time * 1000).toFixed(0)}ms
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="response">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="response">응답</TabsTrigger>
                <TabsTrigger value="sources">
                  사용된 청크 ({testResult.sources.length})
                </TabsTrigger>
                <TabsTrigger value="analysis">분석 정보</TabsTrigger>
              </TabsList>
              
              <TabsContent value="response" className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">쿼리</h3>
                  <p className="text-sm bg-gray-100 p-3 rounded">{testResult.query}</p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">응답</h3>
                  <p className="text-sm bg-blue-50 p-3 rounded whitespace-pre-wrap">
                    {testResult.response}
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="sources" className="space-y-4">
                {testResult.sources.length > 0 ? (
                  <div className="space-y-3">
                    {testResult.sources.map((source, index) => (
                      <div 
                        key={source.chunk_id}
                        className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => handleChunkClick(source)}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">청크 #{index + 1}</Badge>
                            <Badge variant="secondary">
                              {(source.similarity * 100).toFixed(1)}% 유사도
                            </Badge>
                          </div>
                          <Button variant="outline" size="sm">
                            상세보기
                          </Button>
                        </div>
                        <p className="text-sm text-gray-600 mb-1">
                          📄 {source.metadata.filename} ({source.metadata.chunk_index + 1}/{source.metadata.total_chunks})
                        </p>
                        <p className="text-sm line-clamp-3">
                          {source.content.substring(0, 200)}...
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">
                    검색된 청크가 없습니다.
                  </p>
                )}
              </TabsContent>

              <TabsContent value="analysis" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold mb-2">원본 쿼리</h3>
                    <p className="text-sm bg-gray-100 p-3 rounded">
                      {testResult.korean_analysis.original_query}
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">전처리된 쿼리</h3>
                    <p className="text-sm bg-gray-100 p-3 rounded">
                      {testResult.korean_analysis.processed_query}
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold mb-2">토큰화 결과</h3>
                    <div className="flex flex-wrap gap-1">
                      {testResult.korean_analysis.tokenized.map((token, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {token}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">키워드 추출</h3>
                    <div className="flex flex-wrap gap-1">
                      {testResult.korean_analysis.keywords.map((keyword, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      <ChunkDetailsModal 
        source={selectedChunk} 
        onClose={() => setSelectedChunk(null)} 
      />
    </div>
  )
}

export default ChatbotTester