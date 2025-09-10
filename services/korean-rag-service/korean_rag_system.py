"""
Korean RAG System
한국어 RAG (Retrieval-Augmented Generation) 시스템
문서 검색 기반 질의응답 시스템
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime
from milvus_storage import get_milvus_storage
from korean_embeddings import get_korean_embedding_service
from korean_chunker import get_korean_chunker

logger = logging.getLogger(__name__)

class KoreanRAGSystem:
    def __init__(self):
        """
        한국어 RAG 시스템 초기화 (Graceful fallback 지원)
        """
        try:
            self.vector_storage = get_milvus_storage()
        except Exception as e:
            logger.error(f"벡터 스토리지 초기화 실패: {e}")
            self.vector_storage = None
            
        try:
            self.embedding_service = get_korean_embedding_service()
        except Exception as e:
            logger.error(f"임베딩 서비스 초기화 실패: {e}")
            self.embedding_service = None
            
        try:
            self.chunker = get_korean_chunker()
        except Exception as e:
            logger.error(f"청킹 서비스 초기화 실패: {e}")
            self.chunker = None
        
        # RAG 설정
        self.max_context_chunks = 5  # LLM에 전달할 최대 청크 수
        self.similarity_threshold = 0.3  # 유사도 임계값
        self.max_context_length = 2000  # 최대 컨텍스트 길이
        
        # 초기화 상태 체크
        self.is_fully_operational = all([
            self.vector_storage is not None and getattr(self.vector_storage, 'collection', None) is not None,
            self.embedding_service is not None,
            self.chunker is not None
        ])
        
        if self.is_fully_operational:
            logger.info("Korean RAG 시스템 초기화 완료 - 모든 서비스 정상")
        else:
            logger.warning("Korean RAG 시스템 초기화 완료 - 일부 서비스 비활성화 (Graceful fallback 모드)")
    
    def add_document(self, 
                    title: str, 
                    content: str, 
                    metadata: Dict[str, Any] = None,
                    document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        새 문서를 RAG 시스템에 추가
        
        Args:
            title: 문서 제목
            content: 문서 내용
            metadata: 추가 메타데이터
            document_id: 문서 ID (없으면 자동 생성)
            
        Returns:
            추가 결과
        """
        try:
            # 문서 ID 생성
            if not document_id:
                document_id = f"doc_{uuid.uuid4().hex[:8]}"
            
            # 메타데이터 준비
            doc_metadata = {
                "title": title,
                "created_at": datetime.now().isoformat(),
                "type": "document",
                **(metadata or {})
            }
            
            # 벡터 스토리지에 저장
            result = self.vector_storage.store_document(
                document_id=document_id,
                text=content,
                metadata=doc_metadata
            )
            
            if result.get("status") == "success":
                logger.info(f"문서 추가 성공: {title} ({document_id})")
                return {
                    "status": "success",
                    "document_id": document_id,
                    "title": title,
                    "chunks_created": result.get("chunks_stored", 0),
                    "message": f"문서가 성공적으로 추가되었습니다. {result.get('chunks_stored', 0)}개 청크 생성"
                }
            else:
                logger.error(f"문서 추가 실패: {result.get('message', 'Unknown error')}")
                return {
                    "status": "error",
                    "message": f"문서 추가 실패: {result.get('message', 'Unknown error')}"
                }
                
        except Exception as e:
            logger.error(f"문서 추가 중 오류: {e}")
            return {
                "status": "error", 
                "message": f"문서 추가 중 오류가 발생했습니다: {str(e)}"
            }
    
    def retrieve_relevant_context(self, query: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        쿼리와 관련된 컨텍스트 검색
        
        Args:
            query: 사용자 질문
            
        Returns:
            (검색된 청크 리스트, 컨텍스트 문자열)
        """
        try:
            # 유사한 청크 검색
            similar_chunks = self.vector_storage.search_similar(
                query=query,
                top_k=self.max_context_chunks,
                score_threshold=self.similarity_threshold
            )
            
            if not similar_chunks:
                logger.info("관련 컨텍스트를 찾지 못했습니다")
                return [], ""
            
            # 컨텍스트 구성
            context_parts = []
            total_length = 0
            used_chunks = []
            
            for chunk in similar_chunks:
                chunk_text = chunk.get("text", "")
                chunk_length = len(chunk_text)
                
                # 길이 제한 확인
                if total_length + chunk_length <= self.max_context_length:
                    context_parts.append(f"[문서 {chunk.get('document_id', 'unknown')}] {chunk_text}")
                    total_length += chunk_length
                    used_chunks.append(chunk)
                else:
                    break
            
            context_string = "\n\n".join(context_parts)
            
            logger.info(f"컨텍스트 검색 완료: {len(used_chunks)}개 청크, {total_length}자")
            
            return used_chunks, context_string
            
        except Exception as e:
            logger.error(f"컨텍스트 검색 중 오류: {e}")
            return [], ""
    
    def generate_rag_prompt(self, query: str, context: str) -> str:
        """
        RAG를 위한 프롬프트 생성
        
        Args:
            query: 사용자 질문
            context: 검색된 컨텍스트
            
        Returns:
            LLM용 프롬프트
        """
        if not context:
            return f"""다음 질문에 답변해주세요:

질문: {query}

참고할 수 있는 문서가 없어 일반적인 지식으로 답변드리겠습니다."""

        prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.

=== 참고 문서 ===
{context}

=== 질문 ===
{query}

=== 답변 지침 ===
1. 위 참고 문서의 내용을 기반으로 정확하게 답변하세요
2. 문서에 없는 내용은 추측하지 마세요
3. 한국어로 자연스럽게 답변하세요
4. 가능하면 참고한 문서를 언급하세요

답변:"""
        
        return prompt
    
    def search_and_answer(self, query: str) -> Dict[str, Any]:
        """
        질문 검색 및 답변 생성을 위한 정보 반환
        
        Args:
            query: 사용자 질문
            
        Returns:
            RAG 정보가 포함된 결과
        """
        try:
            # 관련 컨텍스트 검색
            relevant_chunks, context_string = self.retrieve_relevant_context(query)
            
            # RAG 프롬프트 생성
            rag_prompt = self.generate_rag_prompt(query, context_string)
            
            # 결과 구성
            result = {
                "query": query,
                "has_context": bool(context_string),
                "context_chunks_count": len(relevant_chunks),
                "context": context_string,
                "rag_prompt": rag_prompt,
                "relevant_chunks": relevant_chunks,
                "similarity_threshold_used": self.similarity_threshold
            }
            
            logger.info(f"RAG 검색 완료: {len(relevant_chunks)}개 청크 찾음")
            
            return result
            
        except Exception as e:
            logger.error(f"RAG 검색 중 오류: {e}")
            return {
                "query": query,
                "has_context": False,
                "context_chunks_count": 0,
                "context": "",
                "rag_prompt": self.generate_rag_prompt(query, ""),
                "relevant_chunks": [],
                "error": str(e)
            }
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        문서 삭제
        
        Args:
            document_id: 삭제할 문서 ID
            
        Returns:
            삭제 결과
        """
        try:
            success = self.vector_storage.delete_document(document_id)
            
            if success:
                return {
                    "status": "success",
                    "message": f"문서 {document_id}가 삭제되었습니다"
                }
            else:
                return {
                    "status": "error",
                    "message": f"문서 {document_id} 삭제 실패"
                }
                
        except Exception as e:
            logger.error(f"문서 삭제 중 오류: {e}")
            return {
                "status": "error",
                "message": f"문서 삭제 중 오류: {str(e)}"
            }
    
    def list_documents(self) -> Dict[str, Any]:
        """
        저장된 문서 목록 조회
        
        Returns:
            문서 목록 및 통계
        """
        try:
            # 실제 문서 목록 조회
            documents = self.vector_storage.get_all_documents()
            stats = self.vector_storage.get_collection_stats()
            
            return {
                "status": "success",
                "total_documents": len(documents),
                "total_chunks": stats.get("total_chunks", 0),
                "documents": documents,
                "collection_stats": stats
            }
            
        except Exception as e:
            logger.error(f"문서 목록 조회 중 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "total_documents": 0,
                "total_chunks": 0,
                "documents": []
            }
    
    def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """
        문서 내용 상세 조회
        
        Args:
            document_id: 조회할 문서 ID
            
        Returns:
            문서 내용 정보
        """
        try:
            # 문서 목록에서 해당 문서 찾기
            documents_result = self.list_documents()
            if documents_result.get("status") != "success":
                return {
                    "status": "error",
                    "message": "문서 목록 조회 실패"
                }
            
            documents = documents_result.get("documents", [])
            target_document = None
            
            for doc in documents:
                if doc.get("id") == document_id:
                    target_document = doc
                    break
            
            if not target_document:
                return {
                    "status": "error", 
                    "message": f"문서 '{document_id}'를 찾을 수 없습니다"
                }
            
            # Korean RAG 시스템은 원본 문서를 저장하지 않고 청크로만 저장
            # 원본 내용 복원은 현재 구현되지 않음
            title = target_document.get('title', '제목 없음')
            filename = target_document.get('filename', '알 수 없음')
            chunk_count = target_document.get('chunk_count', 0)
            created_at = target_document.get('created_at', '알 수 없음')
            
            reconstructed_content = f"""이 문서는 Korean RAG 시스템에서 처리되어 원본 내용을 직접 표시할 수 없습니다.

문서 정보:
- 제목: {title}
- 파일명: {filename}
- 생성 청크 수: {chunk_count}개
- 생성일: {created_at}

이 문서는 벡터 데이터베이스에 청크 단위로 저장되어 있어 
검색 시 관련 부분만 조회됩니다. 원본 내용을 확인하려면 
원본 파일을 참조해주세요."""
            
            return {
                "status": "success",
                "document": {
                    "id": target_document.get("id"),
                    "filename": target_document.get("filename", target_document.get("title", "알 수 없음")),
                    "title": target_document.get("title", target_document.get("filename", "제목 없음")),
                    "content": reconstructed_content,
                    "file_size": target_document.get("file_size"),
                    "created_at": target_document.get("created_at"),
                    "chunk_count": target_document.get("chunk_count"),
                    "processing_method": "korean_rag",
                    "metadata": target_document.get("metadata", {})
                }
            }
            
        except Exception as e:
            error_msg = str(e) if str(e) else "알 수 없는 오류가 발생했습니다"
            logger.error(f"문서 내용 조회 중 오류: {error_msg}")
            logger.error(f"예외 타입: {type(e)}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"문서 조회 중 오류가 발생했습니다: {error_msg}"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        RAG 시스템 상태 확인
        
        Returns:
            시스템 상태 정보
        """
        try:
            # 각 구성요소 상태 확인
            milvus_health = self.vector_storage.health_check()
            embedding_info = self.embedding_service.get_model_info()
            collection_stats = self.vector_storage.get_collection_stats()
            
            return {
                "status": "healthy" if milvus_health.get("status") == "healthy" else "unhealthy",
                "components": {
                    "vector_storage": milvus_health,
                    "embedding_service": embedding_info,
                    "collection_stats": collection_stats
                },
                "configuration": {
                    "max_context_chunks": self.max_context_chunks,
                    "similarity_threshold": self.similarity_threshold,
                    "max_context_length": self.max_context_length
                }
            }
            
        except Exception as e:
            logger.error(f"시스템 상태 확인 중 오류: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 전역 RAG 시스템 인스턴스
_rag_system = None

def get_korean_rag_system() -> KoreanRAGSystem:
    """한국어 RAG 시스템 인스턴스 반환"""
    global _rag_system
    if _rag_system is None:
        _rag_system = KoreanRAGSystem()
    return _rag_system


if __name__ == "__main__":
    # 테스트 코드
    rag_system = KoreanRAGSystem()
    
    # 시스템 상태 확인
    status = rag_system.get_system_status()
    print("=== RAG 시스템 상태 ===")
    print(f"상태: {status['status']}")
    
    # 테스트 문서 추가
    test_doc = """
    머신러닝과 딥러닝의 차이점에 대해 설명드리겠습니다.
    
    머신러닝은 컴퓨터가 명시적으로 프로그래밍되지 않고도 학습할 수 있게 하는 인공지능의 한 분야입니다.
    데이터를 통해 패턴을 찾고 예측이나 결정을 내릴 수 있습니다.
    
    딥러닝은 머신러닝의 하위 분야로, 인공 신경망을 사용하여 복잡한 패턴을 학습합니다.
    특히 이미지 인식, 음성 인식, 자연어 처리 등에서 뛰어난 성능을 보입니다.
    
    둘의 주요 차이점은 데이터 처리 방식과 복잡성에 있습니다.
    머신러닝은 특성 추출을 수동으로 해야 하지만, 딥러닝은 자동으로 특성을 학습합니다.
    """
    
    result = rag_system.add_document(
        title="머신러닝 vs 딥러닝",
        content=test_doc,
        metadata={"category": "AI/ML", "author": "test"}
    )
    print(f"\n=== 문서 추가 결과 ===")
    print(result)
    
    # 질의응답 테스트
    query = "머신러닝과 딥러닝의 차이점이 뭔가요?"
    rag_result = rag_system.search_and_answer(query)
    
    print(f"\n=== RAG 검색 결과 ===")
    print(f"질문: {rag_result['query']}")
    print(f"컨텍스트 발견: {rag_result['has_context']}")
    print(f"관련 청크 수: {rag_result['context_chunks_count']}")
    
    if rag_result['has_context']:
        print("\n=== LLM용 프롬프트 ===")
        print(rag_result['rag_prompt'][:500] + "..." if len(rag_result['rag_prompt']) > 500 else rag_result['rag_prompt'])
    
    # 문서 목록 확인
    doc_list = rag_system.list_documents()
    print(f"\n=== 문서 통계 ===")
    print(f"총 청크 수: {doc_list.get('total_chunks', 0)}")