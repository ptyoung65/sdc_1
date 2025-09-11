"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { 
  MessageSquare, 
  FileText, 
  Search, 
  Zap, 
  ArrowRight,
  Sparkles
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

interface WelcomeScreenProps {
  onSendMessage: (message: string, files?: File[]) => void
}

const suggestedQuestions = [
  {
    icon: MessageSquare,
    title: "일반 질문",
    message: "SDC Gen AI는 어떤 기능을 제공하나요?",
    description: "서비스의 주요 기능에 대해 알아보세요"
  },
  {
    icon: FileText,
    title: "문서 분석",
    message: "업로드한 문서를 분석해주세요",
    description: "PDF, DOCX 등 다양한 문서 형식 지원"
  },
  {
    icon: Search,
    title: "검색 질문",
    message: "최신 AI 기술 동향을 알려주세요",
    description: "실시간 웹 검색을 통한 최신 정보"
  },
  {
    icon: Zap,
    title: "코딩 도움",
    message: "React 컴포넌트 작성을 도와주세요",
    description: "프로그래밍 관련 질문과 코드 리뷰"
  }
]

const features = [
  {
    title: "멀티 LLM",
    description: "다양한 AI 모델을 활용한 최적의 답변"
  },
  {
    title: "한국어 특화",
    description: "KURE-v1 임베딩으로 정확한 한국어 처리"
  },
  {
    title: "RAG 검색",
    description: "문서 기반 검색으로 신뢰할 수 있는 정보"
  },
  {
    title: "실시간 웹검색",
    description: "Searxng를 통한 최신 정보 제공"
  }
]

export function WelcomeScreen({ onSendMessage }: WelcomeScreenProps) {
  const containerVariants = {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        duration: 0.5,
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.4 }
    }
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="initial"
      animate="animate"
      className="flex flex-col items-center justify-center min-h-full p-8 text-center"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="mb-8">
        <h1 className="text-3xl font-bold gradient-text mb-2">
          SDC Gen AI에 오신 것을 환영합니다
        </h1>
        <p className="text-lg text-muted-foreground max-w-md">
          대화형 AI 서비스로 무엇이든 물어보세요
        </p>
      </motion.div>

      {/* Features */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 gap-3 mb-8 max-w-md">
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            variants={itemVariants}
            className="bg-muted/50 rounded-lg p-3 text-left"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
          >
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="font-medium text-sm">{feature.title}</span>
            </div>
            <p className="text-xs text-muted-foreground">{feature.description}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* Suggested Questions */}
      <motion.div variants={itemVariants} className="w-full max-w-2xl">
        <h2 className="text-lg font-semibold mb-4 text-left">
          이런 것들을 물어보세요
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {suggestedQuestions.map((question, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Card 
                className="cursor-pointer hover:bg-muted/50 transition-colors border-muted"
                onClick={() => onSendMessage(question.message)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="shrink-0 h-8 w-8 bg-primary/10 rounded-lg flex items-center justify-center">
                      <question.icon className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1 text-left">
                      <h3 className="font-medium text-sm mb-1">{question.title}</h3>
                      <p className="text-xs text-muted-foreground mb-2">
                        {question.description}
                      </p>
                      <div className="flex items-center gap-1 text-xs text-primary">
                        <span className="truncate">{question.message}</span>
                        <ArrowRight className="h-3 w-3 shrink-0" />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Bottom hint */}
      <motion.div 
        variants={itemVariants}
        className="mt-8 text-sm text-muted-foreground"
      >
        <p>
          아래 입력창에 직접 질문을 입력하거나 파일을 첨부할 수 있습니다
        </p>
      </motion.div>
    </motion.div>
  )
}