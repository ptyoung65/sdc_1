"use client"

import React from 'react'
import { LazyMotion, domAnimation, MotionConfig } from 'framer-motion'

interface MotionProviderProps {
  children: React.ReactNode
}

export function MotionProvider({ children }: MotionProviderProps) {
  return (
    <LazyMotion features={domAnimation}>
      <MotionConfig reducedMotion="user">
        {children}
      </MotionConfig>
    </LazyMotion>
  )
}