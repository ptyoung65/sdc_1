// Re-export all stores for easy importing
import { useAuthStore } from './auth-store'
import { useChatStore } from './chat-store'
import { useUIStore, useNotifications, useTheme } from './ui-store'
import { useDocumentStore } from './document-store'

export { useAuthStore, useChatStore, useUIStore, useNotifications, useTheme, useDocumentStore }

// Combined store hook for accessing all stores
export const useStores = () => ({
  auth: useAuthStore(),
  chat: useChatStore(), 
  ui: useUIStore(),
  document: useDocumentStore(),
})