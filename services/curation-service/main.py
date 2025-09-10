"""
AI-Curated RAG Pipeline Curation Service
Provides intelligent content curation, quality assessment, and recommendation
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np
import asyncio
import httpx
import logging
import json
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Curation Service",
    description="Intelligent content curation for RAG pipeline",
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
VECTOR_DB_URL = "http://vector-db-service:8003"
AI_MODEL_URL = "http://ai-model-service:8007"
ORCHESTRATOR_URL = "http://rag-orchestrator:8008"
CACHE_TTL = 3600  # 1 hour

# Enums
class CurationStrategy(str, Enum):
    RELEVANCE_BASED = "relevance_based"
    QUALITY_BASED = "quality_based"
    DIVERSITY_BASED = "diversity_based"
    TEMPORAL_BASED = "temporal_based"
    HYBRID = "hybrid"

class ContentQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

# Models
class CurationRequest(BaseModel):
    query: str
    user_context: Dict[str, Any] = Field(default_factory=dict)
    strategy: CurationStrategy = CurationStrategy.HYBRID
    max_results: int = Field(default=10, ge=1, le=100)
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    diversity_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    personalization: bool = True
    filters: Dict[str, Any] = Field(default_factory=dict)

class CuratedContent(BaseModel):
    id: str
    content: str
    source: str
    relevance_score: float
    quality_score: float
    diversity_score: float
    temporal_score: float
    overall_score: float
    quality_label: ContentQuality
    metadata: Dict[str, Any]
    curation_reason: str
    recommendations: List[str]

class CurationResponse(BaseModel):
    request_id: str
    query: str
    strategy: CurationStrategy
    curated_items: List[CuratedContent]
    total_candidates: int
    curation_metrics: Dict[str, float]
    processing_time_ms: int
    timestamp: datetime

class QualityAssessment(BaseModel):
    content_id: str
    readability_score: float
    completeness_score: float
    accuracy_score: float
    coherence_score: float
    factuality_score: float
    overall_quality: float
    quality_label: ContentQuality
    issues: List[str]
    suggestions: List[str]

class PersonalizationProfile(BaseModel):
    user_id: str
    preferences: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    expertise_level: str
    language_preference: str
    content_type_preference: List[str]

# Curation Engine
class CurationEngine:
    def __init__(self):
        self.cache = {}
        self.quality_models = {}
        self.user_profiles = {}
        
    async def curate_content(
        self, 
        request: CurationRequest
    ) -> CurationResponse:
        """Main curation pipeline"""
        start_time = datetime.now()
        request_id = self._generate_request_id(request)
        
        # Step 1: Retrieve candidate content
        candidates = await self._retrieve_candidates(request)
        
        # Step 2: Assess quality
        quality_assessments = await self._assess_quality_batch(candidates)
        
        # Step 3: Apply curation strategy
        curated_items = await self._apply_curation_strategy(
            candidates,
            quality_assessments,
            request
        )
        
        # Step 4: Personalize if requested
        if request.personalization:
            curated_items = await self._personalize_content(
                curated_items,
                request.user_context
            )
        
        # Step 5: Generate recommendations
        curated_items = await self._generate_recommendations(curated_items)
        
        # Calculate metrics
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        curation_metrics = self._calculate_curation_metrics(curated_items)
        
        return CurationResponse(
            request_id=request_id,
            query=request.query,
            strategy=request.strategy,
            curated_items=curated_items[:request.max_results],
            total_candidates=len(candidates),
            curation_metrics=curation_metrics,
            processing_time_ms=processing_time,
            timestamp=datetime.now()
        )
    
    async def _retrieve_candidates(
        self, 
        request: CurationRequest
    ) -> List[Dict[str, Any]]:
        """Retrieve candidate content from vector DB"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{VECTOR_DB_URL}/api/v1/search",
                    json={
                        "query": request.query,
                        "top_k": request.max_results * 5,  # Oversample for curation
                        "filters": request.filters,
                        "user_context": request.user_context
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("results", [])
        except Exception as e:
            logger.error(f"Failed to retrieve candidates: {e}")
            return []
    
    async def _assess_quality_batch(
        self,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, QualityAssessment]:
        """Assess quality of multiple content items"""
        assessments = {}
        
        # Batch process for efficiency
        tasks = []
        for candidate in candidates:
            tasks.append(self._assess_quality(candidate))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for candidate, result in zip(candidates, results):
            if not isinstance(result, Exception):
                assessments[candidate["id"]] = result
        
        return assessments
    
    async def _assess_quality(
        self,
        content: Dict[str, Any]
    ) -> QualityAssessment:
        """Assess quality of a single content item"""
        content_id = content.get("id", "unknown")
        text = content.get("content", "")
        
        # Calculate quality scores
        readability = self._calculate_readability(text)
        completeness = self._calculate_completeness(text, content.get("metadata", {}))
        coherence = self._calculate_coherence(text)
        
        # Get AI-based quality assessment
        ai_assessment = await self._get_ai_quality_assessment(text)
        
        # Combine scores
        overall_quality = np.mean([
            readability,
            completeness,
            coherence,
            ai_assessment.get("accuracy", 0.5),
            ai_assessment.get("factuality", 0.5)
        ])
        
        # Determine quality label
        if overall_quality >= 0.85:
            quality_label = ContentQuality.EXCELLENT
        elif overall_quality >= 0.7:
            quality_label = ContentQuality.GOOD
        elif overall_quality >= 0.5:
            quality_label = ContentQuality.FAIR
        else:
            quality_label = ContentQuality.POOR
        
        return QualityAssessment(
            content_id=content_id,
            readability_score=readability,
            completeness_score=completeness,
            accuracy_score=ai_assessment.get("accuracy", 0.5),
            coherence_score=coherence,
            factuality_score=ai_assessment.get("factuality", 0.5),
            overall_quality=overall_quality,
            quality_label=quality_label,
            issues=ai_assessment.get("issues", []),
            suggestions=ai_assessment.get("suggestions", [])
        )
    
    async def _apply_curation_strategy(
        self,
        candidates: List[Dict[str, Any]],
        quality_assessments: Dict[str, QualityAssessment],
        request: CurationRequest
    ) -> List[CuratedContent]:
        """Apply selected curation strategy"""
        curated_items = []
        
        for candidate in candidates:
            content_id = candidate.get("id")
            quality = quality_assessments.get(content_id)
            
            if not quality or quality.overall_quality < request.quality_threshold:
                continue
            
            # Calculate strategy-specific scores
            relevance_score = candidate.get("score", 0.0)
            quality_score = quality.overall_quality
            diversity_score = self._calculate_diversity_score(
                candidate, 
                curated_items
            )
            temporal_score = self._calculate_temporal_score(candidate)
            
            # Calculate overall score based on strategy
            if request.strategy == CurationStrategy.RELEVANCE_BASED:
                overall_score = relevance_score
                curation_reason = "High relevance to query"
            elif request.strategy == CurationStrategy.QUALITY_BASED:
                overall_score = quality_score
                curation_reason = "High content quality"
            elif request.strategy == CurationStrategy.DIVERSITY_BASED:
                overall_score = diversity_score
                curation_reason = "Adds diversity to results"
            elif request.strategy == CurationStrategy.TEMPORAL_BASED:
                overall_score = temporal_score
                curation_reason = "Recent and timely content"
            else:  # HYBRID
                overall_score = (
                    relevance_score * 0.4 +
                    quality_score * 0.3 +
                    diversity_score * request.diversity_weight +
                    temporal_score * (0.3 - request.diversity_weight)
                )
                curation_reason = "Balanced relevance, quality, and diversity"
            
            curated_items.append(CuratedContent(
                id=content_id,
                content=candidate.get("content", ""),
                source=candidate.get("source", "unknown"),
                relevance_score=relevance_score,
                quality_score=quality_score,
                diversity_score=diversity_score,
                temporal_score=temporal_score,
                overall_score=overall_score,
                quality_label=quality.quality_label,
                metadata=candidate.get("metadata", {}),
                curation_reason=curation_reason,
                recommendations=[]
            ))
        
        # Sort by overall score
        curated_items.sort(key=lambda x: x.overall_score, reverse=True)
        
        return curated_items
    
    async def _personalize_content(
        self,
        items: List[CuratedContent],
        user_context: Dict[str, Any]
    ) -> List[CuratedContent]:
        """Personalize content based on user profile"""
        user_id = user_context.get("user_id")
        if not user_id:
            return items
        
        # Get or create user profile
        profile = self.user_profiles.get(user_id)
        if not profile:
            profile = await self._create_user_profile(user_context)
            self.user_profiles[user_id] = profile
        
        # Adjust scores based on personalization
        for item in items:
            # Boost score for preferred content types
            if item.metadata.get("type") in profile.get("content_type_preference", []):
                item.overall_score *= 1.2
            
            # Adjust based on expertise level
            content_level = item.metadata.get("difficulty", "medium")
            user_level = profile.get("expertise_level", "intermediate")
            if self._match_expertise_level(content_level, user_level):
                item.overall_score *= 1.1
        
        # Re-sort after personalization
        items.sort(key=lambda x: x.overall_score, reverse=True)
        
        return items
    
    async def _generate_recommendations(
        self,
        items: List[CuratedContent]
    ) -> List[CuratedContent]:
        """Generate recommendations for each curated item"""
        for item in items:
            recommendations = []
            
            # Quality-based recommendations
            if item.quality_score < 0.6:
                recommendations.append("Consider cross-referencing with additional sources")
            elif item.quality_score > 0.85:
                recommendations.append("High-quality content recommended for detailed study")
            
            # Temporal recommendations
            if item.temporal_score < 0.5:
                recommendations.append("Content may be outdated, check for recent updates")
            
            # Diversity recommendations
            if item.diversity_score > 0.8:
                recommendations.append("Provides unique perspective on the topic")
            
            item.recommendations = recommendations
        
        return items
    
    async def _get_ai_quality_assessment(
        self,
        text: str
    ) -> Dict[str, Any]:
        """Get AI-based quality assessment"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{AI_MODEL_URL}/api/v1/assess_quality",
                    json={"text": text},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"AI quality assessment failed: {e}")
            return {
                "accuracy": 0.5,
                "factuality": 0.5,
                "issues": [],
                "suggestions": []
            }
    
    async def _create_user_profile(
        self,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create user profile from context"""
        return {
            "user_id": user_context.get("user_id"),
            "preferences": user_context.get("preferences", {}),
            "interaction_history": [],
            "expertise_level": user_context.get("expertise_level", "intermediate"),
            "language_preference": user_context.get("language", "en"),
            "content_type_preference": user_context.get("content_types", ["article", "paper"])
        }
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified)"""
        if not text:
            return 0.0
        
        # Simple readability metrics
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        if sentences == 0:
            return 0.5
        
        avg_words_per_sentence = len(words) / sentences
        
        # Normalize to 0-1 (ideal is 15-20 words per sentence)
        if 15 <= avg_words_per_sentence <= 20:
            return 1.0
        elif avg_words_per_sentence < 15:
            return avg_words_per_sentence / 15
        else:
            return max(0.3, 1.0 - (avg_words_per_sentence - 20) / 30)
    
    def _calculate_completeness(
        self, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate content completeness score"""
        score = 0.5  # Base score
        
        # Check for various content elements
        if len(text) > 500:
            score += 0.2
        if metadata.get("has_references"):
            score += 0.1
        if metadata.get("has_examples"):
            score += 0.1
        if metadata.get("has_summary"):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_coherence(self, text: str) -> float:
        """Calculate text coherence score (simplified)"""
        if not text:
            return 0.0
        
        # Simple coherence check based on paragraph structure
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            return min(1.0, 0.5 + len(paragraphs) * 0.1)
        return 0.7
    
    def _calculate_diversity_score(
        self,
        candidate: Dict[str, Any],
        existing_items: List[CuratedContent]
    ) -> float:
        """Calculate diversity score compared to existing items"""
        if not existing_items:
            return 1.0
        
        # Simple diversity based on source and topic
        candidate_source = candidate.get("source", "")
        candidate_topics = set(candidate.get("metadata", {}).get("topics", []))
        
        similarity_scores = []
        for item in existing_items:
            source_match = 1.0 if item.source == candidate_source else 0.0
            
            item_topics = set(item.metadata.get("topics", []))
            topic_overlap = len(candidate_topics & item_topics) / max(
                len(candidate_topics | item_topics), 1
            )
            
            similarity = (source_match * 0.3 + topic_overlap * 0.7)
            similarity_scores.append(similarity)
        
        # Diversity is inverse of average similarity
        avg_similarity = np.mean(similarity_scores)
        return 1.0 - avg_similarity
    
    def _calculate_temporal_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate temporal relevance score"""
        metadata = candidate.get("metadata", {})
        
        # Get content timestamp
        timestamp_str = metadata.get("created_at", metadata.get("updated_at"))
        if not timestamp_str:
            return 0.5  # Neutral score if no timestamp
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age_days = (datetime.now() - timestamp.replace(tzinfo=None)).days
            
            # Exponential decay over time
            # Content from today = 1.0, 30 days old = 0.5, 90 days old = 0.25
            return max(0.1, np.exp(-age_days / 30))
        except:
            return 0.5
    
    def _match_expertise_level(
        self, 
        content_level: str, 
        user_level: str
    ) -> bool:
        """Check if content level matches user expertise"""
        level_map = {
            "beginner": 1,
            "intermediate": 2,
            "advanced": 3,
            "expert": 4
        }
        
        content_val = level_map.get(content_level, 2)
        user_val = level_map.get(user_level, 2)
        
        # Content should be at or slightly above user level
        return user_val <= content_val <= user_val + 1
    
    def _calculate_curation_metrics(
        self,
        items: List[CuratedContent]
    ) -> Dict[str, float]:
        """Calculate overall curation metrics"""
        if not items:
            return {
                "avg_relevance": 0.0,
                "avg_quality": 0.0,
                "avg_diversity": 0.0,
                "coverage": 0.0
            }
        
        return {
            "avg_relevance": np.mean([item.relevance_score for item in items]),
            "avg_quality": np.mean([item.quality_score for item in items]),
            "avg_diversity": np.mean([item.diversity_score for item in items]),
            "coverage": len(set(item.source for item in items)) / len(items)
        }
    
    def _generate_request_id(self, request: CurationRequest) -> str:
        """Generate unique request ID"""
        content = f"{request.query}_{request.strategy}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

# Initialize curation engine
curation_engine = CurationEngine()

# API Endpoints
@app.post("/api/v1/curate", response_model=CurationResponse)
async def curate_content(request: CurationRequest):
    """Curate content based on query and strategy"""
    try:
        response = await curation_engine.curate_content(request)
        return response
    except Exception as e:
        logger.error(f"Curation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/assess_quality", response_model=QualityAssessment)
async def assess_quality(content: Dict[str, Any]):
    """Assess quality of a single content item"""
    try:
        assessment = await curation_engine._assess_quality(content)
        return assessment
    except Exception as e:
        logger.error(f"Quality assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/strategies")
async def get_curation_strategies():
    """Get available curation strategies"""
    return {
        "strategies": [
            {
                "name": strategy.value,
                "description": {
                    CurationStrategy.RELEVANCE_BASED: "Prioritize content relevance to query",
                    CurationStrategy.QUALITY_BASED: "Prioritize high-quality content",
                    CurationStrategy.DIVERSITY_BASED: "Maximize content diversity",
                    CurationStrategy.TEMPORAL_BASED: "Prioritize recent content",
                    CurationStrategy.HYBRID: "Balance all factors"
                }.get(strategy)
            }
            for strategy in CurationStrategy
        ]
    }

@app.post("/api/v1/feedback")
async def submit_feedback(
    content_id: str,
    rating: int = Field(ge=1, le=5),
    feedback: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Submit feedback on curated content"""
    # Store feedback for improving curation
    return {
        "status": "success",
        "message": "Feedback recorded",
        "content_id": content_id
    }

@app.get("/api/v1/metrics")
async def get_curation_metrics():
    """Get curation service metrics"""
    return {
        "total_requests": 1000,  # Would be from database
        "avg_processing_time_ms": 250,
        "cache_hit_rate": 0.65,
        "avg_quality_score": 0.78,
        "strategies_usage": {
            "hybrid": 0.45,
            "relevance_based": 0.25,
            "quality_based": 0.20,
            "diversity_based": 0.05,
            "temporal_based": 0.05
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "curation-service",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)