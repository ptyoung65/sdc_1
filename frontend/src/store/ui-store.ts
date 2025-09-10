import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { Theme, UIState, Notification } from '@/types'
import { generateId } from '@/lib/utils'

interface UIStore extends UIState {
  // Actions
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: Theme) => void
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
  updateNotification: (id: string, updates: Partial<Notification>) => void
  
  // Modal/Dialog state
  isCommandPaletteOpen: boolean
  setCommandPaletteOpen: (open: boolean) => void
  
  // Loading states
  globalLoading: boolean
  setGlobalLoading: (loading: boolean) => void
  
  // Mobile responsive
  isMobile: boolean
  setIsMobile: (mobile: boolean) => void
  
  // Settings
  settings: {
    animations: boolean
    autoSave: boolean
    soundEnabled: boolean
    compactMode: boolean
  }
  updateSettings: (settings: Partial<UIStore['settings']>) => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      // Initial state
      theme: 'system',
      sidebarOpen: true,
      notifications: [],
      isCommandPaletteOpen: false,
      globalLoading: false,
      isMobile: false,
      settings: {
        animations: true,
        autoSave: true,
        soundEnabled: false,
        compactMode: false,
      },

      // Sidebar actions
      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }))
      },

      setSidebarOpen: (open: boolean) => {
        set({ sidebarOpen: open })
      },

      // Theme actions
      setTheme: (theme: Theme) => {
        set({ theme })
        
        // Apply theme to document
        const root = document.documentElement
        root.classList.remove('light', 'dark')
        
        if (theme === 'system') {
          const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches 
            ? 'dark' 
            : 'light'
          root.classList.add(systemTheme)
        } else {
          root.classList.add(theme)
        }
      },

      // Notification actions
      addNotification: (notification) => {
        const newNotification: Notification = {
          ...notification,
          id: generateId(),
        }

        set((state) => ({
          notifications: [newNotification, ...state.notifications].slice(0, 10) // Keep max 10 notifications
        }))

        // Auto-remove notification based on duration
        const duration = notification.duration || 5000
        if (duration > 0) {
          setTimeout(() => {
            get().removeNotification(newNotification.id)
          }, duration)
        }
      },

      removeNotification: (id: string) => {
        set((state) => ({
          notifications: state.notifications.filter(n => n.id !== id)
        }))
      },

      clearNotifications: () => {
        set({ notifications: [] })
      },

      updateNotification: (id: string, updates: Partial<Notification>) => {
        set((state) => ({
          notifications: state.notifications.map(n =>
            n.id === id ? { ...n, ...updates } : n
          )
        }))
      },

      // Command palette
      setCommandPaletteOpen: (open: boolean) => {
        set({ isCommandPaletteOpen: open })
      },

      // Global loading
      setGlobalLoading: (loading: boolean) => {
        set({ globalLoading: loading })
      },

      // Mobile responsive
      setIsMobile: (mobile: boolean) => {
        set({ isMobile: mobile })
        
        // Auto-collapse sidebar on mobile
        if (mobile) {
          set({ sidebarOpen: false })
        }
      },

      // Settings
      updateSettings: (newSettings) => {
        set((state) => ({
          settings: { ...state.settings, ...newSettings }
        }))
      },
    }),
    {
      name: 'sdc-ui-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
        settings: state.settings,
      }),
    }
  )
)

// Notification helper functions
export const useNotifications = () => {
  const { addNotification, removeNotification, notifications } = useUIStore()

  const showSuccess = (title: string, message?: string, duration?: number) => {
    const notif: any = {
      type: 'success',
      title,
    }
    if (message) notif.message = message
    if (duration) notif.duration = duration
    addNotification(notif)
  }

  const showError = (title: string, message?: string, duration?: number) => {
    const notif: any = {
      type: 'error',
      title,
      duration: duration || 10000, // Error notifications last longer by default
    }
    if (message) notif.message = message
    addNotification(notif)
  }

  const showWarning = (title: string, message?: string, duration?: number) => {
    const notif: any = {
      type: 'warning',
      title,
    }
    if (message) notif.message = message
    if (duration) notif.duration = duration
    addNotification(notif)
  }

  const showInfo = (title: string, message?: string, duration?: number) => {
    const notif: any = {
      type: 'info',
      title,
    }
    if (message) notif.message = message
    if (duration) notif.duration = duration
    addNotification(notif)
  }

  return {
    notifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeNotification,
  }
}

// Theme helper hook
export const useTheme = () => {
  const { theme, setTheme } = useUIStore()

  React.useEffect(() => {
    // Initialize theme on mount
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches 
        ? 'dark' 
        : 'light'
      root.classList.add(systemTheme)
      
      // Listen for system theme changes
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = () => {
        if (useUIStore.getState().theme === 'system') {
          root.classList.remove('light', 'dark')
          root.classList.add(mediaQuery.matches ? 'dark' : 'light')
        }
      }
      
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    } else {
      root.classList.add(theme)
      return undefined
    }
  }, [theme])

  React.useEffect(() => {
    // Handle mobile responsiveness
    const checkMobile = () => {
      const mobile = window.innerWidth < 768
      useUIStore.getState().setIsMobile(mobile)
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  return { theme, setTheme }
}

// Add React import for useEffect
import * as React from 'react'