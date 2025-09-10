"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, ChevronUp, Database, GitGraph, Search, Zap } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export interface RAGResult {
  type: 'vector' | 'graph' | 'keyword' | 'database'
  success: boolean
  response?: string
  error?: string
  metadata?: {
    sources?: string[]
    confidence?: number
    processingTime?: number
    resultCount?: number
  }
}

interface MultiRAGResponseProps {
  ragResults: RAGResult[]
  finalResponse: string
  className?: string
}

const RAG_CONFIG = {
  vector: {
    label: '벡터 RAG',
    icon: Zap,
    color: 'bg-blue-500',
    description: '한국어 문서 임베딩 기반 검색'
  },
  graph: {
    label: '그래프 RAG', 
    icon: GitGraph,
    color: 'bg-green-500',
    description: '관계형 정보 기반 검색'
  },
  keyword: {
    label: '키워드 RAG',
    icon: Search, 
    color: 'bg-orange-500',
    description: '전문 검색 엔진 기반 검색'
  },
  database: {
    label: '데이터베이스 RAG',
    icon: Database,
    color: 'bg-purple-500', 
    description: '자연어를 SQL로 변환하여 데이터베이스 검색'
  }
}

export function MultiRAGResponse({ ragResults, finalResponse, className }: MultiRAGResponseProps) {
  const [expandedSections, setExpandedSections] = React.useState<Record<string, boolean>>({})

  const toggleSection = (ragType: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [ragType]: !prev[ragType]
    }))
  }

  const successfulResults = ragResults.filter(result => result.success && result.response)
  const failedResults = ragResults.filter(result => !result.success || !result.response)

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Final Combined Response */}
      <Card className="border-primary/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-primary"></div>
            종합 답변
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm leading-relaxed">
            {finalResponse}
          </div>
        </CardContent>
      </Card>

      {/* Individual RAG Results */}
      <div className="space-y-2">
        <div className="text-xs font-medium text-muted-foreground mb-2">
          RAG 시스템별 결과 ({successfulResults.length}/{ragResults.length} 성공)
        </div>
        
        {ragResults.map((result) => {
          const config = RAG_CONFIG[result.type]
          const Icon = config.icon
          const isExpanded = expandedSections[result.type]
          
          return (
            <Card key={result.type} className="border-muted/50">
              <CardHeader className="py-2 px-3">
                <div 
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => toggleSection(result.type)}
                >
                  <div className="flex items-center gap-2">
                    <Icon className="h-3 w-3" />
                    <span className="text-sm font-medium">{config.label}</span>
                    <Badge 
                      variant={result.success && result.response ? "default" : "destructive"}
                      className="text-xs px-1.5 py-0"
                    >
                      {result.success && result.response ? "성공" : "답변 없음"}
                    </Badge>
                    {result.metadata?.resultCount && (
                      <Badge variant="outline" className="text-xs px-1.5 py-0">
                        {result.metadata.resultCount}건
                      </Badge>
                    )}
                  </div>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    {isExpanded ? (
                      <ChevronUp className="h-3 w-3" />
                    ) : (
                      <ChevronDown className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <CardContent className="pt-0 px-3 pb-3">
                      {result.success && result.response ? (
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            {config.description}
                          </div>
                          <div className="text-sm leading-relaxed bg-muted/30 p-2 rounded">
                            {result.response}
                          </div>
                          {result.metadata && (
                            <div className="flex gap-2 text-xs text-muted-foreground">
                              {result.metadata.confidence && (
                                <span>신뢰도: {Math.round(result.metadata.confidence * 100)}%</span>
                              )}
                              {result.metadata.processingTime && (
                                <span>처리시간: {result.metadata.processingTime.toFixed(2)}초</span>
                              )}
                              {result.metadata.sources && result.metadata.sources.length > 0 && (
                                <span>출처: {result.metadata.sources.length}개</span>
                              )}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-sm text-muted-foreground">
                          {result.error || "이 RAG 시스템에서는 관련 정보를 찾을 수 없었습니다."}
                        </div>
                      )}
                    </CardContent>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          )
        })}
      </div>
    </div>
  )
}