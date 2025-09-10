"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Star, MessageSquare, ThumbsUp, ThumbsDown } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"

interface MessageRatingProps {
  messageId: string
  userId: string
  currentRating?: number
  currentFeedback?: string
  onRate: (rating: number, feedback?: string) => void
  className?: string
}

export function MessageRating({
  messageId,
  userId,
  currentRating,
  currentFeedback,
  onRate,
  className
}: MessageRatingProps) {
  const [selectedRating, setSelectedRating] = React.useState(currentRating || 0)
  const [hoverRating, setHoverRating] = React.useState(0)
  const [feedback, setFeedback] = React.useState(currentFeedback || "")
  const [showFeedback, setShowFeedback] = React.useState(false)
  const [isSubmitting, setIsSubmitting] = React.useState(false)

  const handleStarClick = async (rating: number) => {
    if (isSubmitting) return
    
    setSelectedRating(rating)
    setIsSubmitting(true)
    
    try {
      await onRate(rating, feedback || undefined)
      
      // Show feedback input for ratings <= 3
      if (rating <= 3 && !feedback) {
        setShowFeedback(true)
      }
    } catch (error) {
      console.error("Failed to submit rating:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleFeedbackSubmit = async () => {
    if (isSubmitting) return
    
    setIsSubmitting(true)
    
    try {
      await onRate(selectedRating, feedback || undefined)
      setShowFeedback(false)
    } catch (error) {
      console.error("Failed to submit feedback:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const ratingLabels = {
    1: "매우 불만족",
    2: "불만족", 
    3: "보통",
    4: "만족",
    5: "매우 만족"
  }

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {/* Star Rating */}
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Button
            key={star}
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            disabled={isSubmitting}
            onMouseEnter={() => setHoverRating(star)}
            onMouseLeave={() => setHoverRating(0)}
            onClick={() => handleStarClick(star)}
          >
            <Star
              className={cn(
                "h-4 w-4 transition-colors",
                (hoverRating >= star || selectedRating >= star)
                  ? "fill-yellow-400 text-yellow-400"
                  : "text-muted-foreground"
              )}
            />
          </Button>
        ))}
        
        {selectedRating > 0 && (
          <motion.span
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="ml-2 text-xs text-muted-foreground"
          >
            {ratingLabels[selectedRating as keyof typeof ratingLabels]}
          </motion.span>
        )}
      </div>

      {/* Quick Feedback Buttons */}
      {selectedRating > 0 && selectedRating <= 3 && !showFeedback && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="flex gap-2"
        >
          <Button
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={() => setShowFeedback(true)}
            disabled={isSubmitting}
          >
            <MessageSquare className="h-3 w-3 mr-1" />
            피드백 작성
          </Button>
        </motion.div>
      )}

      {/* Feedback Input */}
      <AnimatePresence>
        {showFeedback && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <Card className="p-3">
              <Textarea
                placeholder="개선할 점이나 의견을 자유롭게 작성해주세요..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="min-h-[60px] text-sm"
                disabled={isSubmitting}
              />
              <div className="flex justify-end gap-2 mt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFeedback(false)}
                  disabled={isSubmitting}
                >
                  취소
                </Button>
                <Button
                  size="sm"
                  onClick={handleFeedbackSubmit}
                  disabled={isSubmitting || !feedback.trim()}
                >
                  {isSubmitting ? "저장 중..." : "저장"}
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Current Feedback Display */}
      {currentFeedback && !showFeedback && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-xs text-muted-foreground bg-muted/50 p-2 rounded-md"
        >
          <span className="font-medium">피드백: </span>
          {currentFeedback}
        </motion.div>
      )}
    </div>
  )
}

// Compact version for message bubbles
export function CompactMessageRating({
  messageId,
  userId,
  currentRating,
  onRate,
  className
}: Pick<MessageRatingProps, "messageId" | "userId" | "currentRating" | "onRate" | "className">) {
  const [isRating, setIsRating] = React.useState(false)
  const [selectedRating, setSelectedRating] = React.useState(currentRating || 0)

  const handleQuickRate = async (rating: number) => {
    setIsRating(true)
    setSelectedRating(rating)
    
    try {
      await onRate(rating)
    } catch (error) {
      console.error("Failed to submit rating:", error)
    } finally {
      setIsRating(false)
    }
  }

  return (
    <div className={cn("flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity", className)}>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0"
        onClick={() => handleQuickRate(5)}
        disabled={isRating}
      >
        <ThumbsUp 
          className={cn(
            "h-3 w-3",
            selectedRating >= 4 ? "text-green-600" : "text-muted-foreground"
          )} 
        />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0"
        onClick={() => handleQuickRate(2)}
        disabled={isRating}
      >
        <ThumbsDown 
          className={cn(
            "h-3 w-3",
            selectedRating <= 2 && selectedRating > 0 ? "text-red-600" : "text-muted-foreground"
          )} 
        />
      </Button>
      
      {selectedRating > 0 && (
        <div className="flex items-center ml-1">
          <Star
            className={cn(
              "h-3 w-3",
              "fill-yellow-400 text-yellow-400"
            )}
          />
          <span className="text-xs text-muted-foreground ml-1">
            {selectedRating}
          </span>
        </div>
      )}
    </div>
  )
}