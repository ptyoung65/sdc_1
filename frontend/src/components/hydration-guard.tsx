'use client'

import { useEffect, useState } from 'react'

interface HydrationGuardProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

/**
 * HydrationGuard - Prevents hydration errors from browser extensions
 * 
 * This component ensures that the client-side rendering is stable
 * by waiting for hydration to complete before rendering children.
 * It also prevents browser extensions from interfering with the DOM.
 */
export function HydrationGuard({ children, fallback }: HydrationGuardProps) {
  const [isHydrated, setIsHydrated] = useState(false)

  useEffect(() => {
    // Mark as hydrated after first render
    setIsHydrated(true)

    // Prevent browser extensions from modifying our DOM
    const preventExtensionModification = () => {
      // Remove HIX.AI extension attributes if they exist
      const elements = document.querySelectorAll('[data-hix-id], [data-hix-version], [hix-id], [hix-version]')
      elements.forEach(element => {
        element.removeAttribute('data-hix-id')
        element.removeAttribute('data-hix-version')
        element.removeAttribute('hix-id')
        element.removeAttribute('hix-version')
        // Also remove any attributes with hix prefix
        Array.from(element.attributes).forEach(attr => {
          if (attr.name.includes('hix')) {
            element.removeAttribute(attr.name)
          }
        })
      })
    }

    // Run immediately and on DOM mutations
    preventExtensionModification()

    // Set up MutationObserver to prevent extension modifications
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes') {
          const target = mutation.target as Element
          const attributeName = mutation.attributeName
          if (attributeName && attributeName.includes('hix')) {
            preventExtensionModification()
          }
        }
      })
    })

    observer.observe(document.body, {
      attributes: true,
      subtree: true,
      attributeOldValue: true
    })

    return () => {
      observer.disconnect()
    }
  }, [])

  // During SSR or before hydration, show fallback or nothing
  if (!isHydrated) {
    return fallback || <div className="min-h-screen bg-background" />
  }

  return <>{children}</>
}

/**
 * NoSSR - Component that only renders on the client side
 * Use this for components that have different server/client behavior
 */
export function NoSSR({ children, fallback }: HydrationGuardProps) {
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  if (!isMounted) {
    return fallback || null
  }

  return <>{children}</>
}