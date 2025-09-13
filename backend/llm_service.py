import os
import google.generativeai as genai
from typing import List, Dict, Optional
from enum import Enum
import json

# OpenAI는 선택사항
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

class LLMProvider(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"

class LLMService:
    def __init__(self):
        # Gemini 설정
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            # gemini-1.5-flash는 더 빠르고 무료 할당량이 더 많음
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # OpenAI 설정 (옵션)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        if self.openai_api_key and HAS_OPENAI:
            openai.api_key = self.openai_api_key
        
        # 기본 제공자는 Gemini
        self.default_provider = LLMProvider.GEMINI if self.gemini_api_key else None
    
    async def generate_response(
        self, 
        message: str, 
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        일반 LLM 응답 생성
        """
        return await self._generate_llm_response(
            message, provider, system_prompt, conversation_history
        )
    
    async def generate_rag_response(
        self, 
        message: str,
        context_chunks: List[Dict],
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        RAG 기반 응답 생성 (문서 컨텍스트 포함)
        """
        # 컨텍스트 문서들을 프롬프트에 추가
        context_text = "\n\n".join([
            f"[출처: {chunk.get('metadata', {}).get('filename', 'Unknown')}]\n{chunk.get('content', '')}"
            for chunk in context_chunks
        ])
        
        rag_system_prompt = f"""다음 문서들을 참고하여 사용자의 질문에 답변해주세요.
문서에 없는 내용은 추측하지 말고, 문서 내용을 바탕으로만 답변하세요.
답변 끝에는 참고한 문서의 출처를 명시해주세요.

참고 문서:
{context_text}

{system_prompt or ""}"""

        result = await self._generate_llm_response(
            message, provider, rag_system_prompt, conversation_history
        )
        
        # 출처 정보 추가
        if result.get("success"):
            result["sources"] = [
                {
                    "document_id": chunk.get("document_id"),
                    "filename": chunk.get("metadata", {}).get("filename"),
                    "content_preview": chunk.get("content", "")[:100] + "...",
                    "score": chunk.get("score", 0)
                }
                for chunk in context_chunks
            ]
        
        return result

    async def _generate_llm_response(
        self, 
        message: str, 
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        LLM을 사용하여 응답 생성
        """
        try:
            # 제공자 선택
            if provider:
                selected_provider = LLMProvider(provider.lower())
            else:
                selected_provider = self.default_provider
            
            if not selected_provider:
                return {
                    "success": False,
                    "error": "No LLM provider configured",
                    "response": "LLM 서비스가 설정되지 않았습니다."
                }
            
            # Gemini로 응답 생성
            if selected_provider == LLMProvider.GEMINI:
                return await self._generate_gemini_response(
                    message, system_prompt, conversation_history
                )
            elif selected_provider == LLMProvider.OPENAI:
                return await self._generate_openai_response(
                    message, system_prompt, conversation_history
                )
            else:
                return {
                    "success": False,
                    "error": f"Provider {selected_provider.value} not implemented",
                    "response": f"{selected_provider.value} 제공자는 아직 구현되지 않았습니다."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"오류가 발생했습니다: {str(e)}"
            }
    
    async def _generate_gemini_response(
        self, 
        message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Gemini를 사용하여 응답 생성
        """
        try:
            # 대화 컨텍스트 구성
            prompt = ""
            
            if system_prompt:
                prompt += f"시스템 지시사항: {system_prompt}\n\n"
            
            if conversation_history:
                prompt += "대화 기록:\n"
                for msg in conversation_history[-5:]:  # 최근 5개 메시지만 사용
                    role = "사용자" if msg.get("role") == "user" else "AI"
                    prompt += f"{role}: {msg.get('content', '')}\n"
                prompt += "\n"
            
            prompt += f"사용자: {message}\nAI:"
            
            # Gemini로 응답 생성
            response = self.gemini_model.generate_content(prompt)
            
            return {
                "success": True,
                "response": response.text,
                "provider": "gemini",
                "model": "gemini-1.5-flash",
                "tokens": {
                    "prompt": len(prompt.split()),
                    "completion": len(response.text.split())
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Gemini 응답 생성 중 오류: {str(e)}"
            }
    
    async def _generate_openai_response(
        self, 
        message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        OpenAI를 사용하여 응답 생성
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            if conversation_history:
                for msg in conversation_history[-5:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({"role": "user", "content": message})
            
            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "tokens": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"OpenAI 응답 생성 중 오류: {str(e)}"
            }
    
    def get_available_providers(self) -> List[Dict]:
        """
        사용 가능한 LLM 제공자 목록 반환
        """
        providers = []
        
        if self.gemini_api_key:
            providers.append({
                "id": "gemini",
                "name": "Google Gemini",
                "model": "gemini-1.5-flash",
                "available": True,
                "default": True
            })
        
        if self.openai_api_key and HAS_OPENAI:
            providers.append({
                "id": "openai",
                "name": "OpenAI GPT-4",
                "model": "gpt-4-turbo-preview",
                "available": True,
                "default": False
            })
        
        # Claude는 아직 미구현
        providers.append({
            "id": "claude",
            "name": "Anthropic Claude",
            "model": "claude-3-opus",
            "available": False,
            "default": False
        })
        
        return providers