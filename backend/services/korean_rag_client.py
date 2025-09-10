"""
Korean RAG Client
Dummy implementation for compatibility
"""
import asyncio
import json

class KoreanRAGClient:
    def __init__(self):
        self.is_available = True  # 더미이지만 사용 가능한 것으로 표시
        self.base_url = None  # 실제 서버 연결 없음
    
    async def fetch_documents(self, user_id: str, limit: int = 20, offset: int = 0):
        """문서 목록을 가져옵니다 (더미 구현)"""
        # 더미 응답 - 실제 서버 연결 없이 빈 목록 반환
        return []
    
    async def search_context(self, message: str, user_id: str = "default_user"):
        """Korean RAG 컨텍스트 검색 (더미 구현)"""
        return {
            "status": "dummy_mode",
            "message": "Korean RAG service running in dummy mode",
            "contexts": [],
            "sources": []
        }
    
    async def upload_document(self, user_id: str, document_data: dict):
        """문서 업로드 (더미 구현)"""
        return {
            "status": "success",
            "message": "Document uploaded in dummy mode",
            "document_id": f"dummy_{user_id}_{len(document_data.get('content', ''))}"
        }

def get_korean_rag_client():
    """Return a Korean RAG client instance"""
    return KoreanRAGClient()