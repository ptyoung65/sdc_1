'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { TestHistoryStorage } from '../lib/testHistoryStorage'
import { TestResult, TestHistoryFilters } from '../types/TestHistory'

interface TestHistoryProps {
  onTestSelect?: (test: TestResult) => void
}

const TestHistory: React.FC<TestHistoryProps> = ({ onTestSelect }) => {
  const [history, setHistory] = useState<TestResult[]>([])
  const [filteredHistory, setFilteredHistory] = useState<TestResult[]>([])
  const [filters, setFilters] = useState<TestHistoryFilters>({
    status: 'all'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [selectedTest, setSelectedTest] = useState<TestResult | null>(null)

  // Load test history on component mount
  useEffect(() => {
    loadTestHistory()
    
    // Set up periodic refresh to catch new tests
    const interval = setInterval(loadTestHistory, 5000)
    return () => clearInterval(interval)
  }, [])

  // Apply filters when history or filters change
  useEffect(() => {
    applyFilters()
  }, [history, filters])

  const loadTestHistory = () => {
    try {
      const allTests = TestHistoryStorage.getTestHistory()
      setHistory(allTests)
    } catch (error) {
      console.error('Failed to load test history:', error)
    }
  }

  const applyFilters = () => {
    try {
      const filtered = TestHistoryStorage.getTestHistory(filters)
      setFilteredHistory(filtered)
    } catch (error) {
      console.error('Failed to apply filters:', error)
      setFilteredHistory(history)
    }
  }

  const handleFilterChange = (key: keyof TestHistoryFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }))
  }

  const handleTestClick = (test: TestResult) => {
    setSelectedTest(test)
    onTestSelect?.(test)
  }

  const clearHistory = () => {
    if (confirm('모든 테스트 히스토리를 삭제하시겠습니까?')) {
      TestHistoryStorage.clearHistory()
      loadTestHistory()
    }
  }

  const getStatistics = () => {
    return TestHistoryStorage.getStatistics()
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const stats = getStatistics()

  return (
    <div className="space-y-6">
      {/* Statistics Card */}
      <Card>
        <CardHeader>
          <CardTitle>테스트 히스토리 통계</CardTitle>
          <CardDescription>
            챗봇 테스트 실행 기록 및 성과 분석
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-sm text-gray-600">총 테스트</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.successful}</div>
              <div className="text-sm text-gray-600">성공</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
              <div className="text-sm text-gray-600">실패</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.successRate.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">성공률</div>
            </div>
          </div>
          <div className="mt-4 text-center">
            <div className="text-lg font-semibold">평균 처리 시간: {(stats.avgProcessingTime * 1000).toFixed(0)}ms</div>
          </div>
        </CardContent>
      </Card>

      {/* Filters Card */}
      <Card>
        <CardHeader>
          <CardTitle>필터</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">검색어</label>
              <Input
                placeholder="쿼리 검색..."
                value={filters.query || ''}
                onChange={(e) => handleFilterChange('query', e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">상태</label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={filters.status || 'all'}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <option value="all">전체</option>
                <option value="success">성공</option>
                <option value="error">오류</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">시작 날짜</label>
              <Input
                type="date"
                value={filters.dateFrom || ''}
                onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">종료 날짜</label>
              <Input
                type="date"
                value={filters.dateTo || ''}
                onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" onClick={loadTestHistory}>
              새로고침
            </Button>
            <Button variant="destructive" onClick={clearHistory}>
              히스토리 삭제
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Test History List */}
      <Card>
        <CardHeader>
          <CardTitle>테스트 히스토리 ({filteredHistory.length}개)</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredHistory.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              테스트 히스토리가 없습니다.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {filteredHistory.map((test) => (
                <div
                  key={test.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleTestClick(test)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant={test.status === 'success' ? 'default' : 'destructive'}>
                        {test.status === 'success' ? '성공' : '오류'}
                      </Badge>
                      <Badge variant="outline">
                        {test.sources.length}개 청크
                      </Badge>
                      <Badge variant="secondary">
                        {(test.processing_time * 1000).toFixed(0)}ms
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(test.timestamp)}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm font-medium text-gray-700">쿼리: </span>
                      <span className="text-sm">{test.query}</span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">응답: </span>
                      <span className="text-sm text-gray-600 line-clamp-2">
                        {test.response.substring(0, 150)}...
                      </span>
                    </div>
                    {test.korean_analysis.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {test.korean_analysis.keywords.slice(0, 5).map((keyword, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {keyword}
                          </Badge>
                        ))}
                        {test.korean_analysis.keywords.length > 5 && (
                          <Badge variant="outline" className="text-xs">
                            +{test.korean_analysis.keywords.length - 5}
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Selected Test Details Modal */}
      {selectedTest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto m-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">테스트 상세 정보</h2>
              <Button variant="outline" size="sm" onClick={() => setSelectedTest(null)}>
                닫기
              </Button>
            </div>
            
            <Tabs defaultValue="overview">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="overview">개요</TabsTrigger>
                <TabsTrigger value="sources">사용된 청크 ({selectedTest.sources.length})</TabsTrigger>
                <TabsTrigger value="analysis">분석 정보</TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold mb-2">테스트 ID</h3>
                    <p className="text-sm font-mono bg-gray-100 p-2 rounded">{selectedTest.id}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">실행 시간</h3>
                    <p className="text-sm">{formatDate(selectedTest.timestamp)}</p>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-2">쿼리</h3>
                  <p className="text-sm bg-gray-100 p-3 rounded">{selectedTest.query}</p>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-2">응답</h3>
                  <p className="text-sm bg-blue-50 p-3 rounded whitespace-pre-wrap">
                    {selectedTest.response}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <h3 className="font-semibold mb-2">처리 시간</h3>
                    <Badge variant="secondary">
                      {(selectedTest.processing_time * 1000).toFixed(0)}ms
                    </Badge>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">상태</h3>
                    <Badge variant={selectedTest.status === 'success' ? 'default' : 'destructive'}>
                      {selectedTest.status === 'success' ? '성공' : '오류'}
                    </Badge>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">최대 청크 수</h3>
                    <Badge variant="outline">{selectedTest.max_chunks}</Badge>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">유사도 임계값</h3>
                    <Badge variant="outline">{selectedTest.similarity_threshold}</Badge>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="sources" className="space-y-4 mt-4">
                {selectedTest.sources.length > 0 ? (
                  <div className="space-y-3">
                    {selectedTest.sources.map((source, index) => (
                      <div key={source.chunk_id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">청크 #{index + 1}</Badge>
                            <Badge variant="secondary">
                              {(source.similarity * 100).toFixed(1)}% 유사도
                            </Badge>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          📄 {source.metadata.filename || 'Unknown'}
                        </p>
                        <p className="text-sm bg-gray-50 p-3 rounded">
                          {source.content}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">
                    사용된 청크가 없습니다.
                  </p>
                )}
              </TabsContent>

              <TabsContent value="analysis" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold mb-2">원본 쿼리</h3>
                    <p className="text-sm bg-gray-100 p-3 rounded">
                      {selectedTest.korean_analysis.original_query}
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">전처리된 쿼리</h3>
                    <p className="text-sm bg-gray-100 p-3 rounded">
                      {selectedTest.korean_analysis.processed_query}
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold mb-2">토큰화 결과</h3>
                    <div className="flex flex-wrap gap-1">
                      {selectedTest.korean_analysis.tokenized.map((token, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {token}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">키워드 추출</h3>
                    <div className="flex flex-wrap gap-1">
                      {selectedTest.korean_analysis.keywords.map((keyword, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      )}
    </div>
  )
}

export default TestHistory