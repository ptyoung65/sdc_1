import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { Document, DocumentStatus, DocumentType, DocumentState, SearchQuery, SearchResult } from '@/types'
import { generateId } from '@/lib/utils'
import { apiService } from '@/services/api'

interface DocumentStore extends Omit<DocumentState, 'uploadDocument'> {
  // Actions
  loadDocuments: (userId?: string) => Promise<void>
  uploadDocument: (file: File, metadata?: Partial<Document>) => Promise<Document>
  deleteDocument: (id: string) => void
  updateDocument: (id: string, updates: Partial<Document>) => void
  searchDocuments: (query: SearchQuery) => Promise<SearchResult[]>
  getDocument: (id: string) => Document | undefined
  getDocumentsByType: (type: DocumentType) => Document[]
  getDocumentsByStatus: (status: DocumentStatus) => Document[]
  clearDocuments: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | undefined) => void
  
  // Processing queue
  processingQueue: string[]
  addToProcessingQueue: (documentId: string) => void
  removeFromProcessingQueue: (documentId: string) => void
  
  // Search history
  searchHistory: string[]
  addSearchQuery: (query: string) => void
  clearSearchHistory: () => void
}

export const useDocumentStore = create<DocumentStore>()(
  persist(
    (set, get) => ({
      // Initial state
      documents: [],
      isLoading: false,
      processingQueue: [],
      searchHistory: [],

      // Load documents from API
      loadDocuments: async (userId = 'default_user') => {
        try {
          set({ isLoading: true })
          const documents = await apiService.getUserDocuments(userId)
          
          // Convert backend format to frontend format
          const convertedDocuments: Document[] = documents.map((doc: any) => ({
            id: doc.id || generateId(),
            title: doc.filename || doc.title || 'Untitled',
            content: doc.content || '',
            type: getDocumentTypeFromExtension(doc.filename),
            size: doc.file_size || doc.size || 0,
            uploadedBy: userId,
            uploadedAt: doc.created_at || doc.uploadedAt || new Date().toISOString(),
            status: DocumentStatus.READY, // Assume loaded documents are ready
            metadata: {
              pageCount: 0,
              wordCount: 0,
              extractedImages: 0,
              ...(doc.metadata || {})
            },
            chunks: []
          }))

          set({ 
            documents: convertedDocuments,
            isLoading: false
          })
          get().setError(undefined)
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '문서 목록을 불러오는 중 오류가 발생했습니다.'
          set({ isLoading: false })
          get().setError(errorMessage)
          throw error
        }
      },

      // Document management
      uploadDocument: async (file: File, metadata = {}) => {
        try {
          set({ isLoading: true })

          // Create document object
          const document: Document = {
            id: generateId(),
            title: metadata.title || file.name.replace(/\.[^/.]+$/, ''), // Remove extension
            content: '', // Will be populated after processing
            type: getDocumentTypeFromFile(file),
            size: file.size,
            uploadedBy: 'current-user', // TODO: Get from auth store
            uploadedAt: new Date().toISOString(),
            status: DocumentStatus.UPLOADING,
            metadata: {
              ...metadata,
              pageCount: 0,
              wordCount: 0,
              extractedImages: 0,
            },
            chunks: [],
          }

          // Add to documents list
          set((state) => ({
            documents: [document, ...state.documents]
          }))

          // Add to processing queue
          get().addToProcessingQueue(document.id)

          // TODO: Replace with actual API call
          // const response = await documentApi.upload(file, metadata)

          // Mock file processing
          await mockFileProcessing(file, document)

          // Update document status
          const processedDocument: Document = {
            ...document,
            status: DocumentStatus.READY,
            content: generateMockContent(file),
            metadata: {
              ...document.metadata!,
              pageCount: Math.floor(Math.random() * 50) + 1,
              wordCount: Math.floor(Math.random() * 10000) + 500,
              extractedImages: Math.floor(Math.random() * 5),
            },
            chunks: generateMockChunks(document.id),
          }

          // Remove from processing queue
          get().removeFromProcessingQueue(document.id)

          // Update document in store
          const updateData: any = {
            status: DocumentStatus.READY,
            content: processedDocument.content,
          }
          if (processedDocument.metadata) {
            updateData.metadata = processedDocument.metadata
          }
          if (processedDocument.chunks) {
            updateData.chunks = processedDocument.chunks
          }
          get().updateDocument(document.id, updateData)

          set({ isLoading: false })
          return processedDocument

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '파일 업로드 중 오류가 발생했습니다.'
          
          // Update document status to error
          const documents = get().documents || []
          if (documents.length > 0) {
            const lastDocument = documents[0]
            if (lastDocument) {
              get().updateDocument(lastDocument.id, {
                status: DocumentStatus.ERROR,
              })
              get().removeFromProcessingQueue(lastDocument.id)
            }
          }

          set({
            isLoading: false,
            error: errorMessage,
          })
          throw error
        }
      },

      deleteDocument: (id: string) => {
        set((state) => ({
          documents: (state.documents || []).filter(d => d.id !== id),
          processingQueue: (state.processingQueue || []).filter(qid => qid !== id),
        }))
      },

      updateDocument: (id: string, updates: Partial<Document>) => {
        set((state) => ({
          documents: (state.documents || []).map(d =>
            d.id === id ? { ...d, ...updates } : d
          )
        }))
      },

      searchDocuments: async (query: SearchQuery) => {
        try {
          set({ isLoading: true })

          // Add to search history
          if (query.query.trim()) {
            get().addSearchQuery(query.query)
          }

          // TODO: Replace with actual API call
          // const results = await documentApi.search(query)

          // Mock search implementation
          const results = mockSearchDocuments(query, get().documents)
          
          set({ isLoading: false })
          return results

        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : '검색 중 오류가 발생했습니다.'
          })
          throw error
        }
      },

      getDocument: (id: string) => {
        return (get().documents || []).find(d => d.id === id)
      },

      getDocumentsByType: (type: DocumentType) => {
        return (get().documents || []).filter(d => d.type === type)
      },

      getDocumentsByStatus: (status: DocumentStatus) => {
        return (get().documents || []).filter(d => d.status === status)
      },

      clearDocuments: () => {
        set({
          documents: [],
          processingQueue: [],
          searchHistory: [],
        })
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },

      setError: (error: string | undefined) => {
        if (error !== undefined) {
          set({ error } as Partial<DocumentStore>)
        } else {
          const state = get()
          delete (state as any).error
          set(state)
        }
      },

      // Processing queue management
      addToProcessingQueue: (documentId: string) => {
        set((state) => ({
          processingQueue: [...(state.processingQueue || []), documentId]
        }))
      },

      removeFromProcessingQueue: (documentId: string) => {
        set((state) => ({
          processingQueue: (state.processingQueue || []).filter(id => id !== documentId)
        }))
      },

      // Search history
      addSearchQuery: (query: string) => {
        set((state) => {
          const trimmedQuery = query.trim()
          if (!trimmedQuery) return state

          const newHistory = [
            trimmedQuery,
            ...(state.searchHistory || []).filter(q => q !== trimmedQuery)
          ].slice(0, 10) // Keep last 10 searches

          return { searchHistory: newHistory }
        })
      },

      clearSearchHistory: () => {
        set({ searchHistory: [] })
      },
    }),
    {
      name: 'sdc-document-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        documents: state.documents,
        searchHistory: state.searchHistory,
      }),
    }
  )
)

