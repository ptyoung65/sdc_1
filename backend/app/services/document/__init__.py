"""
Document Processing Services

이 패키지는 다양한 문서 형식의 처리를 담당합니다:
- Docling 서비스를 통한 고급 문서 처리
- 로컬 Python 라이브러리를 통한 대안 처리
"""

from .docling_client import docling_client, DoclingClient
from .alternative_processor import alternative_processor, AlternativeProcessor

__all__ = ['docling_client', 'DoclingClient', 'alternative_processor', 'AlternativeProcessor']