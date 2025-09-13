"""
Docling Client Service - Document Processing Integration

이 모듈은 Docling 서비스와의 HTTP 클라이언트 통신을 담당합니다.
PDF, PPT, XLSX, DOC 등의 구조화된 문서를 텍스트로 변환합니다.
"""

import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional, Tuple
import tempfile
import logging

logger = logging.getLogger(__name__)

class DoclingClient:
    """Docling 서비스와의 HTTP 클라이언트"""
    
    def __init__(self):
        self.base_url = f"http://{os.getenv('DOCLING_HOST', 'localhost')}:{os.getenv('DOCLING_PORT', '5000')}"
        self.health_url = f"{self.base_url}/health"
        self.convert_url = f"{self.base_url}/convert"
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5분 타임아웃
        
    async def health_check(self) -> bool:
        """Docling 서비스 헬스 체크"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(self.health_url) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Docling health check failed: {e}")
            return False
    
    async def convert_document(self, file_content: bytes, filename: str) -> Tuple[bool, Dict[str, Any]]:
        """
        문서를 Docling 서비스를 통해 텍스트로 변환
        
        Args:
            file_content: 파일의 바이트 내용
            filename: 파일명 (확장자 포함)
            
        Returns:
            (성공여부, 결과데이터)
        """
        try:
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                
                # Docling 서비스에 요청
                data = aiohttp.FormData()
                data.add_field('file', 
                             open(temp_file.name, 'rb'),
                             filename=filename,
                             content_type='application/octet-stream')
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(self.convert_url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            # 임시 파일 삭제
                            os.unlink(temp_file.name)
                            
                            return True, {
                                'method': 'docling',
                                'content': result.get('markdown', ''),
                                'metadata': result.get('metadata', {}),
                                'status': 'success'
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"Docling conversion failed: {response.status} - {error_text}")
                            
                            # 임시 파일 삭제
                            os.unlink(temp_file.name)
                            
                            return False, {
                                'method': 'docling',
                                'error': f"HTTP {response.status}: {error_text}",
                                'status': 'failed'
                            }
                            
        except Exception as e:
            logger.error(f"Docling client error: {e}")
            return False, {
                'method': 'docling',
                'error': str(e),
                'status': 'failed'
            }
    
    def is_supported_format(self, filename: str) -> bool:
        """지원되는 파일 형식인지 확인"""
        supported_extensions = {'.pdf', '.ppt', '.pptx', '.xlsx', '.xls', '.doc', '.docx'}
        ext = os.path.splitext(filename.lower())[1]
        return ext in supported_extensions

# 전역 클라이언트 인스턴스
docling_client = DoclingClient()