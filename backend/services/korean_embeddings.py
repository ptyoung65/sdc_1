"""
Korean Embeddings Service
한국어 임베딩 서비스 - sentence-transformers를 활용한 한국어 특화 벡터화
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
import torch
from pathlib import Path
import pickle
import hashlib

logger = logging.getLogger(__name__)

class KoreanEmbeddingService:
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        """
        한국어 임베딩 서비스 초기화
        
        Args:
            model_name: 사용할 한국어 임베딩 모델
                - jhgan/ko-sroberta-multitask (추천)
                - sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens
                - distiluse-base-multilingual-cased
        """
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding_dim = None
        
        # 캐시 디렉토리 설정
        self.cache_dir = Path("./vector_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        self._load_model()
    
    def _load_model(self):
        """임베딩 모델 로드"""
        try:
            logger.info(f"한국어 임베딩 모델 로딩 중: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # 임베딩 차원 확인
            test_embedding = self.model.encode(["테스트"], convert_to_tensor=False)
            self.embedding_dim = len(test_embedding[0])
            
            logger.info(f"모델 로딩 완료 - 차원: {self.embedding_dim}, 디바이스: {self.device}")
            
        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}")
            # 폴백 모델 시도
            try:
                logger.info("폴백 모델로 전환: distiluse-base-multilingual-cased")
                self.model_name = "distiluse-base-multilingual-cased"
                self.model = SentenceTransformer(self.model_name, device=self.device)
                
                test_embedding = self.model.encode(["테스트"], convert_to_tensor=False)
                self.embedding_dim = len(test_embedding[0])
                
                logger.info(f"폴백 모델 로딩 완료 - 차원: {self.embedding_dim}")
                
            except Exception as e2:
                logger.error(f"폴백 모델도 로딩 실패: {e2}")
                raise RuntimeError("임베딩 모델을 로드할 수 없습니다.")
    
    def _get_cache_key(self, text: str) -> str:
        """캐시 키 생성"""
        return hashlib.md5(f"{self.model_name}:{text}".encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """캐시에서 임베딩 가져오기"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"캐시 로드 실패: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: np.ndarray):
        """임베딩을 캐시에 저장"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")
    
    def encode_single(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        단일 텍스트를 임베딩으로 변환
        
        Args:
            text: 임베딩할 텍스트
            use_cache: 캐시 사용 여부
            
        Returns:
            임베딩 벡터
        """
        if not text or not text.strip():
            return np.zeros(self.embedding_dim)
        
        # 캐시 확인
        if use_cache:
            cache_key = self._get_cache_key(text)
            cached_embedding = self._get_from_cache(cache_key)
            if cached_embedding is not None:
                return cached_embedding
        
        try:
            # 임베딩 생성
            embedding = self.model.encode([text], convert_to_tensor=False, normalize_embeddings=True)[0]
            
            # 캐시 저장
            if use_cache:
                self._save_to_cache(cache_key, embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return np.zeros(self.embedding_dim)
    
    def encode_batch(self, 
                    texts: List[str], 
                    batch_size: int = 32,
                    use_cache: bool = True) -> List[np.ndarray]:
        """
        배치 텍스트를 임베딩으로 변환
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            use_cache: 캐시 사용 여부
            
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []
        
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # 캐시된 임베딩 확인
        for i, text in enumerate(texts):
            if not text or not text.strip():
                embeddings.append(np.zeros(self.embedding_dim))
                continue
                
            if use_cache:
                cache_key = self._get_cache_key(text)
                cached_embedding = self._get_from_cache(cache_key)
                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                    continue
            
            # 캐시되지 않은 텍스트
            embeddings.append(None)  # 플레이스홀더
            uncached_texts.append(text)
            uncached_indices.append(i)
        
        # 캐시되지 않은 텍스트들을 배치로 처리
        if uncached_texts:
            try:
                logger.info(f"배치 임베딩 생성: {len(uncached_texts)}개 텍스트")
                
                batch_embeddings = []
                for i in range(0, len(uncached_texts), batch_size):
                    batch = uncached_texts[i:i+batch_size]
                    batch_result = self.model.encode(
                        batch, 
                        convert_to_tensor=False, 
                        normalize_embeddings=True
                    )
                    batch_embeddings.extend(batch_result)
                
                # 결과를 원래 위치에 배치하고 캐시에 저장
                for idx, embedding in zip(uncached_indices, batch_embeddings):
                    embeddings[idx] = embedding
                    
                    if use_cache:
                        cache_key = self._get_cache_key(uncached_texts[uncached_indices.index(idx)])
                        self._save_to_cache(cache_key, embedding)
                
            except Exception as e:
                logger.error(f"배치 임베딩 생성 실패: {e}")
                # 실패한 경우 영벡터로 채움
                for idx in uncached_indices:
                    if embeddings[idx] is None:
                        embeddings[idx] = np.zeros(self.embedding_dim)
        
        return embeddings
    
    def encode_documents(self, 
                        documents: List[Dict[str, Any]],
                        text_field: str = 'text') -> List[Dict[str, Any]]:
        """
        문서 리스트의 텍스트를 임베딩으로 변환
        
        Args:
            documents: 문서 리스트 (text_field를 포함해야 함)
            text_field: 텍스트가 들어있는 필드명
            
        Returns:
            임베딩이 추가된 문서 리스트
        """
        if not documents:
            return []
        
        texts = [doc.get(text_field, '') for doc in documents]
        embeddings = self.encode_batch(texts)
        
        # 문서에 임베딩 추가
        result_documents = []
        for doc, embedding in zip(documents, embeddings):
            enhanced_doc = doc.copy()
            enhanced_doc['embedding'] = embedding.tolist()  # JSON 직렬화를 위해 리스트로 변환
            enhanced_doc['embedding_model'] = self.model_name
            enhanced_doc['embedding_dim'] = self.embedding_dim
            result_documents.append(enhanced_doc)
        
        return result_documents
    
    def similarity(self, 
                   text1: str, 
                   text2: str,
                   method: str = 'cosine') -> float:
        """
        두 텍스트 간의 유사도 계산
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            method: 유사도 계산 방법 ('cosine', 'dot')
            
        Returns:
            유사도 점수
        """
        emb1 = self.encode_single(text1)
        emb2 = self.encode_single(text2)
        
        if method == 'cosine':
            return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        elif method == 'dot':
            return np.dot(emb1, emb2)
        else:
            raise ValueError(f"지원하지 않는 유사도 방법: {method}")
    
    def find_most_similar(self, 
                         query: str, 
                         candidates: List[str],
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """
        쿼리와 가장 유사한 후보들을 찾기
        
        Args:
            query: 검색 쿼리
            candidates: 후보 텍스트들
            top_k: 반환할 상위 k개
            
        Returns:
            유사도 정보가 포함된 결과 리스트
        """
        if not candidates:
            return []
        
        query_embedding = self.encode_single(query)
        candidate_embeddings = self.encode_batch(candidates)
        
        similarities = []
        for i, candidate_emb in enumerate(candidate_embeddings):
            similarity = np.dot(query_embedding, candidate_emb)
            similarities.append({
                'index': i,
                'text': candidates[i],
                'similarity': float(similarity)
            })
        
        # 유사도 기준으로 정렬
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:top_k]
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dim,
            'device': self.device,
            'cache_enabled': True,
            'cache_dir': str(self.cache_dir)
        }
    
    def clear_cache(self):
        """캐시 정리"""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            logger.info("임베딩 캐시 정리 완료")
        except Exception as e:
            logger.error(f"캐시 정리 실패: {e}")


# 전역 임베딩 서비스 인스턴스
_embedding_service = None

def get_korean_embedding_service() -> KoreanEmbeddingService:
    """한국어 임베딩 서비스 인스턴스 반환"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = KoreanEmbeddingService()
    return _embedding_service

def encode_korean_text(text: str) -> np.ndarray:
    """한국어 텍스트 임베딩 헬퍼 함수"""
    service = get_korean_embedding_service()
    return service.encode_single(text)

def encode_korean_texts(texts: List[str]) -> List[np.ndarray]:
    """한국어 텍스트 배치 임베딩 헬퍼 함수"""
    service = get_korean_embedding_service()
    return service.encode_batch(texts)


if __name__ == "__main__":
    # 테스트 코드
    service = KoreanEmbeddingService()
    
    test_texts = [
        "인공지능은 미래의 핵심 기술입니다.",
        "AI는 많은 산업을 변화시키고 있습니다.",
        "자연어 처리는 인공지능의 중요한 분야입니다.",
        "오늘 날씨가 정말 좋네요.",
        "맛있는 음식을 먹고 싶어요."
    ]
    
    # 배치 임베딩 테스트
    embeddings = service.encode_batch(test_texts)
    print(f"임베딩 생성 완료: {len(embeddings)}개")
    
    # 유사도 테스트
    query = "AI 기술에 대해 알려주세요"
    similar_results = service.find_most_similar(query, test_texts, top_k=3)
    
    print(f"\n쿼리: {query}")
    print("유사한 텍스트:")
    for result in similar_results:
        print(f"- {result['text']} (유사도: {result['similarity']:.3f})")
    
    # 모델 정보
    print(f"\n모델 정보: {service.get_model_info()}")