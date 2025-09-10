"use client"

import * as React from "react"
import { motion } from "framer-motion"

export function TypingIndicator() {
  return (
    <div className="flex items-center space-x-1">
      <div className="flex space-x-1 bg-muted px-4 py-3 rounded-2xl rounded-bl-sm">
        {[0, 1, 2].map((index) => (
          <motion.div
            key={index}
            className="w-2 h-2 bg-muted-foreground rounded-full"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: index * 0.2,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </div>
  )
}