// Helper functions
function getDocumentTypeFromFile(file: File): DocumentType {
  const extension = file.name.split('.').pop()?.toLowerCase()
  return getDocumentTypeFromExtension(extension)
}

function getDocumentTypeFromExtension(filename?: string): DocumentType {
  if (!filename) return DocumentType.TXT
  const extension = filename.split('.').pop()?.toLowerCase()
  
  switch (extension) {
    case 'pdf':
      return DocumentType.PDF
    case 'doc':
    case 'docx':
      return DocumentType.DOCX
    case 'txt':
      return DocumentType.TXT
    case 'md':
      return DocumentType.MD
    case 'html':
    case 'htm':
      return DocumentType.HTML
    default:
      return DocumentType.TXT
  }
}

async function mockFileProcessing(file: File, document: Document): Promise<void> {
  // Simulate processing time based on file size
  const processingTime = Math.min(file.size / 1000000 * 2000, 5000) // Max 5 seconds
  await new Promise(resolve => setTimeout(resolve, processingTime))
}

function generateMockContent(file: File): string {
  const fileName = file.name
  
  return `# ${fileName}

이것은 "${fileName}" 파일의 처리된 내용입니다.

## 문서 요약
이 문서는 ${file.type || '알 수 없는 형식'}의 파일로, 크기는 ${(file.size / 1024).toFixed(1)}KB입니다.

## 주요 내용
- 파일명: ${fileName}
- 업로드 시간: ${new Date().toLocaleString('ko-KR')}
- 처리 상태: 완료

## 추출된 내용
실제 서비스에서는 여기에 문서의 실제 내용이 표시됩니다. PDF, DOCX, TXT 등 다양한 형식의 파일을 분석하여 텍스트를 추출하고, 이를 바탕으로 질문에 답변할 수 있습니다.

### 기술적 세부사항
- 임베딩 모델: KURE-v1 (한국어 특화)
- 청킹 방식: RecursiveCharacterTextSplitter
- 벡터 데이터베이스: Milvus
- 검색 방식: 하이브리드 (벡터 + 키워드)

이 문서의 내용을 바탕으로 관련 질문을 하시면 정확한 답변을 제공할 수 있습니다.`
}

