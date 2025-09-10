"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Paperclip, Mic, MicOff, Square, Loader2 } from "lucide-react"
import { useDropzone } from "react-dropzone"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card } from "@/components/ui/card"

interface MessageInputProps {
  value: string
  onChange: (value: string) => void
  onSend: (message: string, files?: File[]) => void
  placeholder?: string
  disabled?: boolean
  isLoading?: boolean
  maxLength?: number
  enableFileUpload?: boolean
  enableVoiceInput?: boolean
  className?: string
}

export function MessageInput({
  value,
  onChange,
  onSend,
  placeholder = "메시지를 입력하세요...",
  disabled = false,
  isLoading = false,
  maxLength = 4000,
  enableFileUpload = true,
  enableVoiceInput = false,
  className
}: MessageInputProps) {
  const [files, setFiles] = React.useState<File[]>([])
  const [isRecording, setIsRecording] = React.useState(false)
  const [isFocused, setIsFocused] = React.useState(false)
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  React.useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = "auto"
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
    }
  }, [value])

  // File drop zone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      setFiles(prev => [...prev, ...acceptedFiles])
    },
    noClick: true,
    disabled: !enableFileUpload || disabled,
    accept: {
      'text/*': ['.txt', '.md'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!value.trim() && files.length === 0) return
    if (disabled || isLoading) return

    onSend(value, files.length > 0 ? files : undefined)
    onChange("")
    setFiles([])
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // TODO: Implement voice recording functionality
  }

  const canSend = (value.trim().length > 0 || files.length > 0) && !disabled && !isLoading

  return (
    <div className={cn("relative", className)}>
      {/* File Drop Overlay */}
      <AnimatePresence>
        {isDragActive && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-primary/10 border-2 border-dashed border-primary rounded-lg"
          >
            <div className="text-center">
              <Paperclip className="h-8 w-8 mx-auto mb-2 text-primary" />
              <p className="text-primary font-medium">파일을 드롭하여 업로드</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Uploaded Files */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-3"
          >
            <div className="flex flex-wrap gap-2">
              {files.map((file, index) => (
                <motion.div
                  key={`${file.name}-${index}`}
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  className="flex items-center gap-2 bg-muted px-3 py-2 rounded-md text-sm"
                >
                  <Paperclip className="h-4 w-4" />
                  <span className="truncate max-w-40">{file.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-5 w-5 p-0"
                    onClick={() => removeFile(index)}
                  >
                    ×
                  </Button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <Card 
        className={cn(
          "border-2 transition-colors duration-200",
          isFocused ? "border-primary" : "border-border",
          isDragActive && "border-primary bg-primary/5"
        )}
        {...getRootProps()}
      >
        <form onSubmit={handleSubmit} className="flex items-end gap-2 p-3">
          {/* File Upload Button */}
          {enableFileUpload && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="shrink-0 h-8 w-8"
              disabled={disabled}
              onClick={() => {
                const input = document.createElement('input')
                input.type = 'file'
                input.multiple = true
                input.accept = '.txt,.md,.pdf,.doc,.docx'
                input.onchange = (e) => {
                  const target = e.target as HTMLInputElement
                  if (target.files) {
                    setFiles(prev => [...prev, ...Array.from(target.files!)])
                  }
                }
                input.click()
              }}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
          )}

          {/* Textarea */}
          <div className="flex-1">
            <input {...getInputProps()} />
            <Textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={placeholder}
              className="min-h-[2.5rem] max-h-[7.5rem] resize-none border-0 bg-transparent focus-visible:ring-0 px-0 py-1"
              disabled={disabled}
              maxLength={maxLength}
            />
            
            {/* Character Count */}
            <div className="flex justify-between items-center mt-1 text-xs text-muted-foreground">
              <span></span>
              <span>{value.length}/{maxLength}</span>
            </div>
          </div>

          {/* Voice Input Button */}
          {enableVoiceInput && (
            <Button
              type="button"
              variant={isRecording ? "default" : "ghost"}
              size="icon"
              className="shrink-0 h-8 w-8"
              disabled={disabled}
              onClick={toggleRecording}
            >
              {isRecording ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>
          )}

          {/* Send/Stop Button */}
          <Button
            type="submit"
            size="icon"
            className="shrink-0 h-8 w-8"
            disabled={!canSend}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : canSend ? (
              <Send className="h-4 w-4" />
            ) : (
              <Send className="h-4 w-4 opacity-50" />
            )}
          </Button>
        </form>
      </Card>

      {/* Recording Indicator */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute -top-12 left-4 right-4 bg-destructive text-destructive-foreground px-4 py-2 rounded-md flex items-center gap-2"
          >
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: "0ms" }} />
              <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: "150ms" }} />
              <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: "300ms" }} />
            </div>
            <span className="text-sm font-medium">녹음 중...</span>
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto text-destructive-foreground hover:bg-destructive-foreground/20"
              onClick={toggleRecording}
            >
              <Square className="h-4 w-4" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}