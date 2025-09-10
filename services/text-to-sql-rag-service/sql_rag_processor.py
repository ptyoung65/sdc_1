"""
SQL 결과를 RAG 데이터로 처리하는 모듈
"""

import logging
import asyncio
import asyncpg
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import json

from text_to_sql_converter import SQLQuery

logger = logging.getLogger(__name__)

@dataclass
class RAGData:
    """RAG 처리된 데이터"""
    query_result: List[Dict[str, Any]]
    structured_context: str
    summary: str
    insights: List[str]
    metadata: Dict[str, Any]
    quality_score: float
    processing_time: float

@dataclass
class QueryExecution:
    """쿼리 실행 결과"""
    success: bool
    data: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    error_message: Optional[str] = None

class SQLRAGProcessor:
    """SQL 결과를 RAG 데이터로 처리하는 클래스"""
    
    def __init__(self, db_connection_string: str, llm_client=None):
        """
        SQL RAG 프로세서 초기화
        
        Args:
            db_connection_string: PostgreSQL 연결 문자열
            llm_client: LLM 클라이언트
        """
        self.db_connection_string = db_connection_string
        self.llm_client = llm_client
        self.db_pool = None
        logger.info("SQL RAG 프로세서 초기화 완료")
    
    async def initialize_db_pool(self):
        """데이터베이스 연결 풀 초기화"""
        try:
            self.db_pool = await asyncpg.create_pool(
                self.db_connection_string,
                min_size=1,
                max_size=10,
                command_timeout=30
            )
            logger.info("데이터베이스 연결 풀 초기화 완료")
        except Exception as e:
            logger.error(f"DB 연결 풀 초기화 실패: {e}")
            raise
    
    async def close_db_pool(self):
        """데이터베이스 연결 풀 종료"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("데이터베이스 연결 풀 종료")
    
    async def execute_sql_query(self, sql_query: SQLQuery) -> QueryExecution:
        """SQL 쿼리 실행"""
        start_time = datetime.now()
        
        try:
            if not self.db_pool:
                await self.initialize_db_pool()
            
            async with self.db_pool.acquire() as connection:
                # 쿼리 실행
                rows = await connection.fetch(sql_query.sql)
                
                # 결과를 딕셔너리 리스트로 변환
                data = []
                for row in rows:
                    data.append(dict(row))
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"SQL 쿼리 실행 완료: {len(data)}개 행, {execution_time:.3f}초")
                
                return QueryExecution(
                    success=True,
                    data=data,
                    row_count=len(data),
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"SQL 쿼리 실행 실패: {e}")
            
            return QueryExecution(
                success=False,
                data=[],
                row_count=0,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def process_sql_results_to_rag(self, 
                                       question: str,
                                       sql_query: SQLQuery, 
                                       query_result: QueryExecution) -> RAGData:
        """SQL 결과를 RAG 데이터로 처리"""
        start_time = datetime.now()
        
        try:
            if not query_result.success:
                raise ValueError(f"쿼리 실행 실패: {query_result.error_message}")
            
            # 구조화된 컨텍스트 생성
            structured_context = self._create_structured_context(
                question, sql_query, query_result.data
            )
            
            # 데이터 요약 생성
            summary = await self._generate_data_summary(
                question, query_result.data
            )
            
            # 인사이트 추출
            insights = await self._extract_insights(
                question, query_result.data
            )
            
            # 품질 평가
            quality_score = self._evaluate_data_quality(
                sql_query, query_result
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            rag_data = RAGData(
                query_result=query_result.data,
                structured_context=structured_context,
                summary=summary,
                insights=insights,
                metadata={
                    "original_question": question,
                    "sql_query": sql_query.sql,
                    "row_count": query_result.row_count,
                    "execution_time": query_result.execution_time,
                    "sql_confidence": sql_query.confidence
                },
                quality_score=quality_score,
                processing_time=processing_time
            )
            
            logger.info(f"RAG 데이터 처리 완료: 품질점수 {quality_score:.2f}, 처리시간 {processing_time:.3f}초")
            return rag_data
            
        except Exception as e:
            logger.error(f"RAG 데이터 처리 실패: {e}")
            raise
    
    def _create_structured_context(self, 
                                 question: str, 
                                 sql_query: SQLQuery, 
                                 data: List[Dict[str, Any]]) -> str:
        """구조화된 컨텍스트 생성"""
        try:
            context_parts = []
            
            # 질문과 쿼리 정보
            context_parts.append(f"=== 질문 분석 ===")
            context_parts.append(f"원본 질문: {question}")
            context_parts.append(f"생성된 SQL: {sql_query.sql}")
            context_parts.append(f"SQL 신뢰도: {sql_query.confidence:.2f}")
            context_parts.append("")
            
            # 데이터 요약 정보
            context_parts.append(f"=== 데이터 요약 ===")
            context_parts.append(f"총 레코드 수: {len(data)}")
            
            if data:
                # 컬럼 정보
                columns = list(data[0].keys())
                context_parts.append(f"컬럼: {', '.join(columns)}")
                context_parts.append("")
                
                # 데이터 샘플 (상위 5개)
                context_parts.append("=== 데이터 샘플 ===")
                for i, row in enumerate(data[:5]):
                    context_parts.append(f"[{i+1}] {self._format_row_for_context(row)}")
                
                if len(data) > 5:
                    context_parts.append(f"... 외 {len(data) - 5}개 레코드")
                context_parts.append("")
                
                # 통계 정보 (숫자 컬럼에 대해)
                stats = self._calculate_basic_statistics(data)
                if stats:
                    context_parts.append("=== 기본 통계 ===")
                    for column, stat in stats.items():
                        context_parts.append(f"{column}: {stat}")
            else:
                context_parts.append("검색 결과가 없습니다.")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"구조화된 컨텍스트 생성 실패: {e}")
            return f"컨텍스트 생성 실패: {e}"
    
    def _format_row_for_context(self, row: Dict[str, Any]) -> str:
        """행 데이터를 컨텍스트용으로 형식화"""
        formatted_items = []
        for key, value in row.items():
            if value is not None:
                if isinstance(value, (int, float)):
                    formatted_items.append(f"{key}: {value}")
                elif isinstance(value, str):
                    # 긴 문자열은 자름
                    display_value = value[:50] + "..." if len(value) > 50 else value
                    formatted_items.append(f"{key}: {display_value}")
                else:
                    formatted_items.append(f"{key}: {str(value)}")
        
        return " | ".join(formatted_items)
    
    def _calculate_basic_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """기본 통계 계산"""
        try:
            if not data:
                return {}
            
            # pandas DataFrame으로 변환
            df = pd.DataFrame(data)
            stats = {}
            
            # 숫자 컬럼에 대한 통계
            numeric_columns = df.select_dtypes(include=['number']).columns
            for column in numeric_columns:
                column_stats = []
                column_stats.append(f"평균: {df[column].mean():.2f}")
                column_stats.append(f"최솟값: {df[column].min()}")
                column_stats.append(f"최댓값: {df[column].max()}")
                stats[column] = ", ".join(column_stats)
            
            # 문자열 컬럼에 대한 정보
            string_columns = df.select_dtypes(include=['object']).columns
            for column in string_columns:
                unique_count = df[column].nunique()
                stats[column] = f"고유값: {unique_count}개"
            
            return stats
            
        except Exception as e:
            logger.error(f"통계 계산 실패: {e}")
            return {}
    
    async def _generate_data_summary(self, question: str, data: List[Dict[str, Any]]) -> str:
        """데이터 요약 생성"""
        try:
            if not data:
                return "검색된 데이터가 없습니다."
            
            # LLM을 사용한 요약 (사용 가능한 경우)
            if self.llm_client:
                return await self._generate_summary_with_llm(question, data)
            
            # 간단한 규칙 기반 요약
            summary_parts = []
            
            # 기본 정보
            summary_parts.append(f"'{question}' 질문에 대해 {len(data)}개의 결과를 찾았습니다.")
            
            if len(data) == 1:
                summary_parts.append("단일 결과가 반환되었습니다.")
            elif len(data) < 10:
                summary_parts.append("적은 수의 결과가 반환되었습니다.")
            elif len(data) < 100:
                summary_parts.append("중간 규모의 결과가 반환되었습니다.")
            else:
                summary_parts.append("대량의 결과가 반환되었습니다.")
            
            # 컬럼 정보
            if data:
                columns = list(data[0].keys())
                summary_parts.append(f"주요 데이터 항목: {', '.join(columns[:5])}")
                if len(columns) > 5:
                    summary_parts.append(f"외 {len(columns) - 5}개 항목")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"데이터 요약 생성 실패: {e}")
            return "요약 생성에 실패했습니다."
    
    async def _extract_insights(self, question: str, data: List[Dict[str, Any]]) -> List[str]:
        """데이터에서 인사이트 추출"""
        try:
            insights = []
            
            if not data:
                insights.append("검색 결과가 없어 분석할 수 없습니다.")
                return insights
            
            # 기본 인사이트들
            insights.append(f"총 {len(data)}개의 레코드가 조건에 매칭됩니다.")
            
            # 숫자 데이터 인사이트
            df = pd.DataFrame(data)
            numeric_columns = df.select_dtypes(include=['number']).columns
            
            for column in numeric_columns:
                if not df[column].isna().all():
                    avg_value = df[column].mean()
                    max_value = df[column].max()
                    min_value = df[column].min()
                    
                    insights.append(f"{column}의 평균값은 {avg_value:.2f}입니다.")
                    if max_value != min_value:
                        insights.append(f"{column}의 범위는 {min_value}부터 {max_value}까지입니다.")
            
            # 카테고리 데이터 인사이트
            string_columns = df.select_dtypes(include=['object']).columns
            for column in string_columns:
                if not df[column].isna().all():
                    unique_count = df[column].nunique()
                    if unique_count < len(data):
                        most_common = df[column].value_counts().index[0]
                        insights.append(f"{column}에서 가장 빈번한 값은 '{most_common}'입니다.")
            
            # LLM 기반 고급 인사이트 (가능한 경우)
            if self.llm_client:
                advanced_insights = await self._generate_insights_with_llm(question, data)
                insights.extend(advanced_insights)
            
            return insights[:10]  # 최대 10개 인사이트
            
        except Exception as e:
            logger.error(f"인사이트 추출 실패: {e}")
            return ["인사이트 추출에 실패했습니다."]
    
    def _evaluate_data_quality(self, sql_query: SQLQuery, query_result: QueryExecution) -> float:
        """데이터 품질 평가"""
        try:
            quality_score = 0.0
            
            # SQL 신뢰도 (30%)
            quality_score += sql_query.confidence * 0.3
            
            # 실행 성공 여부 (20%)
            if query_result.success:
                quality_score += 0.2
            
            # 결과 데이터 유무 (20%)
            if query_result.row_count > 0:
                quality_score += 0.2
            
            # 실행 속도 (15%)
            if query_result.execution_time < 1.0:
                quality_score += 0.15
            elif query_result.execution_time < 5.0:
                quality_score += 0.1
            
            # 결과 크기 적절성 (15%)
            if 1 <= query_result.row_count <= 1000:
                quality_score += 0.15
            elif query_result.row_count > 0:
                quality_score += 0.1
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            logger.error(f"데이터 품질 평가 실패: {e}")
            return 0.0
    
    async def _generate_summary_with_llm(self, question: str, data: List[Dict[str, Any]]) -> str:
        """LLM을 사용한 고급 요약 생성"""
        # 실제 구현에서는 LLM API 호출
        return f"LLM 생성 요약: {question}에 대한 {len(data)}개 결과의 요약입니다."
    
    async def _generate_insights_with_llm(self, question: str, data: List[Dict[str, Any]]) -> List[str]:
        """LLM을 사용한 고급 인사이트 생성"""
        # 실제 구현에서는 LLM API 호출
        return ["LLM이 생성한 고급 인사이트 1", "LLM이 생성한 고급 인사이트 2"]

def get_sql_rag_processor(db_connection_string: str) -> SQLRAGProcessor:
    """SQL RAG 프로세서 인스턴스 반환"""
    return SQLRAGProcessor(db_connection_string)