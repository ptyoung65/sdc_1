"""
Text-to-SQL 변환기
자연어 질문을 SQL 쿼리로 변환하는 모듈
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class SQLQuery:
    """SQL 쿼리 정보"""
    sql: str
    confidence: float
    reasoning: str
    parameters: Dict[str, Any]
    estimated_complexity: str  # simple, medium, complex
    safety_check: bool
    tables_involved: List[str]

@dataclass
class DatabaseSchema:
    """데이터베이스 스키마 정보"""
    tables: Dict[str, Dict[str, str]]  # table_name: {column_name: column_type}
    relationships: List[Dict[str, str]]  # foreign key relationships
    descriptions: Dict[str, str]  # table descriptions

class TextToSQLConverter:
    """자연어를 SQL로 변환하는 클래스"""
    
    def __init__(self, llm_client=None):
        """
        Text-to-SQL 변환기 초기화
        
        Args:
            llm_client: LLM 클라이언트 (OpenAI, Anthropic 등)
        """
        self.llm_client = llm_client
        self.db_schema = None
        self.question_patterns = self._initialize_patterns()
        logger.info("Text-to-SQL 변환기 초기화 완료")
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """한국어 질문 패턴 초기화"""
        return {
            "count": ["몇 개", "몇명", "얼마나", "수량", "개수", "명수"],
            "sum": ["총", "합계", "총계", "전체", "누적"],
            "average": ["평균", "평균적으로", "보통", "일반적으로"],
            "max": ["최대", "가장 큰", "최고", "최상"],
            "min": ["최소", "가장 작은", "최저", "최하"],
            "recent": ["최근", "요즘", "근래", "지금"],
            "order": ["순서", "정렬", "순위", "랭킹"],
            "filter": ["조건", "필터", "에서", "만", "인"],
            "group": ["그룹", "분류", "별로", "기준으로"],
            "join": ["관련", "연결", "함께", "포함"]
        }
    
    def load_database_schema(self, schema_info: Dict[str, Any]) -> None:
        """데이터베이스 스키마 로드"""
        try:
            self.db_schema = DatabaseSchema(
                tables=schema_info.get("tables", {}),
                relationships=schema_info.get("relationships", []),
                descriptions=schema_info.get("descriptions", {})
            )
            logger.info(f"데이터베이스 스키마 로드 완료: {len(self.db_schema.tables)}개 테이블")
        except Exception as e:
            logger.error(f"스키마 로드 실패: {e}")
            raise
    
    def analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """질문 의도 분석"""
        try:
            intent = {
                "question": question,
                "needs_db_search": False,
                "query_type": "unknown",
                "operations": [],
                "entities": [],
                "confidence": 0.0
            }
            
            # DB 검색이 필요한 패턴 확인
            db_indicators = [
                "데이터", "기록", "정보", "목록", "리스트", "통계", "분석",
                "몇 개", "얼마나", "언제", "어디", "누구", "무엇",
                "최근", "지난", "이전", "현재", "총", "평균", "최대", "최소"
            ]
            
            for indicator in db_indicators:
                if indicator in question:
                    intent["needs_db_search"] = True
                    intent["confidence"] += 0.1
            
            # 쿼리 타입 분석
            for pattern_type, patterns in self.question_patterns.items():
                for pattern in patterns:
                    if pattern in question:
                        intent["operations"].append(pattern_type)
                        intent["confidence"] += 0.15
            
            # 기본 쿼리 타입 결정
            if "count" in intent["operations"]:
                intent["query_type"] = "aggregation"
            elif any(op in intent["operations"] for op in ["sum", "average", "max", "min"]):
                intent["query_type"] = "aggregation"
            elif "order" in intent["operations"]:
                intent["query_type"] = "ranking"
            elif "filter" in intent["operations"]:
                intent["query_type"] = "filtered_search"
            else:
                intent["query_type"] = "basic_search"
            
            intent["confidence"] = min(intent["confidence"], 1.0)
            
            logger.info(f"질문 의도 분석 완료: {intent['query_type']} (신뢰도: {intent['confidence']:.2f})")
            return intent
            
        except Exception as e:
            logger.error(f"질문 의도 분석 실패: {e}")
            return {"needs_db_search": False, "confidence": 0.0}
    
    async def convert_to_sql(self, question: str) -> SQLQuery:
        """자연어 질문을 SQL로 변환"""
        try:
            # 질문 의도 분석
            intent = self.analyze_question_intent(question)
            
            if not intent.get("needs_db_search", False):
                raise ValueError("DB 검색이 필요하지 않은 질문입니다.")
            
            if not self.db_schema:
                raise ValueError("데이터베이스 스키마가 로드되지 않았습니다.")
            
            # LLM을 통한 SQL 생성
            if self.llm_client:
                sql_result = await self._generate_sql_with_llm(question, intent)
            else:
                sql_result = self._generate_sql_with_patterns(question, intent)
            
            # SQL 안전성 검증
            sql_result.safety_check = self._validate_sql_safety(sql_result.sql)
            
            logger.info(f"SQL 변환 완료: {sql_result.sql[:100]}...")
            return sql_result
            
        except Exception as e:
            logger.error(f"SQL 변환 실패: {e}")
            raise
    
    async def _generate_sql_with_llm(self, question: str, intent: Dict[str, Any]) -> SQLQuery:
        """LLM을 사용한 SQL 생성"""
        try:
            # 스키마 정보 준비
            schema_description = self._format_schema_for_llm()
            
            # LLM 프롬프트 구성
            prompt = f"""