function generateMockChunks(documentId: string) {
  return [
    {
      id: generateId(),
      documentId,
      content: '이것은 문서의 첫 번째 청크입니다. 문서 제목과 개요 정보를 포함합니다.',
      startIndex: 0,
      endIndex: 150,
      metadata: { section: '서론', page: 1 }
    },
    {
      id: generateId(),
      documentId,
      content: '문서의 주요 내용을 담고 있는 두 번째 청크입니다. 핵심 정보와 데이터를 포함합니다.',
      startIndex: 150,
      endIndex: 300,
      metadata: { section: '본문', page: 2 }
    },
    {
      id: generateId(),
      documentId,
      content: '문서의 결론 부분에 해당하는 세 번째 청크입니다. 요약과 향후 계획을 담고 있습니다.',
      startIndex: 300,
      endIndex: 450,
      metadata: { section: '결론', page: 3 }
    }
  ]
}

function mockSearchDocuments(query: SearchQuery, documents: Document[]): SearchResult[] {
  const searchTerm = query.query.toLowerCase()
  
  return documents
    .filter(doc => {
      // Apply filters
      if (query.filters?.documentTypes && !query.filters.documentTypes.includes(doc.type)) {
        return false
      }
      
      if (query.filters?.dateRange) {
        const docDate = new Date(doc.uploadedAt)
        const startDate = new Date(query.filters.dateRange.start)
        const endDate = new Date(query.filters.dateRange.end)
        
        if (docDate < startDate || docDate > endDate) {
          return false
        }
      }

      // Text search
      return (
        doc.title.toLowerCase().includes(searchTerm) ||
        doc.content.toLowerCase().includes(searchTerm)
      )
    })
    .map(doc => {
      // Calculate relevance score (mock)
      const titleMatch = doc.title.toLowerCase().includes(searchTerm)
      const contentMatch = doc.content.toLowerCase().includes(searchTerm)
      
      let score = 0
      if (titleMatch) score += 0.8
      if (contentMatch) score += 0.6
      
      // Find best matching chunk
      const bestChunk = doc.chunks?.[0] || {
        id: generateId(),
        documentId: doc.id,
        content: doc.content.substring(0, 200) + '...',
        startIndex: 0,
        endIndex: 200,
      }

      return {
        id: generateId(),
        score,
        document: doc,
        chunk: bestChunk,
        highlights: [searchTerm],
      }
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, query.options?.limit || 10)
}