"""
AI-Curated RAG Pipeline Orchestrator Service
Manages end-to-end RAG pipeline with intelligent orchestration and optimization
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio
import httpx
import logging
import json
import uuid
from enum import Enum
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Orchestrator Service",
    description="Intelligent orchestration for AI-curated RAG pipeline",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CURATION_SERVICE_URL = "http://curation-service:8006"
AI_MODEL_URL = "http://ai-model-service:8007"
VECTOR_DB_URL = "http://vector-db-service:8003"
DOCUMENT_PROCESSING_URL = "http://document-processing-service:8004"
EVALUATION_URL = "http://rag-evaluator:8006"

# Enums
class PipelineMode(str, Enum):
    STANDARD = "standard"
    CURATED = "curated"
    HYBRID = "hybrid"
    EXPERIMENTAL = "experimental"

class ProcessingStage(str, Enum):
    QUERY_ANALYSIS = "query_analysis"
    RETRIEVAL = "retrieval"
    CURATION = "curation"
    AUGMENTATION = "augmentation"
    GENERATION = "generation"
    POST_PROCESSING = "post_processing"
    EVALUATION = "evaluation"

class OptimizationStrategy(str, Enum):
    LATENCY_OPTIMIZED = "latency_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    COST_OPTIMIZED = "cost_optimized"
    BALANCED = "balanced"

# Models
class QueryIntent(BaseModel):
    intent_type: str
    confidence: float
    entities: List[Dict[str, Any]]
    complexity: str
    requires_curation: bool
    suggested_pipeline: PipelineMode

class RAGRequest(BaseModel):
    query: str
    mode: PipelineMode = PipelineMode.CURATED
    optimization: OptimizationStrategy = OptimizationStrategy.BALANCED
    user_context: Dict[str, Any] = Field(default_factory=dict)
    enable_streaming: bool = False
    max_chunks: int = Field(default=10, ge=1, le=50)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    enable_evaluation: bool = True
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)

class RAGResponse(BaseModel):
    request_id: str
    query: str
    answer: str
    mode: PipelineMode
    sources: List[Dict[str, Any]]
    pipeline_trace: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    evaluation: Optional[Dict[str, Any]]
    processing_time_ms: int
    timestamp: datetime

class PipelineConfig(BaseModel):
    mode: PipelineMode
    stages: List[ProcessingStage]
    optimization: OptimizationStrategy
    parallel_stages: List[List[ProcessingStage]]
    stage_timeouts: Dict[ProcessingStage, int]
    retry_policy: Dict[str, Any]
    cache_config: Dict[str, Any]

class StageResult(BaseModel):
    stage: ProcessingStage
    status: str
    output: Any
    metrics: Dict[str, float]
    duration_ms: int
    errors: List[str] = Field(default_factory=list)

# Pipeline Orchestrator
class PipelineOrchestrator:
    def __init__(self):
        self.active_pipelines = {}
        self.pipeline_configs = self._initialize_configs()
        self.stage_cache = defaultdict(dict)
        self.performance_history = defaultdict(list)
        
    def _initialize_configs(self) -> Dict[PipelineMode, PipelineConfig]:
        """Initialize pipeline configurations"""
        return {
            PipelineMode.STANDARD: PipelineConfig(
                mode=PipelineMode.STANDARD,
                stages=[
                    ProcessingStage.QUERY_ANALYSIS,
                    ProcessingStage.RETRIEVAL,
                    ProcessingStage.GENERATION,
                    ProcessingStage.POST_PROCESSING
                ],
                optimization=OptimizationStrategy.BALANCED,
                parallel_stages=[],
                stage_timeouts={
                    ProcessingStage.QUERY_ANALYSIS: 2000,
                    ProcessingStage.RETRIEVAL: 5000,
                    ProcessingStage.GENERATION: 10000,
                    ProcessingStage.POST_PROCESSING: 2000
                },
                retry_policy={"max_retries": 2, "backoff": 1000},
                cache_config={"ttl": 3600, "max_size": 1000}
            ),
            PipelineMode.CURATED: PipelineConfig(
                mode=PipelineMode.CURATED,
                stages=[
                    ProcessingStage.QUERY_ANALYSIS,
                    ProcessingStage.RETRIEVAL,
                    ProcessingStage.CURATION,
                    ProcessingStage.AUGMENTATION,
                    ProcessingStage.GENERATION,
                    ProcessingStage.POST_PROCESSING,
                    ProcessingStage.EVALUATION
                ],
                optimization=OptimizationStrategy.QUALITY_OPTIMIZED,
                parallel_stages=[
                    [ProcessingStage.RETRIEVAL, ProcessingStage.QUERY_ANALYSIS]
                ],
                stage_timeouts={
                    ProcessingStage.QUERY_ANALYSIS: 3000,
                    ProcessingStage.RETRIEVAL: 5000,
                    ProcessingStage.CURATION: 5000,
                    ProcessingStage.AUGMENTATION: 3000,
                    ProcessingStage.GENERATION: 15000,
                    ProcessingStage.POST_PROCESSING: 3000,
                    ProcessingStage.EVALUATION: 5000
                },
                retry_policy={"max_retries": 3, "backoff": 2000},
                cache_config={"ttl": 7200, "max_size": 2000}
            ),
            PipelineMode.HYBRID: PipelineConfig(
                mode=PipelineMode.HYBRID,
                stages=[
                    ProcessingStage.QUERY_ANALYSIS,
                    ProcessingStage.RETRIEVAL,
                    ProcessingStage.CURATION,
                    ProcessingStage.GENERATION,
                    ProcessingStage.POST_PROCESSING
                ],
                optimization=OptimizationStrategy.BALANCED,
                parallel_stages=[
                    [ProcessingStage.RETRIEVAL, ProcessingStage.CURATION]
                ],
                stage_timeouts={
                    ProcessingStage.QUERY_ANALYSIS: 2500,
                    ProcessingStage.RETRIEVAL: 5000,
                    ProcessingStage.CURATION: 4000,
                    ProcessingStage.GENERATION: 12000,
                    ProcessingStage.POST_PROCESSING: 2500
                },
                retry_policy={"max_retries": 2, "backoff": 1500},
                cache_config={"ttl": 5400, "max_size": 1500}
            ),
            PipelineMode.EXPERIMENTAL: PipelineConfig(
                mode=PipelineMode.EXPERIMENTAL,
                stages=[
                    ProcessingStage.QUERY_ANALYSIS,
                    ProcessingStage.RETRIEVAL,
                    ProcessingStage.CURATION,
                    ProcessingStage.AUGMENTATION,
                    ProcessingStage.GENERATION,
                    ProcessingStage.POST_PROCESSING,
                    ProcessingStage.EVALUATION
                ],
                optimization=OptimizationStrategy.QUALITY_OPTIMIZED,
                parallel_stages=[
                    [ProcessingStage.RETRIEVAL, ProcessingStage.QUERY_ANALYSIS],
                    [ProcessingStage.CURATION, ProcessingStage.AUGMENTATION]
                ],
                stage_timeouts={
                    ProcessingStage.QUERY_ANALYSIS: 4000,
                    ProcessingStage.RETRIEVAL: 6000,
                    ProcessingStage.CURATION: 6000,
                    ProcessingStage.AUGMENTATION: 4000,
                    ProcessingStage.GENERATION: 20000,
                    ProcessingStage.POST_PROCESSING: 4000,
                    ProcessingStage.EVALUATION: 6000
                },
                retry_policy={"max_retries": 3, "backoff": 2500},
                cache_config={"ttl": 10800, "max_size": 3000}
            )
        }
    
    async def execute_pipeline(
        self,
        request: RAGRequest
    ) -> RAGResponse:
        """Execute RAG pipeline with intelligent orchestration"""
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        pipeline_trace = []
        
        try:
            # Get pipeline configuration
            config = self.pipeline_configs[request.mode]
            
            # Apply optimization strategy
            config = self._apply_optimization(config, request.optimization)
            
            # Initialize pipeline state
            pipeline_state = {
                "request_id": request_id,
                "request": request,
                "config": config,
                "results": {},
                "errors": []
            }
            
            self.active_pipelines[request_id] = pipeline_state
            
            # Execute pipeline stages
            for stage in config.stages:
                stage_result = await self._execute_stage(
                    stage,
                    pipeline_state,
                    config.stage_timeouts.get(stage, 10000)
                )
                
                pipeline_state["results"][stage] = stage_result
                pipeline_trace.append(stage_result.dict())
                
                # Check for critical failures
                if stage_result.status == "failed" and stage in [
                    ProcessingStage.RETRIEVAL,
                    ProcessingStage.GENERATION
                ]:
                    raise Exception(f"Critical stage {stage} failed")
            
            # Generate final response
            answer = pipeline_state["results"][ProcessingStage.GENERATION].output
            sources = pipeline_state["results"].get(
                ProcessingStage.CURATION,
                pipeline_state["results"].get(ProcessingStage.RETRIEVAL, StageResult(
                    stage=ProcessingStage.RETRIEVAL,
                    status="skipped",
                    output=[],
                    metrics={},
                    duration_ms=0
                ))
            ).output
            
            # Get evaluation if enabled
            evaluation = None
            if request.enable_evaluation and ProcessingStage.EVALUATION in pipeline_state["results"]:
                evaluation = pipeline_state["results"][ProcessingStage.EVALUATION].output
            
            # Calculate metrics
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            metrics = self._calculate_pipeline_metrics(pipeline_state)
            
            # Store performance data
            self.performance_history[request.mode].append({
                "request_id": request_id,
                "processing_time": processing_time,
                "metrics": metrics,
                "timestamp": datetime.now()
            })
            
            return RAGResponse(
                request_id=request_id,
                query=request.query,
                answer=answer,
                mode=request.mode,
                sources=sources if isinstance(sources, list) else [],
                pipeline_trace=pipeline_trace,
                metrics=metrics,
                evaluation=evaluation,
                processing_time_ms=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Cleanup
            if request_id in self.active_pipelines:
                del self.active_pipelines[request_id]
    
    async def _execute_stage(
        self,
        stage: ProcessingStage,
        pipeline_state: Dict[str, Any],
        timeout: int
    ) -> StageResult:
        """Execute a single pipeline stage"""
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(stage, pipeline_state)
            if cache_key in self.stage_cache[stage]:
                cached_result = self.stage_cache[stage][cache_key]
                cached_result.duration_ms = 0  # Indicate cache hit
                return cached_result
            
            # Execute stage based on type
            if stage == ProcessingStage.QUERY_ANALYSIS:
                output = await self._analyze_query(pipeline_state["request"])
            elif stage == ProcessingStage.RETRIEVAL:
                output = await self._retrieve_documents(pipeline_state)
            elif stage == ProcessingStage.CURATION:
                output = await self._curate_content(pipeline_state)
            elif stage == ProcessingStage.AUGMENTATION:
                output = await self._augment_context(pipeline_state)
            elif stage == ProcessingStage.GENERATION:
                output = await self._generate_answer(pipeline_state)
            elif stage == ProcessingStage.POST_PROCESSING:
                output = await self._post_process(pipeline_state)
            elif stage == ProcessingStage.EVALUATION:
                output = await self._evaluate_response(pipeline_state)
            else:
                output = None
            
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = StageResult(
                stage=stage,
                status="success",
                output=output,
                metrics=self._get_stage_metrics(stage, output),
                duration_ms=duration
            )
            
            # Cache result
            self.stage_cache[stage][cache_key] = result
            
            return result
            
        except asyncio.TimeoutError:
            return StageResult(
                stage=stage,
                status="timeout",
                output=None,
                metrics={},
                duration_ms=timeout,
                errors=[f"Stage {stage} timed out after {timeout}ms"]
            )
        except Exception as e:
            logger.error(f"Stage {stage} failed: {e}")
            return StageResult(
                stage=stage,
                status="failed",
                output=None,
                metrics={},
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                errors=[str(e)]
            )
    
    async def _analyze_query(self, request: RAGRequest) -> QueryIntent:
        """Analyze query intent and complexity"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{AI_MODEL_URL}/api/v1/analyze_query",
                    json={"query": request.query, "context": request.user_context},
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                
                return QueryIntent(
                    intent_type=data.get("intent_type", "information_seeking"),
                    confidence=data.get("confidence", 0.8),
                    entities=data.get("entities", []),
                    complexity=data.get("complexity", "medium"),
                    requires_curation=data.get("requires_curation", True),
                    suggested_pipeline=PipelineMode(
                        data.get("suggested_pipeline", request.mode.value)
                    )
                )
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return QueryIntent(
                intent_type="unknown",
                confidence=0.5,
                entities=[],
                complexity="medium",
                requires_curation=True,
                suggested_pipeline=request.mode
            )
    
    async def _retrieve_documents(
        self,
        pipeline_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents"""
        request = pipeline_state["request"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{VECTOR_DB_URL}/api/v1/search",
                    json={
                        "query": request.query,
                        "top_k": request.max_chunks * 2,  # Oversample for curation
                        "user_context": request.user_context
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("results", [])
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []
    
    async def _curate_content(
        self,
        pipeline_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Curate retrieved content"""
        request = pipeline_state["request"]
        retrieved_docs = pipeline_state["results"].get(
            ProcessingStage.RETRIEVAL, 
            StageResult(stage=ProcessingStage.RETRIEVAL, status="", output=[], metrics={}, duration_ms=0)
        ).output
        
        if not retrieved_docs:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{CURATION_SERVICE_URL}/api/v1/curate",
                    json={
                        "query": request.query,
                        "user_context": request.user_context,
                        "strategy": "hybrid",
                        "max_results": request.max_chunks,
                        "quality_threshold": 0.6,
                        "diversity_weight": 0.3,
                        "personalization": True
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                curated = response.json().get("curated_items", [])
                
                # Convert to expected format
                return [
                    {
                        "id": item["id"],
                        "content": item["content"],
                        "source": item["source"],
                        "score": item["overall_score"],
                        "metadata": item["metadata"]
                    }
                    for item in curated
                ]
        except Exception as e:
            logger.error(f"Content curation failed: {e}")
            return retrieved_docs[:request.max_chunks]
    
    async def _augment_context(
        self,
        pipeline_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Augment context with additional information"""
        curated_content = pipeline_state["results"].get(
            ProcessingStage.CURATION,
            StageResult(stage=ProcessingStage.CURATION, status="", output=[], metrics={}, duration_ms=0)
        ).output
        
        # Simple augmentation - add summaries and key points
        augmented = {
            "original_content": curated_content,
            "summaries": [],
            "key_points": [],
            "relationships": []
        }
        
        for item in curated_content:
            # Would call AI service for actual summarization
            augmented["summaries"].append({
                "source": item.get("source"),
                "summary": item.get("content", "")[:200] + "..."
            })
        
        return augmented
    
    async def _generate_answer(
        self,
        pipeline_state: Dict[str, Any]
    ) -> str:
        """Generate answer using LLM"""
        request = pipeline_state["request"]
        
        # Get context from curation or retrieval
        context_data = pipeline_state["results"].get(
            ProcessingStage.AUGMENTATION,
            pipeline_state["results"].get(
                ProcessingStage.CURATION,
                pipeline_state["results"].get(ProcessingStage.RETRIEVAL)
            )
        ).output
        
        # Prepare context
        if isinstance(context_data, dict) and "original_content" in context_data:
            context = "\n\n".join([
                item.get("content", "") for item in context_data["original_content"]
            ])
        elif isinstance(context_data, list):
            context = "\n\n".join([
                item.get("content", "") for item in context_data
            ])
        else:
            context = ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{AI_MODEL_URL}/api/v1/generate",
                    json={
                        "query": request.query,
                        "context": context,
                        "temperature": request.temperature,
                        "max_tokens": 1000,
                        "user_context": request.user_context
                    },
                    timeout=20.0
                )
                response.raise_for_status()
                return response.json().get("answer", "Unable to generate answer")
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return f"I apologize, but I encountered an error generating the answer: {str(e)}"
    
    async def _post_process(
        self,
        pipeline_state: Dict[str, Any]
    ) -> str:
        """Post-process generated answer"""
        answer = pipeline_state["results"][ProcessingStage.GENERATION].output
        
        # Simple post-processing - clean up formatting
        if answer:
            answer = answer.strip()
            # Remove any potential prompt leakage
            if "Context:" in answer:
                answer = answer.split("Answer:")[-1].strip()
        
        return answer
    
    async def _evaluate_response(
        self,
        pipeline_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate generated response"""
        request = pipeline_state["request"]
        answer = pipeline_state["results"].get(
            ProcessingStage.POST_PROCESSING,
            pipeline_state["results"].get(ProcessingStage.GENERATION)
        ).output
        
        context_data = pipeline_state["results"].get(
            ProcessingStage.CURATION,
            pipeline_state["results"].get(ProcessingStage.RETRIEVAL)
        ).output
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{EVALUATION_URL}/api/v1/evaluate",
                    json={
                        "session_id": pipeline_state["request_id"],
                        "query": request.query,
                        "retrieved_chunks": context_data if isinstance(context_data, list) else [],
                        "generated_answer": answer,
                        "user_id": request.user_context.get("user_id", "default")
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"error": str(e)}
    
    def _apply_optimization(
        self,
        config: PipelineConfig,
        strategy: OptimizationStrategy
    ) -> PipelineConfig:
        """Apply optimization strategy to pipeline configuration"""
        if strategy == OptimizationStrategy.LATENCY_OPTIMIZED:
            # Reduce timeouts and skip non-critical stages
            for stage in config.stage_timeouts:
                config.stage_timeouts[stage] = int(config.stage_timeouts[stage] * 0.7)
            if ProcessingStage.EVALUATION in config.stages:
                config.stages.remove(ProcessingStage.EVALUATION)
        
        elif strategy == OptimizationStrategy.QUALITY_OPTIMIZED:
            # Increase timeouts and ensure all quality stages
            for stage in config.stage_timeouts:
                config.stage_timeouts[stage] = int(config.stage_timeouts[stage] * 1.5)
            if ProcessingStage.AUGMENTATION not in config.stages:
                idx = config.stages.index(ProcessingStage.GENERATION)
                config.stages.insert(idx, ProcessingStage.AUGMENTATION)
        
        elif strategy == OptimizationStrategy.COST_OPTIMIZED:
            # Minimize API calls and caching
            config.cache_config["ttl"] *= 2
            config.retry_policy["max_retries"] = 1
        
        return config
    
    def _get_cache_key(
        self,
        stage: ProcessingStage,
        pipeline_state: Dict[str, Any]
    ) -> str:
        """Generate cache key for stage"""
        request = pipeline_state["request"]
        key_parts = [
            stage.value,
            request.query,
            request.mode.value,
            str(request.max_chunks)
        ]
        return "|".join(key_parts)
    
    def _get_stage_metrics(
        self,
        stage: ProcessingStage,
        output: Any
    ) -> Dict[str, float]:
        """Get metrics for stage output"""
        metrics = {}
        
        if stage == ProcessingStage.RETRIEVAL and isinstance(output, list):
            metrics["documents_retrieved"] = len(output)
            metrics["avg_score"] = np.mean([
                item.get("score", 0) for item in output
            ]) if output else 0
        
        elif stage == ProcessingStage.CURATION and isinstance(output, list):
            metrics["documents_curated"] = len(output)
            if output and "overall_score" in output[0]:
                metrics["avg_curation_score"] = np.mean([
                    item.get("overall_score", 0) for item in output
                ])
        
        elif stage == ProcessingStage.GENERATION and isinstance(output, str):
            metrics["answer_length"] = len(output)
            metrics["answer_words"] = len(output.split())
        
        return metrics
    
    def _calculate_pipeline_metrics(
        self,
        pipeline_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall pipeline metrics"""
        metrics = {
            "stages_completed": len(pipeline_state["results"]),
            "stages_failed": sum(
                1 for r in pipeline_state["results"].values()
                if r.status == "failed"
            ),
            "total_duration_ms": sum(
                r.duration_ms for r in pipeline_state["results"].values()
            ),
            "cache_hits": sum(
                1 for r in pipeline_state["results"].values()
                if r.duration_ms == 0
            )
        }
        
        # Add stage-specific metrics
        for stage, result in pipeline_state["results"].items():
            if result.metrics:
                for key, value in result.metrics.items():
                    metrics[f"{stage.value}_{key}"] = value
        
        return metrics

# Initialize orchestrator
orchestrator = PipelineOrchestrator()

# API Endpoints
@app.post("/api/v1/process", response_model=RAGResponse)
async def process_rag_request(request: RAGRequest):
    """Process RAG request through orchestrated pipeline"""
    return await orchestrator.execute_pipeline(request)

@app.websocket("/api/v1/stream")
async def stream_rag_response(websocket: WebSocket):
    """Stream RAG response in real-time"""
    await websocket.accept()
    
    try:
        while True:
            # Receive request
            data = await websocket.receive_json()
            request = RAGRequest(**data)
            
            # Execute pipeline with streaming
            pipeline_id = str(uuid.uuid4())
            
            # Send updates as pipeline progresses
            async for update in stream_pipeline_updates(pipeline_id, request):
                await websocket.send_json(update)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

async def stream_pipeline_updates(
    pipeline_id: str,
    request: RAGRequest
) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream pipeline updates"""
    # Simplified streaming - would integrate with actual pipeline
    stages = ["retrieval", "curation", "generation", "complete"]
    
    for i, stage in enumerate(stages):
        await asyncio.sleep(1)  # Simulate processing
        yield {
            "type": "progress",
            "stage": stage,
            "progress": (i + 1) / len(stages),
            "message": f"Processing {stage}..."
        }
    
    # Final response
    yield {
        "type": "complete",
        "answer": "This is a streamed response",
        "sources": []
    }

@app.get("/api/v1/pipelines")
async def get_pipeline_configs():
    """Get available pipeline configurations"""
    return {
        "pipelines": [
            {
                "mode": mode.value,
                "stages": [s.value for s in config.stages],
                "optimization": config.optimization.value,
                "description": {
                    PipelineMode.STANDARD: "Basic RAG pipeline",
                    PipelineMode.CURATED: "AI-curated content pipeline",
                    PipelineMode.HYBRID: "Balanced curation and speed",
                    PipelineMode.EXPERIMENTAL: "Advanced experimental features"
                }.get(mode)
            }
            for mode, config in orchestrator.pipeline_configs.items()
        ]
    }

@app.get("/api/v1/performance")
async def get_performance_metrics():
    """Get pipeline performance metrics"""
    metrics = {}
    
    for mode, history in orchestrator.performance_history.items():
        if history:
            recent = history[-100:]  # Last 100 requests
            metrics[mode.value] = {
                "requests_processed": len(recent),
                "avg_processing_time_ms": np.mean([
                    h["processing_time"] for h in recent
                ]),
                "p95_processing_time_ms": np.percentile([
                    h["processing_time"] for h in recent
                ], 95),
                "success_rate": sum(
                    1 for h in recent 
                    if h["metrics"].get("stages_failed", 0) == 0
                ) / len(recent)
            }
    
    return metrics

@app.post("/api/v1/optimize")
async def optimize_pipeline(
    mode: PipelineMode,
    target_metric: str = "latency",
    constraints: Dict[str, Any] = None
):
    """Optimize pipeline configuration"""
    # Simplified optimization - would use ML in production
    config = orchestrator.pipeline_configs[mode]
    
    if target_metric == "latency":
        config.optimization = OptimizationStrategy.LATENCY_OPTIMIZED
    elif target_metric == "quality":
        config.optimization = OptimizationStrategy.QUALITY_OPTIMIZED
    elif target_metric == "cost":
        config.optimization = OptimizationStrategy.COST_OPTIMIZED
    
    orchestrator.pipeline_configs[mode] = config
    
    return {
        "status": "optimized",
        "mode": mode.value,
        "optimization": config.optimization.value
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rag-orchestrator",
        "active_pipelines": len(orchestrator.active_pipelines),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)