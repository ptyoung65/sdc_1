"use client"

import * as React from "react"
import { ToastProvider, ToastViewport } from "@/components/ui/toast"

interface ClientToasterProps {
  children?: React.ReactNode
}

export function ClientToaster({ children }: ClientToasterProps) {
  return (
    <ToastProvider>
      {children}
      <ToastViewport />
    </ToastProvider>
  )
}