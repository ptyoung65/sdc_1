export interface TestResult {
  id: string;
  query: string;
  response: string;
  sources: ChunkDetail[];
  korean_analysis: {
    original_query: string;
    processed_query: string;
    tokenized: string[];
    keywords: string[];
  };
  processing_time: number;
  similarity_threshold: number;
  max_chunks: number;
  timestamp: string;
  status: 'success' | 'error';
}

export interface ChunkDetail {
  chunk_id: string;
  content: string;
  similarity: number;
  metadata: Record<string, any>;
  korean_features?: Record<string, any>;
}

export interface TestHistoryFilters {
  dateFrom?: string;
  dateTo?: string;
  query?: string;
  status?: 'all' | 'success' | 'error';
}