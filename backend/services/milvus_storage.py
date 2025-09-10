"""
Milvus Vector Storage Service
Milvus 벡터 스토리지 서비스 - 한국어 문서 임베딩 저장 및 검색
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    Index
)
from korean_embeddings import get_korean_embedding_service
from korean_chunker import get_korean_chunker

logger = logging.getLogger(__name__)

class MilvusVectorStorage:
    def __init__(self, 
                 host: str = "localhost", 
                 port: str = "19530",
                 collection_name: str = "korean_documents"):
        """
        Milvus 벡터 스토리지 초기화
        
        Args:
            host: Milvus 서버 호스트
            port: Milvus 서버 포트
            collection_name: 컬렉션 이름
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        self.embedding_service = get_korean_embedding_service()
        self.chunker = get_korean_chunker()
        
        # 임베딩 차원
        self.embedding_dim = 768  # jhgan/ko-sroberta-multitask 기본 차원
        
        self._connect()
        self._ensure_collection()
    
    def _connect(self):
        """Milvus에 연결 (프로덕션 Milvus 서버)"""
        try:
            # 기존 연결이 있다면 해제
            try:
                connections.disconnect("default")
            except:
                pass
            
            # 프로덕션 Milvus 서버 연결
            connections.connect("default", host=self.host, port=self.port)
            logger.info(f"Milvus 연결 성공: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Milvus 연결 실패: {e}")
            # 연결 실패 시 예외 발생하지 않고 None으로 설정
            logger.warning("Milvus 연결 실패 - Graceful fallback 모드로 동작")
            self.collection = None
            raise RuntimeError(f"Milvus 서버에 연결할 수 없습니다: {e}")
    
    def _ensure_collection(self):
        """컬렉션 존재 확인 및 생성 (Graceful fallback 지원)"""
        try:
            # 연결 상태 확인
            if not connections.has_connection("default"):
                logger.warning("Milvus 연결이 없어 컬렉션 설정을 건너뜀")
                self.collection = None
                return
            
            # 기존 컬렉션이 있는지 확인
            if utility.has_collection(self.collection_name):
                logger.info(f"기존 컬렉션 로드: {self.collection_name}")
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info("기존 컬렉션 로드 완료")
            else:
                # 새 컬렉션 생성
                logger.info(f"새 컬렉션 생성: {self.collection_name}")
                self._create_collection()
                
                # 컬렉션 로드
                if self.collection:
                    self.collection.load()
                    logger.info("새 컬렉션 로드 완료")
            
        except Exception as e:
            logger.error(f"컬렉션 설정 중 오류: {e}")
            logger.warning("컬렉션 설정 실패 - Graceful fallback 모드로 동작")
            self.collection = None
    
    def _create_collection(self):
        """새 컬렉션 생성"""
        try:
            # 스키마 정의 - 극도로 보수적인 설정
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=50, is_primary=True),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="chunk_id", dtype=DataType.INT64),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=1000),  # 2000에서 1000으로 축소
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=30)
            ]
            
            schema = CollectionSchema(fields, "Korean document chunks collection")
            
            # 컬렉션 생성
            self.collection = Collection(self.collection_name, schema)
            logger.info(f"새 컬렉션 생성: {self.collection_name}")
            
            # 인덱스 생성
            self._create_index()
            
        except Exception as e:
            logger.error(f"컬렉션 생성 실패: {e}")
            raise
    
    def _create_index(self):
        """벡터 인덱스 생성"""
        try:
            # IVF_FLAT 인덱스 생성 (한국어 검색에 적합)
            index_params = {
                "metric_type": "COSINE",  # 코사인 유사도
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            logger.info("벡터 인덱스 생성 완료")
            
        except Exception as e:
            logger.warning(f"인덱스 생성 중 경고: {e}")
    
    def store_document(self, 
                      document_id: str,
                      text: str, 
                      metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        문서를 청킹하고 임베딩하여 Milvus에 저장
        
        Args:
            document_id: 문서 고유 ID
            text: 문서 텍스트
            metadata: 문서 메타데이터
            
        Returns:
            저장 결과 정보
        """
        try:
            # 문서 청킹
            chunks = self.chunker.chunk_document(text, metadata)
            if not chunks:
                return {"status": "error", "message": "청킹 실패"}
            
            # 청크 텍스트 추출
            chunk_texts = [chunk['text'] for chunk in chunks]
            
            # 배치 임베딩 생성
            embeddings = self.embedding_service.encode_batch(chunk_texts)
            
            # Milvus에 저장할 데이터 준비
            ids = []
            document_ids = []
            chunk_ids = []
            texts = []
            vector_embeddings = []
            metadatas = []
            created_ats = []
            
            current_time = datetime.now().isoformat()
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # UUID를 30자로 제한 (원래 36자인데 안전하게)
                chunk_uuid = str(uuid.uuid4())[:30]
                
                # 텍스트 길이를 강제로 400자로 제한 (극도로 보수적인 마진)
                safe_text = chunk['text'][:400]
                logger.warning(f"청크 {i} 텍스트를 400자로 강제 제한: 원본 {len(chunk['text'])}자 -> 제한 {len(safe_text)}자")
                
                # 추가 검증: 실제로 400자 이하인지 확인
                if len(safe_text) > 400:
                    logger.error(f"CRITICAL: 청크 {i} 텍스트가 여전히 400자 초과: {len(safe_text)}자")
                    safe_text = safe_text[:400]
                
                ids.append(chunk_uuid)
                # document_id도 40자로 제한 (안전하게)
                safe_document_id = str(document_id)[:40]
                document_ids.append(safe_document_id)
                chunk_ids.append(i)
                texts.append(safe_text)  # 안전한 텍스트 사용
                vector_embeddings.append(embedding.tolist())
                
                # 메타데이터 준비
                chunk_metadata = {
                    "original_metadata": metadata or {},
                    "chunk_info": {
                        "sentence_count": chunk.get("sentence_count", 0),
                        "length": chunk.get("length", 0),
                        "has_overlap": chunk.get("has_overlap", False)
                    },
                    "embedding_model": self.embedding_service.model_name
                }
                metadatas.append(chunk_metadata)
                # 타임스탬프도 25자로 제한 (안전하게)
                safe_timestamp = str(current_time)[:25]
                created_ats.append(safe_timestamp)
            
            # 삽입 전 최종 검증 로깅
            logger.warning(f"Milvus 삽입 전 최종 검증:")
            for i, text in enumerate(texts):
                text_len = len(text)
                if text_len > 400:
                    logger.error(f"CRITICAL ERROR: 텍스트 {i} 길이가 400자 초과: {text_len}자")
                else:
                    logger.info(f"텍스트 {i}: {text_len}자 (안전)")
            
            # 전체 엔티티 필드 검증
            logger.warning(f"전체 엔티티 길이 검증:")
            logger.info(f"IDs 개수: {len(ids)}, 샘플: {ids[0] if ids else 'None'}")
            logger.info(f"Document IDs 개수: {len(document_ids)}, 샘플: {document_ids[0] if document_ids else 'None'}")
            logger.info(f"Created ATs 개수: {len(created_ats)}, 샘플: {created_ats[0] if created_ats else 'None'}")
            
            # 모든 문자열 필드 길이 상세 검증 (15번째 청크에 집중)
            logger.warning(f"15번째 청크(인덱스 15) 상세 검증:")
            if len(ids) > 15:
                logger.error(f"ID[15]: '{ids[15]}' ({len(str(ids[15]))}자)")
                logger.error(f"Document_ID[15]: '{document_ids[15]}' ({len(str(document_ids[15]))}자)")
                logger.error(f"Text[15]: '{texts[15][:100]}...' ({len(texts[15])}자)")
                logger.error(f"Created_AT[15]: '{created_ats[15]}' ({len(str(created_ats[15]))}자)")
                
                # 메타데이터 JSON 길이 확인 - 가장 큰 문제 가능성
                metadata_str = str(metadatas[15]) if len(metadatas) > 15 else "N/A"
                logger.error(f"Metadata[15]: '{metadata_str[:200]}...' ({len(metadata_str)}자)")
                
                # JSON 직렬화 길이 확인
                import json
                json_str = json.dumps(metadatas[15], ensure_ascii=False) if len(metadatas) > 15 else ""
                logger.error(f"Metadata[15] 완전한 JSON 길이: {len(json_str)}자")
                logger.error(f"Metadata[15] 완전한 JSON: '{json_str}'")
                
                # 실제로 1660자가 어디에 있는지 다시 확인
                logger.error(f"실제 필드 길이 재확인:")
                logger.error(f"  - IDs[15] str 길이: {len(str(ids[15]))}자")
                logger.error(f"  - Document_IDs[15] str 길이: {len(str(document_ids[15]))}자") 
                logger.error(f"  - Texts[15] 길이: {len(texts[15])}자")
                logger.error(f"  - Created_ATs[15] str 길이: {len(str(created_ats[15]))}자")
                logger.error(f"  - Metadatas[15] JSON str 길이: {len(json_str)}자")
                
                # 임베딩도 확인해보자
                if len(vector_embeddings) > 15:
                    embedding_len = len(str(vector_embeddings[15])) if isinstance(vector_embeddings[15], list) else "N/A"
                    logger.error(f"  - Vector_Embeddings[15] str 길이: {embedding_len}자")
            
            # IDs 검증
            for i, id_val in enumerate(ids):
                if len(str(id_val)) > 50:
                    logger.error(f"CRITICAL ERROR: ID {i} 길이가 50자 초과: {len(str(id_val))}자 - '{str(id_val)[:50]}...'")
                    
            # Document IDs 검증
            for i, doc_id in enumerate(document_ids):
                if len(str(doc_id)) > 50:
                    logger.error(f"CRITICAL ERROR: Document_ID {i} 길이가 50자 초과: {len(str(doc_id))}자 - '{str(doc_id)[:50]}...'")
            
            # Created_At 검증
            for i, created_at in enumerate(created_ats):
                if len(str(created_at)) > 30:
                    logger.error(f"CRITICAL ERROR: Created_AT {i} 길이가 30자 초과: {len(str(created_at))}자 - '{str(created_at)[:30]}...'")
            
            # Milvus에 삽입
            entities = [
                ids,
                document_ids,
                chunk_ids,
                texts,
                vector_embeddings,
                metadatas,
                created_ats
            ]
            
            insert_result = self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"문서 저장 완료: {document_id}, {len(chunks)}개 청크")
            
            return {
                "status": "success",
                "document_id": document_id,
                "chunks_stored": len(chunks),
                "ids": insert_result.primary_keys
            }
            
        except Exception as e:
            logger.error(f"문서 저장 중 오류: {e}")
            return {"status": "error", "message": str(e)}
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5,
                      score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        쿼리와 유사한 문서 청크 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            score_threshold: 최소 유사도 임계값
            
        Returns:
            유사한 청크 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_service.encode_single(query)
            
            # 벡터 검색
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["document_id", "chunk_id", "text", "metadata", "created_at"]
            )
            
            # 결과 처리
            similar_chunks = []
            for hits in results:
                for hit in hits:
                    # 유사도 임계값 확인
                    if hit.score >= score_threshold:
                        chunk_info = {
                            "id": hit.id,
                            "document_id": hit.entity.get("document_id"),
                            "chunk_id": hit.entity.get("chunk_id"),
                            "text": hit.entity.get("text"),
                            "similarity_score": float(hit.score),
                            "metadata": hit.entity.get("metadata"),
                            "created_at": hit.entity.get("created_at")
                        }
                        similar_chunks.append(chunk_info)
            
            logger.info(f"검색 완료: {len(similar_chunks)}개 결과")
            return similar_chunks
            
        except Exception as e:
            logger.error(f"검색 중 오류: {e}")
            return []
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """특정 문서의 모든 청크 조회"""
        try:
            expr = f'document_id == "{document_id}"'
            results = self.collection.query(
                expr=expr,
                output_fields=["id", "chunk_id", "text", "metadata", "created_at"]
            )
            
            # chunk_id로 정렬
            results.sort(key=lambda x: x.get("chunk_id", 0))
            
            return results
            
        except Exception as e:
            logger.error(f"문서 청크 조회 중 오류: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """문서와 관련된 모든 청크 삭제"""
        try:
            expr = f'document_id == "{document_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"문서 삭제 완료: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"문서 삭제 중 오류: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보"""
        try:
            stats = self.collection.num_entities
            
            return {
                "collection_name": self.collection_name,
                "total_chunks": stats,
                "embedding_dimension": self.embedding_dim,
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE"
            }
            
        except Exception as e:
            logger.error(f"통계 조회 중 오류: {e}")
            return {}
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        저장된 모든 문서의 메타데이터를 반환
        
        Returns:
            문서 목록 (document_id별로 그룹핑)
        """
        try:
            self.collection.load()
            
            # 모든 청크의 메타데이터 조회
            results = self.collection.query(
                expr="chunk_id >= 0",
                output_fields=["document_id", "metadata", "chunk_id", "created_at"],
                limit=1000  # 최대 1000개 청크
            )
            
            if not results:
                logger.info("저장된 문서가 없습니다")
                return []
            
            # document_id별로 그룹핑하여 문서 목록 생성
            documents_dict = {}
            for record in results:
                doc_id = record.get("document_id", "unknown")
                if doc_id not in documents_dict:
                    metadata = record.get("metadata", {})
                    documents_dict[doc_id] = {
                        "document_id": doc_id,
                        "title": metadata.get("title", "제목 없음"),
                        "type": metadata.get("type", "document"),
                        "created_at": metadata.get("created_at", record.get("created_at", "unknown")),
                        "chunk_count": 0,
                        "metadata": metadata
                    }
                documents_dict[doc_id]["chunk_count"] += 1
            
            # 리스트로 변환하고 created_at으로 정렬 (최신순)
            documents_list = list(documents_dict.values())
            documents_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            logger.info(f"문서 목록 조회 완료: {len(documents_list)}개 문서, {len(results)}개 청크")
            return documents_list
            
        except Exception as e:
            logger.error(f"문서 목록 조회 중 오류: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        try:
            # 연결 상태 확인
            is_connected = connections.has_connection("default")
            
            # 컬렉션 상태 확인
            collection_exists = utility.has_collection(self.collection_name)
            
            return {
                "status": "healthy" if is_connected and collection_exists else "unhealthy",
                "milvus_connected": is_connected,
                "collection_exists": collection_exists,
                "embedding_service": self.embedding_service.get_model_info()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 전역 Milvus 스토리지 인스턴스
_milvus_storage = None

def get_milvus_storage() -> MilvusVectorStorage:
    """Milvus 스토리지 인스턴스 반환"""
    global _milvus_storage
    if _milvus_storage is None:
        _milvus_storage = MilvusVectorStorage()
    return _milvus_storage


if __name__ == "__main__":
    # 테스트 코드
    storage = MilvusVectorStorage()
    
    # 상태 확인
    health = storage.health_check()
    print("Milvus 상태:", health)
    
    # 테스트 문서 저장
    test_doc = """
    인공지능 기술이 급속도로 발전하면서 다양한 산업 분야에서 혁신을 이끌고 있습니다.
    특히 자연어 처리 분야에서는 GPT, BERT와 같은 대형 언어 모델이 등장했습니다.
    한국어 자연어 처리는 언어의 특성상 더욱 정교한 기술이 필요합니다.
    형태소 분석, 구문 분석, 의미 분석 등 다양한 단계를 거쳐 처리됩니다.
    """
    
    result = storage.store_document(
        document_id="test_doc_001",
        text=test_doc,
        metadata={"source": "test", "category": "AI"}
    )
    print("저장 결과:", result)
    
    # 유사도 검색 테스트
    query = "인공지능과 자연어 처리에 대해 알려주세요"
    similar_results = storage.search_similar(query, top_k=3)
    
    print(f"\n검색 쿼리: {query}")
    for result in similar_results:
        print(f"- 유사도: {result['similarity_score']:.3f}")
        print(f"  텍스트: {result['text'][:100]}...")
    
    # 통계 정보
    stats = storage.get_collection_stats()
    print(f"\n컬렉션 통계: {stats}")