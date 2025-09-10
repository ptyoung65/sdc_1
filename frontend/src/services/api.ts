// API 서비스
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LLMProvider {
  id: string;
  name: string;
  model: string;
  available: boolean;
  default: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface ChatRequest {
  message: string;
  provider?: string;
  system_prompt?: string;
  conversation_history?: ChatMessage[];
  use_rag?: boolean;
  use_web_search?: boolean;
  web_search_engines?: string[];
  search_mode?: 'documents' | 'web' | 'combined';
  use_agentic_rag?: boolean;
  agentic_complexity_threshold?: number;
  user_id?: string;
  conversation_id?: string;
  enabled_rag_types?: {
    vector?: boolean;
    graph?: boolean;
    keyword?: boolean;
    database?: boolean;
  };
}

export interface RAGResult {
  type: 'vector' | 'graph' | 'keyword' | 'database';
  success: boolean;
  response?: string;
  error?: string;
  metadata?: {
    sources?: string[];
    confidence?: number;
    processingTime?: number;
    resultCount?: number;
  };
}

export interface ChatResponse {
  success: boolean;
  response: string;
  provider?: string;
  model?: string;
  error?: string;
  tokens?: {
    prompt?: number;
    completion?: number;
    total?: number;
  };
  sources?: Array<{
    document_id?: string;
    filename?: string;
    content_preview?: string;
    score?: number;
  }>;
  message_id?: string;
  conversation_id?: string;
  rag_results?: RAGResult[];
  has_multi_rag?: boolean;
}

export interface RatingRequest {
  message_id: string;
  user_id: string;
  rating: number;
  feedback?: string;
}

export interface WebSearchRequest {
  query: string;
  category?: string;
  engines?: string[];
  language?: string;
}

export interface WebSearchResult {
  title: string;
  url: string;
  content: string;
  snippet: string;
  engine: string;
  score: number;
}

export interface WebSearchResponse {
  success: boolean;
  query: string;
  number_of_results: number;
  results: WebSearchResult[];
  suggestions: string[];
  error?: string;
}

export interface SearchEngine {
  id: string;
  name: string;
  description: string;
  available: boolean;
}

export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  metadata?: any;
  sources?: any[];
  created_at: string;
  rating?: number;
  feedback?: string;
}

class APIService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // LLM 제공자 목록 가져오기
  async getProviders(): Promise<LLMProvider[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/providers`);
      if (!response.ok) throw new Error('Failed to fetch providers');
      const data = await response.json();
      
      // 백엔드 응답을 프론트엔드 형식으로 변환
      return (data.providers || []).map((provider: any, index: number) => ({
        id: provider.name,
        name: provider.display_name,
        model: provider.models?.[0] || provider.name,
        available: provider.available,
        default: index === 0 // 첫 번째를 기본값으로
      }));
    } catch (error) {
      console.error('Error fetching providers:', error);
      // API 실패 시 fallback 데이터 반환
      return [
        {
          id: 'gemini',
          name: 'Google Gemini',
          model: 'gemini-pro',
          available: true,
          default: true
        },
        {
          id: 'claude',
          name: 'Anthropic Claude',
          model: 'claude-3-sonnet',
          available: false,
          default: false
        }
      ];
    }
  }

  // 채팅 메시지 전송
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message:', error);
      return {
        success: false,
        response: '메시지 전송 중 오류가 발생했습니다.',
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  // 메시지 평가
  async rateMessage(request: RatingRequest): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/messages/rate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error rating message:', error);
      return false;
    }
  }

  // 사용자 대화 목록 조회 (페이지네이션 지원)
  async getUserConversations(userId: string, limit: number = 50, offset: number = 0): Promise<Conversation[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/conversations/${userId}?limit=${limit}&offset=${offset}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      // Backend returns direct array, not wrapped in success/data structure
      return Array.isArray(result) ? result : [];
    } catch (error) {
      console.error('Error fetching conversations:', error);
      return [];
    }
  }

  // 대화 메시지 목록 조회
  async getConversationMessages(conversationId: string): Promise<Message[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/conversations/${conversationId}/messages`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      // Backend returns direct array, not wrapped in success/data structure  
      return Array.isArray(result) ? result : [];
    } catch (error) {
      console.error('Error fetching conversation messages:', error);
      return [];
    }
  }

  // 대화 삭제
  async deleteConversation(conversationId: string, userId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/conversations/${conversationId}?user_id=${userId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error deleting conversation:', error);
      return false;
    }
  }

  // 메시지 평가 조회
  async getMessageRating(messageId: string, userId: string): Promise<{rating: number, feedback?: string} | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/messages/${messageId}/rating/${userId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success ? result.data : null;
    } catch (error) {
      console.error('Error fetching message rating:', error);
      return null;
    }
  }

  // 웹 검색
  async webSearch(request: WebSearchRequest): Promise<WebSearchResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/search/web`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error performing web search:', error);
      return {
        success: false,
        query: request.query,
        number_of_results: 0,
        results: [],
        suggestions: [],
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  // Google 검색
  async googleSearch(request: WebSearchRequest): Promise<WebSearchResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/search/web/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error performing Google search:', error);
      return {
        success: false,
        query: request.query,
        number_of_results: 0,
        results: [],
        suggestions: [],
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  // 사용 가능한 검색엔진 목록 가져오기
  async getSearchEngines(): Promise<SearchEngine[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/search/web/engines`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.engines || [];
    } catch (error) {
      console.error('Error fetching search engines:', error);
      // 기본 검색엔진 목록 반환
      return [
        { id: 'google', name: 'Google', description: '가장 널리 사용되는 검색엔진', available: true },
        { id: 'bing', name: 'Bing', description: 'Microsoft의 검색엔진', available: true },
        { id: 'duckduckgo', name: 'DuckDuckGo', description: '개인정보 보호 중심 검색엔진', available: true },
        { id: 'wikipedia', name: 'Wikipedia', description: '위키피디아 검색', available: true },
      ];
    }
  }

  // 문서 관리 API
  async getUserDocuments(userId: string, limit: number = 20, offset: number = 0): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/documents/${userId}?limit=${limit}&offset=${offset}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.documents || [];
    } catch (error) {
      console.error('Error fetching user documents:', error);
      return [];
    }
  }

  async uploadDocument(userId: string, file: File, metadata?: any): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);
      
      if (metadata) {
        formData.append('metadata', JSON.stringify(metadata));
      }

      const response = await fetch(`${this.baseUrl}/api/v1/documents`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading document:', error);
      throw error;
    }
  }

  async deleteDocument(documentId: string, userId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/documents/${documentId}?user_id=${userId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success || false;
    } catch (error) {
      console.error('Error deleting document:', error);
      return false;
    }
  }

  async getDocumentById(documentId: string, userId: string): Promise<any | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/documents/${documentId}?user_id=${userId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching document:', error);
      return null;
    }
  }

  // 상태 확인
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}

export const apiService = new APIService();