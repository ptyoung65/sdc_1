"use client"

import * as React from "react"
import { ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  className?: string
  showFirstLast?: boolean
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  className,
  showFirstLast = true
}: PaginationProps) {
  const getVisiblePages = (): (number | string)[] => {
    const delta = 2
    const range: number[] = []
    const rangeWithDots: (number | string)[] = []

    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i)
    }

    if (currentPage - delta > 2) {
      rangeWithDots.push(1, '...')
    } else {
      rangeWithDots.push(1)
    }

    rangeWithDots.push(...range)

    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages)
    } else if (totalPages > 1) {
      rangeWithDots.push(totalPages)
    }

    // Remove duplicates
    return rangeWithDots.filter((item, index) => 
      index === 0 || rangeWithDots[index - 1] !== item
    )
  }

  if (totalPages <= 1) {
    return null
  }

  const visiblePages = getVisiblePages()

  return (
    <nav 
      role="navigation" 
      aria-label="pagination" 
      className={cn("flex items-center justify-center", className)}
    >
      <div className="flex items-center gap-1">
        {/* Previous Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage <= 1}
          className="h-8 w-8 p-0"
          aria-label="이전 페이지로 이동"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {/* Page Numbers */}
        <div className="flex items-center gap-1">
          {visiblePages.map((page, index) => {
            if (page === '...') {
              return (
                <div
                  key={`dots-${index}`}
                  className="flex h-8 w-8 items-center justify-center"
                >
                  <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                </div>
              )
            }

            const pageNumber = page as number
            const isActive = pageNumber === currentPage

            return (
              <Button
                key={pageNumber}
                variant={isActive ? "default" : "ghost"}
                size="sm"
                onClick={() => onPageChange(pageNumber)}
                className={cn(
                  "h-8 w-8 p-0",
                  isActive && "bg-primary text-primary-foreground"
                )}
                aria-label={`페이지 ${pageNumber}로 이동`}
                aria-current={isActive ? "page" : undefined}
              >
                {pageNumber}
              </Button>
            )
          })}
        </div>

        {/* Next Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage >= totalPages}
          className="h-8 w-8 p-0"
          aria-label="다음 페이지로 이동"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </nav>
  )
}

// 간단한 페이지 정보 표시 컴포넌트
interface PaginationInfoProps {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  className?: string
}

export function PaginationInfo({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  className
}: PaginationInfoProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  return (
    <div className={cn("text-xs text-muted-foreground", className)}>
      {totalItems > 0 ? (
        <span>
          {startItem}-{endItem} / {totalItems}개
        </span>
      ) : (
        <span>결과가 없습니다</span>
      )}
    </div>
  )
}