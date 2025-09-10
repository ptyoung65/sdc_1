// User types
export interface User {
  id: string
  username: string
  email: string
  displayName?: string
  avatar?: string
  role: UserRole
  createdAt: string
  updatedAt: string
}

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  MODERATOR = 'moderator'
}

// Chat types
export interface Message {
  id: string
  content: string
  role: MessageRole
  timestamp: string
  userId?: string
  conversationId: string
  metadata?: MessageMetadata
  sources?: DocumentSource[]
  isStreaming?: boolean
  error?: string
  rating?: number
}

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system'
}

export interface StreamingMessage {
  type: 'content' | 'metadata' | 'error' | 'done'
  content?: string
  sources?: DocumentSource[]
  error?: string
  metadata?: any
}

export interface MessageMetadata {
  model?: string
  temperature?: number
  tokens?: {
    prompt: number
    completion: number
    total: number
  }
  processingTime?: number
  confidence?: number
  attachments?: {
    name: string
    size: number
    type: string
  }[]
  hasMultiRAG?: boolean
  ragResults?: any
}

export interface Conversation {
  id: string
  title: string
  userId: string
  messages: Message[]
  createdAt: string
  updatedAt: string
  isArchived?: boolean
  tags?: string[]
}

// Document types
export interface Document {
  id: string
  title: string
  content: string
  type: DocumentType
  size: number
  uploadedBy: string
  uploadedAt: string
  status: DocumentStatus
  metadata?: DocumentMetadata
  chunks?: DocumentChunk[]
}

export enum DocumentType {
  PDF = 'pdf',
  TXT = 'txt',
  DOCX = 'docx',
  MD = 'md',
  HTML = 'html'
}

export enum DocumentStatus {
  UPLOADING = 'uploading',
  PROCESSING = 'processing',
  READY = 'ready',
  ERROR = 'error'
}

export interface DocumentMetadata {
  author?: string
  createdAt?: string
  language?: string
  pageCount?: number
  wordCount?: number
  extractedImages?: number
}

export interface DocumentChunk {
  id: string
  documentId: string
  content: string
  startIndex: number
  endIndex: number
  embedding?: number[]
  metadata?: {
    page?: number
    section?: string
    title?: string
  }
}

export interface DocumentSource {
  id: string
  title: string
  type: DocumentType
  relevance: number
  snippet: string
  page?: number
  url?: string
}

// Search types
export interface SearchQuery {
  query: string
  filters?: SearchFilters
  options?: SearchOptions
}

export interface SearchFilters {
  documentTypes?: DocumentType[]
  dateRange?: {
    start: string
    end: string
  }
  authors?: string[]
  tags?: string[]
}

export interface SearchOptions {
  limit?: number
  threshold?: number
  hybridWeight?: number
  includeMetadata?: boolean
}

export interface SearchResult {
  id: string
  score: number
  document: Document
  chunk: DocumentChunk
  highlights?: string[]
}

// API types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  pagination?: Pagination
}

export interface Pagination {
  page: number
  limit: number
  total: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
  timestamp: string
}

// Chat streaming types - removed duplicate, using the one defined earlier

export interface ChatRequest {
  message: string
  conversationId?: string
  options?: {
    model?: string
    temperature?: number
    maxTokens?: number
    stream?: boolean
  }
  context?: {
    documents?: string[]
    searchQuery?: string
  }
}

export interface ChatResponse {
  id: string
  message: Message
  conversation: Conversation
  usage?: {
    promptTokens: number
    completionTokens: number
    totalTokens: number
  }
}

// Dashboard types
export interface DashboardStats {
  totalUsers: number
  totalConversations: number
  totalDocuments: number
  totalMessages: number
  averageResponseTime: number
  systemHealth: SystemHealth
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical'
  services: ServiceHealth[]
  uptime: number
  memoryUsage: number
  cpuUsage: number
  diskUsage: number
}

export interface ServiceHealth {
  name: string
  status: 'up' | 'down' | 'degraded'
  responseTime?: number
  lastCheck: string
  url?: string
}

// Chart types for D3.js and Chart.js
export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
}

export interface ChartOptions {
  responsive?: boolean
  maintainAspectRatio?: boolean
  plugins?: {
    legend?: {
      display?: boolean
      position?: 'top' | 'bottom' | 'left' | 'right'
    }
    title?: {
      display?: boolean
      text?: string
    }
  }
  scales?: {
    x?: {
      display?: boolean
      title?: {
        display?: boolean
        text?: string
      }
    }
    y?: {
      display?: boolean
      title?: {
        display?: boolean
        text?: string
      }
    }
  }
}

// Theme types
export type Theme = 'light' | 'dark' | 'system'

// Form types
export interface LoginForm {
  email: string
  password: string
  remember?: boolean
}

export interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  terms: boolean
}

export interface FileUploadForm {
  files: File[]
  tags?: string[]
  description?: string
}

// WebSocket types
export interface WebSocketMessage {
  type: string
  payload: any
  timestamp: string
}

export interface WebSocketState {
  connected: boolean
  error?: string
  lastMessage?: WebSocketMessage
}

// Store types (Zustand)
export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error?: string
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (data: RegisterForm) => Promise<void>
  updateProfile: (data: Partial<User>) => Promise<void>
}

export interface ChatState {
  conversations: Conversation[]
  currentConversation: Conversation | null
  isLoading: boolean
  error?: string
  createConversation: () => void
  selectConversation: (id: string) => void
  sendMessage: (content: string) => Promise<void>
  deleteConversation: (id: string) => void
  updateConversation: (id: string, updates: Partial<Conversation>) => void
}

export interface DocumentState {
  documents: Document[]
  isLoading: boolean
  error?: string
  uploadDocument: (file: File, metadata?: Partial<DocumentMetadata>) => Promise<void>
  deleteDocument: (id: string) => void
  searchDocuments: (query: SearchQuery) => Promise<SearchResult[]>
}

export interface UIState {
  theme: Theme
  sidebarOpen: boolean
  notifications: Notification[]
  toggleSidebar: () => void
  setTheme: (theme: Theme) => void
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
}

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}