당신은 한국어 질문을 PostgreSQL 쿼리로 변환하는 전문가입니다.

데이터베이스 스키마:
{schema_description}

질문 분석 결과:
- 질문: {question}
- 쿼리 타입: {intent.get('query_type', 'unknown')}
- 필요 연산: {', '.join(intent.get('operations', []))}

요구사항:
1. 안전한 SQL만 생성 (SELECT 문만 허용)
2. SQL 인젝션 방지
3. 성능을 고려한 쿼리 작성
4. 한국어 컬럼명/값 처리

응답 형식 (JSON):
{{
    "sql": "생성된 SQL 쿼리",
    "confidence": 0.0-1.0,
    "reasoning": "SQL 생성 근거",
    "tables_involved": ["테이블명들"],
    "estimated_complexity": "simple|medium|complex"
}}
"""
            
            # LLM 호출 (구현은 사용하는 LLM에 따라 달라짐)
            response = await self._call_llm(prompt)
            
            # 응답 파싱
            result = json.loads(response)
            
            return SQLQuery(
                sql=result["sql"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                parameters={},
                estimated_complexity=result["estimated_complexity"],
                safety_check=False,  # 나중에 검증
                tables_involved=result["tables_involved"]
            )
            
        except Exception as e:
            logger.error(f"LLM SQL 생성 실패: {e}")
            # 패턴 기반으로 폴백
            return self._generate_sql_with_patterns(question, intent)
    
    def _generate_sql_with_patterns(self, question: str, intent: Dict[str, Any]) -> SQLQuery:
        """패턴 기반 SQL 생성 (폴백)"""
        try:
            # 간단한 패턴 매칭으로 SQL 생성
            sql_parts = {
                "select": "*",
                "from": "",
                "where": "",
                "group_by": "",
                "order_by": "",
                "limit": ""
            }
            
            # 테이블 추측
            table_name = self._guess_table_from_question(question)
            if not table_name:
                raise ValueError("관련 테이블을 찾을 수 없습니다.")
            
            sql_parts["from"] = table_name
            
            # 집계 함수 처리
            if "count" in intent.get("operations", []):
                sql_parts["select"] = "COUNT(*)"
            elif "sum" in intent.get("operations", []):
                sql_parts["select"] = "SUM(amount)"  # 예시
            elif "average" in intent.get("operations", []):
                sql_parts["select"] = "AVG(value)"  # 예시
            
            # 조건 처리
            conditions = self._extract_conditions_from_question(question)
            if conditions:
                sql_parts["where"] = " AND ".join(conditions)
            
            # 정렬 처리
            if "recent" in intent.get("operations", []):
                sql_parts["order_by"] = "created_at DESC"
                sql_parts["limit"] = "10"
            
            # SQL 조립
            sql = f"SELECT {sql_parts['select']} FROM {sql_parts['from']}"
            
            if sql_parts["where"]:
                sql += f" WHERE {sql_parts['where']}"
            if sql_parts["group_by"]:
                sql += f" GROUP BY {sql_parts['group_by']}"
            if sql_parts["order_by"]:
                sql += f" ORDER BY {sql_parts['order_by']}"
            if sql_parts["limit"]:
                sql += f" LIMIT {sql_parts['limit']}"
            
            return SQLQuery(
                sql=sql,
                confidence=0.6,  # 패턴 기반은 낮은 신뢰도
                reasoning="패턴 기반 SQL 생성",
                parameters={},
                estimated_complexity="simple",
                safety_check=False,
                tables_involved=[table_name]
            )
            
        except Exception as e:
            logger.error(f"패턴 기반 SQL 생성 실패: {e}")
            raise
    
    def _format_schema_for_llm(self) -> str:
        """LLM용 스키마 형식화"""
        if not self.db_schema:
            return "스키마 정보 없음"
        
        schema_text = []
        for table_name, columns in self.db_schema.tables.items():
            schema_text.append(f"테이블: {table_name}")
            for col_name, col_type in columns.items():
                schema_text.append(f"  - {col_name}: {col_type}")
            
            # 테이블 설명 추가
            if table_name in self.db_schema.descriptions:
                schema_text.append(f"  설명: {self.db_schema.descriptions[table_name]}")
            schema_text.append("")
        
        return "\n".join(schema_text)
    
    def _guess_table_from_question(self, question: str) -> Optional[str]:
        """질문에서 테이블명 추측"""
        if not self.db_schema:
            return None
        
        # 테이블명이나 설명에서 매칭되는 키워드 찾기
        for table_name, columns in self.db_schema.tables.items():
            # 테이블명 직접 매칭
            if table_name.lower() in question.lower():
                return table_name
            
            # 설명에서 매칭
            if table_name in self.db_schema.descriptions:
                description = self.db_schema.descriptions[table_name]
                keywords = description.split()
                for keyword in keywords:
                    if len(keyword) > 1 and keyword in question:
                        return table_name
        
        # 기본 테이블 반환 (첫 번째 테이블)
        if self.db_schema.tables:
            return list(self.db_schema.tables.keys())[0]
        
        return None
    
    def _extract_conditions_from_question(self, question: str) -> List[str]:
        """질문에서 WHERE 조건 추출"""
        conditions = []
        
        # 간단한 패턴 매칭으로 조건 추출
        # 실제로는 더 정교한 NER이나 패턴 매칭이 필요
        
        # 날짜 조건
        if "최근" in question or "지난" in question:
            conditions.append("created_at >= NOW() - INTERVAL '7 days'")
        
        # 상태 조건
        if "활성" in question or "사용중" in question:
            conditions.append("status = 'active'")
        
        return conditions
    
    def _validate_sql_safety(self, sql: str) -> bool:
        """SQL 안전성 검증"""
        try:
            # 기본 안전성 검사
            sql_upper = sql.upper().strip()
            
            # SELECT 문만 허용
            if not sql_upper.startswith("SELECT"):
                return False
            
            # 위험한 키워드 체크
            dangerous_keywords = [
                "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
                "TRUNCATE", "EXEC", "EXECUTE", "UNION", "--", "/*", "*/"
            ]
            
            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    return False
            
            # 기본적인 구문 검증
            if sql.count("'") % 2 != 0:  # 홑따옴표 짝 맞지 않음
                return False
            
            if sql.count("(") != sql.count(")"):  # 괄호 짝 맞지 않음
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"SQL 안전성 검증 실패: {e}")
            return False
    
    async def _call_llm(self, prompt: str) -> str:
        """LLM 호출 (실제 구현은 사용하는 LLM에 따라 다름)"""
        # 여기서는 임시로 더미 응답 반환
        # 실제로는 OpenAI, Anthropic 등의 API 호출
        return '''
        {
            "sql": "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '30 days'",
            "confidence": 0.85,
            "reasoning": "최근 사용자 수를 조회하는 쿼리",
            "tables_involved": ["users"],
            "estimated_complexity": "simple"
        }
        '''

def get_text_to_sql_converter() -> TextToSQLConverter:
    """Text-to-SQL 변환기 인스턴스 반환"""
    return TextToSQLConverter()