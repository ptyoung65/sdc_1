"""
Korean Embeddings Service with Docling Integration
한국어 임베딩 서비스 - Docling과 TF-IDF를 활용한 한국어 특화 벡터화
PyTorch/Transformers 의존성 없이 구현
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import pickle
import hashlib
import json
import re
from collections import Counter
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from datetime import datetime
import os

# Korean text processing (using kiwipiepy if available)
try:
    from kiwipiepy import Kiwi
    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False
    logging.warning("Kiwi not available, using basic tokenization")

logger = logging.getLogger(__name__)

class KoreanTextProcessor:
    """한국어 텍스트 전처리 및 청킹 클래스"""
    
    def __init__(self):
        self.kiwi = None
        if KIWI_AVAILABLE:
            try:
                self.kiwi = Kiwi()
                logger.info("✅ Kiwi 한국어 처리기 초기화 완료")
            except Exception as e:
                logger.warning(f"⚠️ Kiwi 초기화 실패: {e}")
                
    def preprocess_text(self, text: str) -> str:
        """한국어 텍스트 전처리"""
        # 기본적인 정리
        text = text.strip()
        
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 한글, 영문, 숫자, 기본 문장부호만 유지
        text = re.sub(r'[^\w\s.!?가-힣]', ' ', text)
        
        return text.strip()
    
    def extract_keywords(self, text: str) -> List[str]:
        """한국어 텍스트에서 키워드 추출"""
        tokens = self.tokenize(text)
        
        # 길이가 2자 이상인 토큰만 키워드로 간주
        keywords = [token for token in tokens if len(token) >= 2]
        
        # 빈도 기반으로 상위 키워드 선택
        from collections import Counter
        counter = Counter(keywords)
        return [word for word, count in counter.most_common(10)]
    
    def tokenize(self, text: str) -> List[str]:
        """한국어 텍스트 토큰화"""
        if self.kiwi:
            try:
                # Kiwi를 사용한 형태소 분석
                result = self.kiwi.tokenize(text)
                tokens = []
                for token in result:
                    # 명사, 동사, 형용사만 추출 (의미있는 토큰)
                    if token.tag in ['NNG', 'NNP', 'VV', 'VA', 'SL']:
                        tokens.append(token.form)
                return tokens
            except Exception as e:
                logger.warning(f"Kiwi tokenization failed: {e}")
                
        # Fallback: 공백 기반 분리 + 한글 추출
        tokens = []
        words = text.split()
        for word in words:
            # 한글만 추출
            korean_chars = re.findall(r'[가-힣]+', word)
            tokens.extend(korean_chars)
        return tokens
    
    def chunk_text(self, 
                   text: str, 
                   chunk_size: int = 500,
                   overlap: int = 50) -> List[str]:
        """
        한국어 텍스트를 의미 단위로 청킹
        
        Args:
            text: 청킹할 텍스트
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 간 중복 크기
            
        Returns:
            청크 리스트
        """
        chunks = []
        
        # 문장 단위로 분리 (한국어 문장 부호 고려)
        sentences = re.split(r'[.!?。！？]\s*', text)
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 현재 청크에 문장 추가 가능한지 확인
            if len(current_chunk) + len(sentence) <= chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(current_chunk)
                    chunk_index += 1
                
                # 새 청크 시작 (오버랩 포함)
                if overlap > 0 and current_chunk:
                    # 이전 청크의 마지막 부분 포함
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
        
        # 마지막 청크 저장
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

class DoclingClient:
    """Docling 서비스와 통신하는 클라이언트"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.getenv("DOCLING_HOST", "localhost")
        self.port = port or int(os.getenv("DOCLING_PORT", "8501"))
        self.base_url = f"http://{self.host}:{self.port}"
        
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Docling을 사용하여 문서 처리
        
        Args:
            file_path: 처리할 문서 경로
            
        Returns:
            처리된 문서 데이터
        """
        try:
            # Docling API 호출 (실제 API에 맞게 수정 필요)
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/process",
                    files=files,
                    timeout=30
                )
                
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Docling processing failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Docling service unavailable: {e}")
            return None
        except Exception as e:
            logger.error(f"Docling processing error: {e}")
            return None

class KoreanEmbeddingService:
    """
    한국어 임베딩 서비스 - TF-IDF 기반 벡터화
    PyTorch/Transformers 없이 scikit-learn 사용
    """
    
    def __init__(self, embedding_dim: int = 768):
        """
        한국어 임베딩 서비스 초기화
        
        Args:
            embedding_dim: 임베딩 차원 (TF-IDF 특징 수)
        """
        self.embedding_dim = embedding_dim
        self.text_processor = KoreanTextProcessor()
        self.docling_client = DoclingClient()
        
        # TF-IDF 벡터라이저 (단일 문서 처리 가능하도록 설정)
        self.vectorizer = TfidfVectorizer(
            max_features=embedding_dim,
            tokenizer=self.text_processor.tokenize,
            token_pattern=None,  # Custom tokenizer 사용
            ngram_range=(1, 2),  # Unigram + Bigram
            min_df=1,
            max_df=1.0,  # 단일 문서에서도 작동하도록 1.0으로 설정
            sublinear_tf=True,  # log(tf) 사용
            use_idf=True
        )
        
        # 문서 코퍼스 (TF-IDF 학습용)
        self.corpus = []
        self.is_fitted = False
        
        # 캐시 디렉토리
        self.cache_dir = Path("./vector_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # 한국어 특화 가중치
        self.korean_weights = self._initialize_korean_weights()
        
        logger.info(f"✅ 한국어 임베딩 서비스 초기화 (차원: {embedding_dim})")
    
    def _initialize_korean_weights(self) -> Dict[str, float]:
        """한국어 특화 단어 가중치 초기화"""
        # 중요 한국어 키워드에 가중치 부여
        return {
            # 기술 용어
            "인공지능": 2.0, "머신러닝": 2.0, "딥러닝": 2.0,
            "데이터": 1.5, "분석": 1.5, "모델": 1.5,
            "알고리즘": 1.8, "학습": 1.5, "예측": 1.5,
            
            # 비즈니스 용어
            "경영": 1.5, "전략": 1.5, "시장": 1.5,
            "고객": 1.8, "서비스": 1.5, "품질": 1.5,
            
            # 일반 중요 단어
            "중요": 1.3, "필수": 1.3, "핵심": 1.5,
            "주요": 1.3, "기본": 1.2, "필요": 1.2
        }
    
    def _get_cache_key(self, text: str) -> str:
        """캐시 키 생성"""
        return hashlib.md5(f"tfidf:{text}".encode()).hexdigest()
    
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
    
    def _apply_korean_weights(self, text: str, vector: np.ndarray) -> np.ndarray:
        """한국어 가중치 적용"""
        # 텍스트에서 가중치 단어 찾기
        weight_multiplier = 1.0
        for keyword, weight in self.korean_weights.items():
            if keyword in text:
                weight_multiplier = max(weight_multiplier, weight)
        
        # 벡터에 가중치 적용
        weighted_vector = vector * weight_multiplier
        
        # 정규화
        norm = np.linalg.norm(weighted_vector)
        if norm > 0:
            weighted_vector = weighted_vector / norm
            
        return weighted_vector
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        텍스트를 TF-IDF 벡터로 변환
        
        Args:
            text: 벡터화할 텍스트
            
        Returns:
            TF-IDF 벡터 (numpy array)
        """
        if not text.strip():
            return np.zeros(self.embedding_dim)
        
        # 캐시 확인
        cache_key = self._get_cache_key(text)
        cached_embedding = self._get_from_cache(cache_key)
        if cached_embedding is not None:
            return cached_embedding
        
        # 텍스트 전처리
        processed_text = self.text_processor.preprocess_text(text)
        
        # TF-IDF 벡터화
        try:
            # 벡터라이저가 아직 fit되지 않았으면 이 텍스트로 fit
            if not hasattr(self.vectorizer, 'vocabulary_') or self.vectorizer.vocabulary_ is None:
                self.vectorizer.fit([processed_text])
            
            # 벡터 변환
            vector = self.vectorizer.transform([processed_text])
            vector_array = vector.toarray()[0]
            
            # 차원 조정
            if len(vector_array) < self.embedding_dim:
                # 부족한 차원은 0으로 패딩
                padded_vector = np.zeros(self.embedding_dim)
                padded_vector[:len(vector_array)] = vector_array
                vector_array = padded_vector
            elif len(vector_array) > self.embedding_dim:
                # 초과 차원은 잘라내기
                vector_array = vector_array[:self.embedding_dim]
            
            # 한국어 가중치 적용
            weighted_vector = self._apply_korean_weights(text, vector_array)
            
            # 캐시에 저장
            self._save_to_cache(cache_key, weighted_vector)
            
            return weighted_vector
            
        except Exception as e:
            logger.error(f"TF-IDF 벡터화 실패: {e}")
            # 실패 시 랜덤 벡터 반환
            return np.random.rand(self.embedding_dim) * 0.1
    
    def fit_corpus(self, texts: List[str]):
        """
        코퍼스로 TF-IDF 모델 학습
        
        Args:
            texts: 학습할 텍스트 리스트
        """
        if not texts:
            return
            
        logger.info(f"📚 TF-IDF 모델 학습 중 ({len(texts)}개 문서)...")
        
        # 코퍼스 업데이트
        self.corpus.extend(texts)
        
        # TF-IDF 학습
        try:
            self.vectorizer.fit(self.corpus)
            self.is_fitted = True
            logger.info("✅ TF-IDF 모델 학습 완료")
        except Exception as e:
            logger.error(f"TF-IDF 학습 실패: {e}")
    
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
            # TF-IDF 벡터 생성
            if not self.is_fitted:
                # 모델이 학습되지 않은 경우, 단일 문서로 임시 학습
                self.fit_corpus([text])
            
            # TF-IDF 변환
            tfidf_vector = self.vectorizer.transform([text]).toarray()[0]
            
            # 차원 조정 (필요한 경우)
            if len(tfidf_vector) < self.embedding_dim:
                # 패딩
                embedding = np.pad(tfidf_vector, 
                                 (0, self.embedding_dim - len(tfidf_vector)), 
                                 mode='constant')
            else:
                embedding = tfidf_vector[:self.embedding_dim]
            
            # 한국어 가중치 적용
            embedding = self._apply_korean_weights(text, embedding)
            
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
        
        for text in texts:
            embedding = self.encode_single(text, use_cache=use_cache)
            embeddings.append(embedding)
        
        return embeddings
    
    def process_document_with_docling(self, 
                                     file_path: str,
                                     chunk_size: int = 500) -> List[Dict[str, Any]]:
        """
        Docling을 사용하여 문서 처리 및 청킹
        
        Args:
            file_path: 문서 파일 경로
            chunk_size: 청크 크기
            
        Returns:
            처리된 청크 리스트
        """
        chunks = []
        
        # Docling으로 문서 처리 시도
        docling_result = self.docling_client.process_document(file_path)
        
        if docling_result and 'text' in docling_result:
            # Docling 성공
            text = docling_result['text']
            metadata = docling_result.get('metadata', {})
            
            # 텍스트 청킹
            text_chunks = self.text_processor.chunk_text(text, chunk_size=chunk_size)
            
            for chunk in text_chunks:
                # 각 청크에 대한 임베딩 생성
                embedding = self.encode_single(chunk['text'])
                
                chunks.append({
                    'text': chunk['text'],
                    'embedding': embedding.tolist(),
                    'metadata': {
                        **metadata,
                        'chunk_index': chunk['index'],
                        'start_char': chunk['start_char'],
                        'processing_method': 'docling'
                    }
                })
        else:
            # Docling 실패 시 기본 텍스트 처리
            logger.info("Docling 처리 실패, 기본 텍스트 처리 사용")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # 텍스트 청킹
                text_chunks = self.text_processor.chunk_text(text, chunk_size=chunk_size)
                
                for chunk in text_chunks:
                    embedding = self.encode_single(chunk['text'])
                    
                    chunks.append({
                        'text': chunk['text'],
                        'embedding': embedding.tolist(),
                        'metadata': {
                            'file_path': str(file_path),
                            'chunk_index': chunk['index'],
                            'start_char': chunk['start_char'],
                            'processing_method': 'basic'
                        }
                    })
            except Exception as e:
                logger.error(f"문서 처리 실패: {e}")
        
        return chunks
    
    def similarity(self, 
                   text1: str, 
                   text2: str,
                   method: str = 'cosine') -> float:
        """
        두 텍스트 간의 유사도 계산
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            method: 유사도 계산 방법
            
        Returns:
            유사도 점수
        """
        emb1 = self.encode_single(text1)
        emb2 = self.encode_single(text2)
        
        if method == 'cosine':
            # Reshape for sklearn
            emb1_2d = emb1.reshape(1, -1)
            emb2_2d = emb2.reshape(1, -1)
            return cosine_similarity(emb1_2d, emb2_2d)[0][0]
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
        
        # 유사도 계산
        query_2d = query_embedding.reshape(1, -1)
        candidates_2d = np.array(candidate_embeddings)
        
        similarities = cosine_similarity(query_2d, candidates_2d)[0]
        
        # 결과 정렬
        results = []
        for i, similarity in enumerate(similarities):
            results.append({
                'index': i,
                'text': candidates[i],
                'similarity': float(similarity)
            })
        
        # 유사도 기준 정렬
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            'model_type': 'TF-IDF',
            'embedding_dimension': self.embedding_dim,
            'korean_processor': 'Kiwi' if KIWI_AVAILABLE else 'Basic',
            'docling_available': True,
            'cache_enabled': True,
            'cache_dir': str(self.cache_dir),
            'corpus_size': len(self.corpus),
            'is_fitted': self.is_fitted
        }
    
    def clear_cache(self):
        """캐시 정리"""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            logger.info("✅ 임베딩 캐시 정리 완료")
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

