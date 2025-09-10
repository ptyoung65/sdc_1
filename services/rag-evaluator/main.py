"""
RAG Performance Evaluation Microservice
Comprehensive RAG system performance metrics collection and evaluation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import asyncio
import time
import uuid
from datetime import datetime, timedelta
import logging
import json
import statistics
from enum import Enum
import numpy as np
from dataclasses import dataclass
import httpx
import redis
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Performance Evaluator",
    description="Comprehensive RAG system performance metrics and evaluation service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Models
Base = declarative_base()

class RAGMetrics(Base):
    __tablename__ = "rag_metrics"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Context Metrics
    context_relevance = Column(Float, nullable=True)
    context_sufficiency = Column(Float, nullable=True)
    retrieved_chunks = Column(JSON, nullable=True)
    
    # Answer Metrics  
    answer_relevance = Column(Float, nullable=True)
    answer_correctness = Column(Float, nullable=True)
    hallucination_rate = Column(Float, nullable=True)
    
    # Performance Metrics
    retrieval_latency_ms = Column(Integer, nullable=True)
    generation_latency_ms = Column(Integer, nullable=True)
    total_latency_ms = Column(Integer, nullable=True)
    
    # Additional Fields
    llm_response = Column(Text, nullable=True)
    ground_truth = Column(Text, nullable=True)
    metric_metadata = Column(JSON, nullable=True)

# Pydantic Models
class MetricType(str, Enum):
    CONTEXT_RELEVANCE = "context_relevance"
    CONTEXT_SUFFICIENCY = "context_sufficiency"
    ANSWER_RELEVANCE = "answer_relevance"
    ANSWER_CORRECTNESS = "answer_correctness"
    HALLUCINATION_RATE = "hallucination_rate"
    LATENCY = "latency"
    THROUGHPUT = "throughput"

class RAGStage(BaseModel):
    stage: str
    start_time: float
    end_time: float
    latency_ms: int
    status: str = "success"
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class RetrievalStage(RAGStage):
    retrieved_chunks: List[Dict[str, Any]] = []
    retrieval_score: Optional[float] = None
    num_chunks: int = 0

class GenerationStage(RAGStage):
    llm_response: str = ""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    model_name: str = ""

class RAGEvaluationRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    retrieval_stage: RetrievalStage
    generation_stage: GenerationStage
    ground_truth: Optional[str] = None
    user_id: str = "default"
    metadata: Dict[str, Any] = {}

class RAGMetricsResponse(BaseModel):
    id: str
    session_id: str
    timestamp: datetime
    
    # Computed Metrics
    context_relevance: Optional[float] = None
    context_sufficiency: Optional[float] = None
    answer_relevance: Optional[float] = None
    answer_correctness: Optional[float] = None  
    hallucination_rate: Optional[float] = None
    
    # Performance Metrics
    retrieval_latency_ms: int
    generation_latency_ms: int
    total_latency_ms: int
    throughput: Optional[float] = None
    
    # Quality Score
    overall_quality_score: Optional[float] = None

class MetricsAggregation(BaseModel):
    period: str
    start_time: datetime
    end_time: datetime
    total_queries: int
    
    # Average Metrics
    avg_context_relevance: Optional[float] = None
    avg_context_sufficiency: Optional[float] = None
    avg_answer_relevance: Optional[float] = None
    avg_answer_correctness: Optional[float] = None
    avg_hallucination_rate: Optional[float] = None
    
    # Performance Statistics
    avg_retrieval_latency_ms: float
    avg_generation_latency_ms: float
    avg_total_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_per_second: float
    
    # Quality Metrics
    avg_quality_score: Optional[float] = None
    quality_distribution: Dict[str, int] = {}

# RAG Evaluation Engine
class RAGEvaluator:
    """Advanced RAG performance evaluation engine"""
    
    def __init__(self):
        self.embeddings_cache = {}
        
    async def compute_context_relevance(self, query: str, chunks: List[Dict[str, Any]]) -> float:
        """
        Context Relevance: 검색된 문서가 질의에 얼마나 관련성 있는지
        Uses semantic similarity between query and retrieved chunks
        """
        if not chunks:
            return 0.0
            
        try:
            relevance_scores = []
            for chunk in chunks:
                content = chunk.get('content', '')
                if not content:
                    continue
                    
                # Simplified relevance computation (in production, use embeddings)
                # For now, use keyword overlap and length-normalized similarity
                query_words = set(query.lower().split())
                content_words = set(content.lower().split())
                
                if not query_words or not content_words:
                    continue
                    
                intersection = len(query_words.intersection(content_words))
                union = len(query_words.union(content_words))
                
                if union > 0:
                    jaccard_similarity = intersection / union
                    relevance_scores.append(jaccard_similarity)
            
            return statistics.mean(relevance_scores) if relevance_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error computing context relevance: {e}")
            return 0.0
    
    async def compute_context_sufficiency(self, query: str, chunks: List[Dict[str, Any]]) -> float:
        """
        Context Sufficiency: 검색된 컨텍스트만으로 답변 생성에 충분한지
        """
        if not chunks:
            return 0.0
            
        try:
            # Compute based on total content length and coverage
            total_content_length = sum(len(chunk.get('content', '')) for chunk in chunks)
            
            # Basic heuristic: longer content generally provides better sufficiency
            # Normalize by query length and number of chunks
            query_length = len(query.split())
            chunk_count = len(chunks)
            
            # Simple sufficiency score based on content-to-query ratio
            content_to_query_ratio = total_content_length / max(len(query), 1)
            chunk_diversity_bonus = min(chunk_count / 5.0, 1.0)  # Bonus for having multiple chunks
            
            sufficiency_score = min(content_to_query_ratio / 100.0 + chunk_diversity_bonus, 1.0)
            
            return max(0.0, min(sufficiency_score, 1.0))
            
        except Exception as e:
            logger.error(f"Error computing context sufficiency: {e}")
            return 0.0
    
    async def compute_answer_relevance(self, query: str, answer: str) -> float:
        """
        Answer Relevance: 최종 답변이 질의에 얼마나 부합하는지
        """
        if not answer or not query:
            return 0.0
            
        try:
            query_words = set(query.lower().split())
            answer_words = set(answer.lower().split())
            
            if not query_words or not answer_words:
                return 0.0
                
            # Compute semantic overlap
            intersection = len(query_words.intersection(answer_words))
            query_coverage = intersection / len(query_words)
            
            # Penalize answers that are too short or too long relative to query
            length_ratio = len(answer.split()) / max(len(query.split()), 1)
            length_penalty = 1.0 if 0.5 <= length_ratio <= 10.0 else 0.8
            
            relevance_score = query_coverage * length_penalty
            
            return max(0.0, min(relevance_score, 1.0))
            
        except Exception as e:
            logger.error(f"Error computing answer relevance: {e}")
            return 0.0
    
    async def compute_answer_correctness(self, answer: str, ground_truth: Optional[str]) -> Optional[float]:
        """
        Answer Correctness: 답변이 정답과 얼마나 일치하는지
        """
        if not ground_truth or not answer:
            return None
            
        try:
            # Simple token-level F1 score
            answer_tokens = set(answer.lower().split())
            truth_tokens = set(ground_truth.lower().split())
            
            if not answer_tokens or not truth_tokens:
                return 0.0
                
            intersection = len(answer_tokens.intersection(truth_tokens))
            
            if intersection == 0:
                return 0.0
                
            precision = intersection / len(answer_tokens)
            recall = intersection / len(truth_tokens)
            
            f1_score = 2 * (precision * recall) / (precision + recall)
            
            return max(0.0, min(f1_score, 1.0))
            
        except Exception as e:
            logger.error(f"Error computing answer correctness: {e}")
            return 0.0
    
    async def compute_hallucination_rate(self, answer: str, chunks: List[Dict[str, Any]]) -> float:
        """
        Hallucination Rate: 허위 정보를 생성하는 비율
        """
        if not answer or not chunks:
            return 1.0  # High hallucination if no context
            
        try:
            answer_sentences = [s.strip() for s in answer.split('.') if s.strip()]
            if not answer_sentences:
                return 0.0
                
            # Combine all chunk content
            all_context = ' '.join([chunk.get('content', '') for chunk in chunks])
            context_words = set(all_context.lower().split())
            
            hallucinated_sentences = 0
            
            for sentence in answer_sentences:
                sentence_words = set(sentence.lower().split())
                
                if not sentence_words:
                    continue
                    
                # Check if sentence has sufficient overlap with context
                overlap = len(sentence_words.intersection(context_words))
                overlap_ratio = overlap / len(sentence_words) if sentence_words else 0
                
                # If less than 30% overlap, consider it potentially hallucinated
                if overlap_ratio < 0.3:
                    hallucinated_sentences += 1
            
            hallucination_rate = hallucinated_sentences / len(answer_sentences)
            
            return max(0.0, min(hallucination_rate, 1.0))
            
        except Exception as e:
            logger.error(f"Error computing hallucination rate: {e}")
            return 1.0
    
    async def compute_overall_quality_score(self, metrics: Dict[str, float]) -> float:
        """
        Overall Quality Score: 전체적인 품질 점수 계산
        """
        try:
            weights = {
                'context_relevance': 0.2,
                'context_sufficiency': 0.15,
                'answer_relevance': 0.25,
                'answer_correctness': 0.25,
                'hallucination_penalty': 0.15
            }
            
            score = 0.0
            total_weight = 0.0
            
            for metric, weight in weights.items():
                if metric == 'hallucination_penalty':
                    # Hallucination rate should reduce the score
                    hallucination_rate = metrics.get('hallucination_rate')
                    if hallucination_rate is not None:
                        score += (1.0 - hallucination_rate) * weight
                        total_weight += weight
                else:
                    value = metrics.get(metric)
                    if value is not None:
                        score += value * weight
                        total_weight += weight
            
            return score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error computing overall quality score: {e}")
            return 0.0

# Global evaluator instance
evaluator = RAGEvaluator()

# API Endpoints
@app.post("/api/v1/rag/evaluate", response_model=RAGMetricsResponse)
async def evaluate_rag_performance(request: RAGEvaluationRequest, background_tasks: BackgroundTasks):
    """
    RAG 성능을 종합적으로 평가하고 메트릭을 수집합니다
    """
    try:
        evaluation_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        logger.info(f"🎯 [RAG-EVAL] Starting evaluation for session: {request.session_id}")
        
        # Extract data
        query = request.query
        retrieval_stage = request.retrieval_stage
        generation_stage = request.generation_stage
        chunks = retrieval_stage.retrieved_chunks
        answer = generation_stage.llm_response
        
        # Compute metrics
        metrics = {}
        
        # Context Metrics
        logger.info("📊 [RAG-EVAL] Computing context metrics...")
        metrics['context_relevance'] = await evaluator.compute_context_relevance(query, chunks)
        metrics['context_sufficiency'] = await evaluator.compute_context_sufficiency(query, chunks)
        
        # Answer Metrics
        logger.info("📝 [RAG-EVAL] Computing answer metrics...")
        metrics['answer_relevance'] = await evaluator.compute_answer_relevance(query, answer)
        
        if request.ground_truth:
            metrics['answer_correctness'] = await evaluator.compute_answer_correctness(answer, request.ground_truth)
        
        metrics['hallucination_rate'] = await evaluator.compute_hallucination_rate(answer, chunks)
        
        # Performance Metrics
        retrieval_latency = retrieval_stage.latency_ms
        generation_latency = generation_stage.latency_ms
        total_latency = retrieval_latency + generation_latency
        
        # Overall Quality Score
        overall_quality = await evaluator.compute_overall_quality_score(metrics)
        
        # Create response
        response = RAGMetricsResponse(
            id=evaluation_id,
            session_id=request.session_id,
            timestamp=timestamp,
            context_relevance=metrics.get('context_relevance'),
            context_sufficiency=metrics.get('context_sufficiency'),
            answer_relevance=metrics.get('answer_relevance'),
            answer_correctness=metrics.get('answer_correctness'),
            hallucination_rate=metrics.get('hallucination_rate'),
            retrieval_latency_ms=retrieval_latency,
            generation_latency_ms=generation_latency,
            total_latency_ms=total_latency,
            overall_quality_score=overall_quality
        )
        
        # Log metrics for monitoring
        logger.info(f"✅ [RAG-EVAL] Evaluation completed:")
        logger.info(f"   Context Relevance: {metrics.get('context_relevance', 'N/A'):.3f}")
        logger.info(f"   Context Sufficiency: {metrics.get('context_sufficiency', 'N/A'):.3f}")
        logger.info(f"   Answer Relevance: {metrics.get('answer_relevance', 'N/A'):.3f}")
        logger.info(f"   Hallucination Rate: {metrics.get('hallucination_rate', 'N/A'):.3f}")
        logger.info(f"   Overall Quality: {overall_quality:.3f}")
        logger.info(f"   Total Latency: {total_latency}ms")
        
        # Store metrics in background
        background_tasks.add_task(store_metrics_async, evaluation_id, request, metrics, timestamp)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ [RAG-EVAL] Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.get("/api/v1/rag/metrics/aggregated")
async def get_aggregated_metrics(
    period: str = "1h",  # 1h, 24h, 7d, 30d
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> MetricsAggregation:
    """
    RAG 성능 지표의 집계된 통계를 반환합니다
    """
    try:
        logger.info(f"📈 [RAG-EVAL] Getting aggregated metrics for period: {period}")
        
        # For demo purposes, return mock aggregated data
        now = datetime.now()
        
        if period == "1h":
            start = now - timedelta(hours=1)
        elif period == "24h":
            start = now - timedelta(days=1)
        elif period == "7d":
            start = now - timedelta(days=7)
        elif period == "30d":
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(hours=1)
        
        # Mock aggregated data
        aggregation = MetricsAggregation(
            period=period,
            start_time=start,
            end_time=now,
            total_queries=150,
            avg_context_relevance=0.78,
            avg_context_sufficiency=0.82,
            avg_answer_relevance=0.85,
            avg_answer_correctness=0.79,
            avg_hallucination_rate=0.12,
            avg_retrieval_latency_ms=245,
            avg_generation_latency_ms=1850,
            avg_total_latency_ms=2095,
            p95_latency_ms=3200,
            p99_latency_ms=4500,
            throughput_per_second=2.3,
            avg_quality_score=0.81,
            quality_distribution={
                "excellent": 45,
                "good": 67,
                "fair": 28,
                "poor": 10
            }
        )
        
        return aggregation
        
    except Exception as e:
        logger.error(f"❌ [RAG-EVAL] Failed to get aggregated metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/api/v1/rag/metrics/realtime")
async def get_realtime_metrics():
    """
    실시간 RAG 성능 지표를 반환합니다
    """
    try:
        # Mock real-time data
        realtime_data = {
            "timestamp": datetime.now().isoformat(),
            "current_throughput": 2.1,
            "avg_latency_1min": 2150,
            "active_sessions": 12,
            "success_rate": 0.96,
            "recent_quality_scores": [0.85, 0.79, 0.91, 0.73, 0.88],
            "status": "healthy"
        }
        
        return realtime_data
        
    except Exception as e:
        logger.error(f"❌ [RAG-EVAL] Failed to get realtime metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get realtime metrics: {str(e)}")

@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "rag-evaluator",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

async def store_metrics_async(evaluation_id: str, request: RAGEvaluationRequest, metrics: Dict[str, Any], timestamp: datetime):
    """
    메트릭을 데이터베이스에 비동기로 저장
    """
    try:
        logger.info(f"💾 [RAG-EVAL] Storing metrics for evaluation: {evaluation_id}")
        # Here you would store to your database
        # For now, just log the metrics
        logger.info(f"   Stored metrics: {json.dumps(metrics, default=str)}")
    except Exception as e:
        logger.error(f"❌ [RAG-EVAL] Failed to store metrics: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)