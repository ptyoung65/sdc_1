"""
Korean Document Chunking Service
한국어 문서 청킹 서비스 - 문장 단위로 지능적으로 문서를 분할
"""

import re
import logging
from typing import List, Dict, Any
from kiwipiepy import Kiwi
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class KoreanDocumentChunker:
    def __init__(self, 
                 chunk_size: int = 400, 
                 chunk_overlap: int = 50,
                 max_chunk_size: int = 1500):
        """
        한국어 문서 청킹기 초기화
        
        Args:
            chunk_size: 기본 청크 크기 (문자 단위)
            chunk_overlap: 청크 간 겹치는 부분 크기
            max_chunk_size: 최대 청크 크기
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size
        
        # Kiwi 형태소 분석기 초기화
        try:
            self.kiwi = Kiwi()
            logger.info("Kiwi 형태소 분석기 초기화 완료")
        except Exception as e:
            logger.warning(f"Kiwi 초기화 실패: {e}, 기본 청킹 사용")
            self.kiwi = None
        
        # LangChain 텍스트 스플리터 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 특수 문자 정리 (필요시)
        text = re.sub(r'[^\w\s\.\!\?\,\:\;\-\(\)]', '', text)
        
        return text
    
    def split_by_sentences(self, text: str) -> List[str]:
        """한국어 문장 단위로 분할"""
        # 문장 종결 문자로 분할
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # 빈 문장 제거
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def create_semantic_chunks(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """의미 단위 청크 생성"""
        chunks = []
        current_chunk = ""
        current_sentences = []
        
        for i, sentence in enumerate(sentences):
            # 현재 청크에 문장을 추가했을 때의 길이 확인
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= self.chunk_size:
                # 청크 크기 내에서 추가 가능
                current_chunk = potential_chunk
                current_sentences.append(sentence)
            else:
                # 현재 청크를 저장하고 새 청크 시작
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'sentences': current_sentences.copy(),
                        'length': len(current_chunk),
                        'sentence_count': len(current_sentences)
                    })
                
                # 새 청크 시작
                current_chunk = sentence
                current_sentences = [sentence]
                
                # 단일 문장이 최대 크기를 초과하는 경우 강제 분할
                if len(sentence) > self.max_chunk_size:
                    sub_chunks = self._force_split_long_sentence(sentence)
                    for sub_chunk in sub_chunks:
                        chunks.append({
                            'text': sub_chunk,
                            'sentences': [sub_chunk],
                            'length': len(sub_chunk),
                            'sentence_count': 1
                        })
                    current_chunk = ""
                    current_sentences = []
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'sentences': current_sentences,
                'length': len(current_chunk),
                'sentence_count': len(current_sentences)
            })
        
        return chunks
    
    def _force_split_long_sentence(self, sentence: str) -> List[str]:
        """긴 문장을 강제로 분할"""
        chunks = []
        words = sentence.split()
        current_chunk = ""
        
        for word in words:
            if len(current_chunk + " " + word) <= self.max_chunk_size:
                current_chunk += " " + word if current_chunk else word
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _force_split_by_char_limit(self, text: str, max_chars: int = 1900) -> List[str]:
        """
        텍스트를 문자 수 제한에 맞춰 강제 분할
        
        Args:
            text: 분할할 텍스트
            max_chars: 최대 문자 수 제한
            
        Returns:
            분할된 텍스트 리스트
        """
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = ""
        
        for word in words:
            # 현재 청크에 단어를 추가했을 때 길이 확인
            potential_chunk = current_chunk + " " + word if current_chunk else word
            
            if len(potential_chunk) <= max_chars:
                current_chunk = potential_chunk
            else:
                # 현재 청크를 저장하고 새 청크 시작
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = word
                else:
                    # 단일 단어가 제한을 초과하는 경우 문자 단위로 분할
                    if len(word) > max_chars:
                        for i in range(0, len(word), max_chars):
                            chunks.append(word[i:i+max_chars])
                    else:
                        current_chunk = word
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def add_overlap(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """청크 간 오버랩 추가"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            overlap_text = ""
            
            # 이전 청크에서 오버랩 텍스트 가져오기
            if i > 0:
                prev_chunk = chunks[i-1]
                prev_words = prev_chunk['text'].split()
                overlap_words = prev_words[-min(self.chunk_overlap//10, len(prev_words)):]
                overlap_text = " ".join(overlap_words)
            
            # 오버랩이 있는 경우 현재 청크 앞에 추가 (2000자 제한 고려)
            if overlap_text:
                potential_text = overlap_text + " " + chunk['text']
                # 더 보수적인 제한: 1200자로 제한
                if len(potential_text) <= 1200:  # 매우 보수적인 마진 800자
                    chunk['text'] = potential_text
                    chunk['length'] = len(chunk['text'])
                    chunk['has_overlap'] = True
                    chunk['overlap_text'] = overlap_text
                else:
                    # 오버랩 추가 시 1200자 초과하면 오버랩 생략
                    chunk['has_overlap'] = False
                    logger.warning(f"오버랩 추가 시 1200자 초과로 생략: {len(potential_text)}자")
            else:
                chunk['has_overlap'] = False
            
            overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    def chunk_document(self, 
                      text: str, 
                      metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        문서를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            metadata: 문서 메타데이터
            
        Returns:
            청크 리스트
        """
        try:
            # 텍스트 전처리
            cleaned_text = self.preprocess_text(text)
            
            if not cleaned_text:
                return []
            
            # 문장 단위로 분할
            sentences = self.split_by_sentences(cleaned_text)
            
            if not sentences:
                return []
            
            # 의미 단위 청크 생성
            chunks = self.create_semantic_chunks(sentences)
            
            # 오버랩 추가
            chunks = self.add_overlap(chunks)
            
            # Milvus 문자열 길이 제한 검증 (1400자로 매우 보수적으로 설정)
            validated_chunks = []
            for chunk in chunks:
                if len(chunk['text']) > 1400:  # 매우 보수적인 마진 600자
                    # 1400자 초과 시 강제 분할
                    logger.warning(f"청크가 1400자를 초과하여 강제 분할: {len(chunk['text'])}자")
                    sub_chunks = self._force_split_by_char_limit(chunk['text'], 1300)  # 여유분 200자
                    for j, sub_text in enumerate(sub_chunks):
                        validated_chunks.append({
                            'text': sub_text,
                            'sentences': [sub_text],  # 강제 분할된 청크는 단일 텍스트로 처리
                            'length': len(sub_text),
                            'sentence_count': sub_text.count('.') + sub_text.count('!') + sub_text.count('?'),
                            'chunk_id': f"{len(validated_chunks)}_{j}",
                            'metadata': chunk.get('metadata', {}),
                            'force_split': True,
                            'created_at': None
                        })
                else:
                    validated_chunks.append(chunk)
            
            # 메타데이터 추가 및 ID 재정리
            for i, chunk in enumerate(validated_chunks):
                chunk.update({
                    'chunk_id': i,
                    'total_chunks': len(validated_chunks),
                    'metadata': metadata or {},
                    'created_at': None  # 실제 사용 시 timestamp 추가
                })
            
            logger.info(f"문서 청킹 완료: {len(validated_chunks)}개 청크 생성")
            return validated_chunks
            
        except Exception as e:
            logger.error(f"문서 청킹 중 오류: {e}")
            # 폴백: LangChain 텍스트 스플리터 사용
            return self._fallback_chunking(text, metadata)
    
    def _fallback_chunking(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """폴백 청킹 (LangChain 사용)"""
        try:
            chunks = self.text_splitter.split_text(text)
            
            result = []
            for i, chunk in enumerate(chunks):
                result.append({
                    'text': chunk,
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'length': len(chunk),
                    'sentence_count': len(chunk.split('.')),
                    'metadata': metadata or {},
                    'fallback': True
                })
            
            return result
            
        except Exception as e:
            logger.error(f"폴백 청킹도 실패: {e}")
            return []

# 전역 청킹 인스턴스
_chunker_instance = None

def get_korean_chunker() -> KoreanDocumentChunker:
    """한국어 청킹기 인스턴스 반환"""
    global _chunker_instance
    # 항상 새로운 인스턴스 생성 (싱글톤 비활성화)
    # 매우 보수적인 설정으로 생성
    _chunker_instance = KoreanDocumentChunker(
        chunk_size=300,  # 더 작은 청크
        chunk_overlap=30,  # 더 작은 오버랩
        max_chunk_size=1200  # 더 작은 최대 크기
    )
    return _chunker_instance


def chunk_korean_document(text: str, 
                         metadata: Dict[str, Any] = None,
                         chunk_size: int = 400,
                         chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """
    한국어 문서 청킹 헬퍼 함수
    
    Args:
        text: 청킹할 텍스트
        metadata: 문서 메타데이터
        chunk_size: 청크 크기
        chunk_overlap: 오버랩 크기
        
    Returns:
        청크 리스트
    """
    chunker = KoreanDocumentChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return chunker.chunk_document(text, metadata)


if __name__ == "__main__":
    # 테스트 코드
    test_text = """
    인공지능은 현대 사회의 혁신적인 기술 중 하나입니다. 
    머신러닝과 딥러닝 기술의 발전으로 인해 다양한 분야에서 활용되고 있습니다.
    특히 자연어 처리 분야에서는 GPT, BERT 같은 대형 언어 모델들이 등장했습니다.
    이러한 모델들은 텍스트 생성, 번역, 요약 등의 작업에서 뛰어난 성능을 보입니다.
    
    한국어 자연어 처리는 영어와 다른 특성을 가지고 있습니다.
    교착어적 특성과 복잡한 어미 변화 때문에 더욱 정교한 처리가 필요합니다.
    형태소 분석, 구문 분석, 의미 분석 등의 단계를 거쳐 처리됩니다.
    """
    
    chunker = KoreanDocumentChunker()
    chunks = chunker.chunk_document(test_text, {"source": "test_document"})
    
    for i, chunk in enumerate(chunks):
        print(f"\n청크 {i+1}:")
        print(f"텍스트: {chunk['text'][:100]}...")
        print(f"길이: {chunk['length']} 문자")
        print(f"문장 수: {chunk['sentence_count']}개")