def process_korean_document(file_path: str) -> List[Dict[str, Any]]:
    """한국어 문서 처리 헬퍼 함수"""
    service = get_korean_embedding_service()
    return service.process_document_with_docling(file_path)


if __name__ == "__main__":
    # 테스트 코드
    service = KoreanEmbeddingService()
    
    # 샘플 코퍼스로 학습
    sample_corpus = [
        "인공지능은 미래의 핵심 기술입니다.",
        "머신러닝과 딥러닝은 AI의 중요한 분야입니다.",
        "한국어 자연어 처리는 도전적인 과제입니다.",
        "데이터 분석을 통해 인사이트를 얻을 수 있습니다.",
        "고객 서비스 품질 향상이 중요합니다."
    ]
    
    service.fit_corpus(sample_corpus)
    
    test_texts = [
        "인공지능은 미래의 핵심 기술입니다.",
        "AI는 많은 산업을 변화시키고 있습니다.",
        "자연어 처리는 인공지능의 중요한 분야입니다.",
        "오늘 날씨가 정말 좋네요.",
        "맛있는 음식을 먹고 싶어요."
    ]
    
    # 배치 임베딩 테스트
    embeddings = service.encode_batch(test_texts)
    print(f"✅ 임베딩 생성 완료: {len(embeddings)}개")
    print(f"   임베딩 차원: {len(embeddings[0])}")
    
    # 유사도 테스트
    query = "AI 기술에 대해 알려주세요"
    similar_results = service.find_most_similar(query, test_texts, top_k=3)
    
    print(f"\n🔍 쿼리: {query}")
    print("📊 유사한 텍스트:")
    for result in similar_results:
        print(f"   - {result['text']} (유사도: {result['similarity']:.3f})")
    
    # 모델 정보
    print(f"\n📌 모델 정보: {service.get_model_info()}")