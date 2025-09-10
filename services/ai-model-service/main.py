"""
AI Model Service for RAG Pipeline
Provides multi-model AI capabilities with intelligent model selection and optimization
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio
import httpx
import logging
import json
import numpy as np
from enum import Enum
import hashlib
import re
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Model Service",
    description="Multi-model AI service for curated RAG pipeline",
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
OPENAI_API_URL = "https://api.openai.com/v1"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1"
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1"
LOCAL_MODEL_URL = "http://ollama:11434"

# Model configurations
MODEL_CONFIGS = {
    "gpt-4": {
        "provider": "openai",
        "max_tokens": 4096,
        "temperature_range": (0.0, 2.0),
        "capabilities": ["general", "reasoning", "coding", "analysis"],
        "cost_per_1k_tokens": 0.03,
        "latency_ms": 2000
    },
    "gpt-3.5-turbo": {
        "provider": "openai",
        "max_tokens": 4096,
        "temperature_range": (0.0, 2.0),
        "capabilities": ["general", "summarization"],
        "cost_per_1k_tokens": 0.002,
        "latency_ms": 1000
    },
    "claude-3-opus": {
        "provider": "anthropic",
        "max_tokens": 4096,
        "temperature_range": (0.0, 1.0),
        "capabilities": ["general", "reasoning", "analysis", "creative"],
        "cost_per_1k_tokens": 0.015,
        "latency_ms": 2500
    },
    "claude-3-sonnet": {
        "provider": "anthropic",
        "max_tokens": 4096,
        "temperature_range": (0.0, 1.0),
        "capabilities": ["general", "coding", "analysis"],
        "cost_per_1k_tokens": 0.003,
        "latency_ms": 1500
    },
    "gemini-pro": {
        "provider": "google",
        "max_tokens": 2048,
        "temperature_range": (0.0, 1.0),
        "capabilities": ["general", "multimodal"],
        "cost_per_1k_tokens": 0.001,
        "latency_ms": 1200
    },
    "llama-3": {
        "provider": "local",
        "max_tokens": 2048,
        "temperature_range": (0.0, 1.0),
        "capabilities": ["general", "local"],
        "cost_per_1k_tokens": 0.0,
        "latency_ms": 500
    }
}

# Enums
class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"

class TaskType(str, Enum):
    GENERATION = "generation"
    SUMMARIZATION = "summarization"
    ANALYSIS = "analysis"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    TRANSLATION = "translation"

class ModelSelectionStrategy(str, Enum):
    QUALITY_FIRST = "quality_first"
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"
    BALANCED = "balanced"
    CAPABILITY_MATCH = "capability_match"

# Models
class GenerationRequest(BaseModel):
    query: str
    context: Optional[str] = ""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4096)
    model: Optional[str] = None
    task_type: TaskType = TaskType.GENERATION
    selection_strategy: ModelSelectionStrategy = ModelSelectionStrategy.BALANCED
    user_context: Dict[str, Any] = Field(default_factory=dict)
    system_prompt: Optional[str] = None
    examples: List[Dict[str, str]] = Field(default_factory=list)

class GenerationResponse(BaseModel):
    answer: str
    model_used: str
    provider: str
    tokens_used: int
    cost_estimate: float
    latency_ms: int
    confidence: float
    metadata: Dict[str, Any]

class QueryAnalysisRequest(BaseModel):
    query: str
    context: Dict[str, Any] = Field(default_factory=dict)

class QueryAnalysisResponse(BaseModel):
    intent_type: str
    confidence: float
    entities: List[Dict[str, Any]]
    complexity: str
    requires_curation: bool
    suggested_pipeline: str
    key_topics: List[str]
    language: str

class QualityAssessmentRequest(BaseModel):
    text: str
    criteria: List[str] = Field(default_factory=lambda: ["accuracy", "completeness", "coherence"])

class QualityAssessmentResponse(BaseModel):
    accuracy: float
    factuality: float
    completeness: float
    coherence: float
    readability: float
    issues: List[str]
    suggestions: List[str]
    overall_score: float

class EmbeddingRequest(BaseModel):
    texts: List[str]
    model: str = "text-embedding-3-small"
    dimensions: int = Field(default=384, ge=1, le=3072)

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model_used: str
    dimensions: int
    tokens_used: int

# AI Model Manager
class AIModelManager:
    def __init__(self):
        self.model_cache = {}
        self.performance_stats = defaultdict(list)
        self.model_availability = {}
        self.prompt_templates = self._load_prompt_templates()
        
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates for different tasks"""
        return {
            "generation": """Context: {context}

Question: {query}

Please provide a comprehensive and accurate answer based on the given context. If the context doesn't contain enough information, indicate what's missing.""",
            
            "summarization": """Text to summarize: {context}

Provide a concise summary that captures the main points and key information.""",
            
            "analysis": """Query: {query}

Analyze the following aspects:
1. Intent and purpose
2. Key entities and concepts
3. Complexity and requirements
4. Suggested approach

Analysis:""",
            
            "quality_assessment": """Text to assess: {text}

Evaluate the text based on:
1. Accuracy and factuality
2. Completeness of information
3. Coherence and structure
4. Readability and clarity

Provide scores (0-1) and specific feedback."""
        }
    
    async def generate(
        self,
        request: GenerationRequest
    ) -> GenerationResponse:
        """Generate response using optimal model"""
        start_time = datetime.now()
        
        # Select optimal model
        selected_model = await self._select_model(request)
        
        # Prepare prompt
        prompt = self._prepare_prompt(request)
        
        # Generate response
        try:
            if MODEL_CONFIGS[selected_model]["provider"] == "openai":
                response = await self._generate_openai(selected_model, prompt, request)
            elif MODEL_CONFIGS[selected_model]["provider"] == "anthropic":
                response = await self._generate_anthropic(selected_model, prompt, request)
            elif MODEL_CONFIGS[selected_model]["provider"] == "google":
                response = await self._generate_google(selected_model, prompt, request)
            else:  # local
                response = await self._generate_local(selected_model, prompt, request)
            
            # Calculate metrics
            latency = int((datetime.now() - start_time).total_seconds() * 1000)
            tokens_used = self._estimate_tokens(prompt + response)
            cost = self._calculate_cost(selected_model, tokens_used)
            confidence = await self._assess_confidence(response, request)
            
            # Update performance stats
            self.performance_stats[selected_model].append({
                "latency": latency,
                "tokens": tokens_used,
                "confidence": confidence,
                "timestamp": datetime.now()
            })
            
            return GenerationResponse(
                answer=response,
                model_used=selected_model,
                provider=MODEL_CONFIGS[selected_model]["provider"],
                tokens_used=tokens_used,
                cost_estimate=cost,
                latency_ms=latency,
                confidence=confidence,
                metadata={
                    "task_type": request.task_type.value,
                    "strategy": request.selection_strategy.value
                }
            )
            
        except Exception as e:
            logger.error(f"Generation failed with {selected_model}: {e}")
            # Try fallback model
            if selected_model != "llama-3":
                request.model = "llama-3"
                return await self.generate(request)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def analyze_query(
        self,
        request: QueryAnalysisRequest
    ) -> QueryAnalysisResponse:
        """Analyze query intent and characteristics"""
        query = request.query
        
        # Simple rule-based analysis (would use NLP model in production)
        intent_type = self._detect_intent(query)
        entities = self._extract_entities(query)
        complexity = self._assess_complexity(query)
        key_topics = self._extract_topics(query)
        
        # Determine if curation is needed
        requires_curation = (
            complexity in ["high", "very_high"] or
            intent_type in ["research", "comparison", "analysis"]
        )
        
        # Suggest pipeline based on analysis
        if requires_curation and complexity == "very_high":
            suggested_pipeline = "experimental"
        elif requires_curation:
            suggested_pipeline = "curated"
        elif intent_type == "simple_qa":
            suggested_pipeline = "standard"
        else:
            suggested_pipeline = "hybrid"
        
        return QueryAnalysisResponse(
            intent_type=intent_type,
            confidence=0.85,
            entities=entities,
            complexity=complexity,
            requires_curation=requires_curation,
            suggested_pipeline=suggested_pipeline,
            key_topics=key_topics,
            language=self._detect_language(query)
        )
    
    async def assess_quality(
        self,
        request: QualityAssessmentRequest
    ) -> QualityAssessmentResponse:
        """Assess content quality"""
        text = request.text
        
        # Calculate various quality metrics
        accuracy = await self._assess_accuracy(text)
        factuality = await self._assess_factuality(text)
        completeness = self._assess_completeness(text)
        coherence = self._assess_coherence(text)
        readability = self._calculate_readability(text)
        
        # Identify issues and suggestions
        issues = []
        suggestions = []
        
        if readability < 0.6:
            issues.append("Low readability score")
            suggestions.append("Simplify sentence structure")
        
        if coherence < 0.7:
            issues.append("Poor text coherence")
            suggestions.append("Improve logical flow between paragraphs")
        
        if completeness < 0.7:
            issues.append("Incomplete information")
            suggestions.append("Add more details or examples")
        
        overall_score = np.mean([
            accuracy, factuality, completeness, 
            coherence, readability
        ])
        
        return QualityAssessmentResponse(
            accuracy=accuracy,
            factuality=factuality,
            completeness=completeness,
            coherence=coherence,
            readability=readability,
            issues=issues,
            suggestions=suggestions,
            overall_score=overall_score
        )
    
    async def generate_embeddings(
        self,
        request: EmbeddingRequest
    ) -> EmbeddingResponse:
        """Generate embeddings for texts"""
        # Simplified embedding generation
        # In production, would use actual embedding models
        
        embeddings = []
        for text in request.texts:
            # Generate pseudo-embedding based on text hash
            hash_val = hashlib.md5(text.encode()).digest()
            embedding = [
                float(b) / 255.0 for b in hash_val
            ] * (request.dimensions // 16)
            embedding = embedding[:request.dimensions]
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = (np.array(embedding) / norm).tolist()
            
            embeddings.append(embedding)
        
        tokens_used = sum(self._estimate_tokens(text) for text in request.texts)
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model_used=request.model,
            dimensions=request.dimensions,
            tokens_used=tokens_used
        )
    
    async def _select_model(
        self,
        request: GenerationRequest
    ) -> str:
        """Select optimal model based on strategy"""
        if request.model:
            return request.model
        
        strategy = request.selection_strategy
        task_type = request.task_type
        
        # Filter models by capability
        capable_models = []
        for model, config in MODEL_CONFIGS.items():
            if task_type.value in config["capabilities"] or "general" in config["capabilities"]:
                capable_models.append(model)
        
        if not capable_models:
            return "gpt-3.5-turbo"  # Default fallback
        
        # Apply selection strategy
        if strategy == ModelSelectionStrategy.QUALITY_FIRST:
            # Prefer high-quality models
            quality_order = ["gpt-4", "claude-3-opus", "claude-3-sonnet", "gemini-pro", "gpt-3.5-turbo", "llama-3"]
            for model in quality_order:
                if model in capable_models:
                    return model
        
        elif strategy == ModelSelectionStrategy.COST_OPTIMIZED:
            # Sort by cost
            capable_models.sort(key=lambda m: MODEL_CONFIGS[m]["cost_per_1k_tokens"])
            return capable_models[0]
        
        elif strategy == ModelSelectionStrategy.LATENCY_OPTIMIZED:
            # Sort by latency
            capable_models.sort(key=lambda m: MODEL_CONFIGS[m]["latency_ms"])
            return capable_models[0]
        
        elif strategy == ModelSelectionStrategy.BALANCED:
            # Score based on multiple factors
            scores = {}
            for model in capable_models:
                config = MODEL_CONFIGS[model]
                # Normalize and weight factors
                cost_score = 1.0 - (config["cost_per_1k_tokens"] / 0.03)  # Normalize to max cost
                latency_score = 1.0 - (config["latency_ms"] / 3000)  # Normalize to max latency
                quality_score = {"gpt-4": 1.0, "claude-3-opus": 0.95, 
                                "claude-3-sonnet": 0.85, "gemini-pro": 0.75,
                                "gpt-3.5-turbo": 0.7, "llama-3": 0.6}.get(model, 0.5)
                
                scores[model] = (quality_score * 0.4 + cost_score * 0.3 + latency_score * 0.3)
            
            return max(scores, key=scores.get)
        
        else:  # CAPABILITY_MATCH
            # Match based on specific capabilities
            return capable_models[0]
    
    def _prepare_prompt(
        self,
        request: GenerationRequest
    ) -> str:
        """Prepare prompt based on task type"""
        template = self.prompt_templates.get(
            request.task_type.value,
            self.prompt_templates["generation"]
        )
        
        # Add system prompt if provided
        if request.system_prompt:
            prompt = f"{request.system_prompt}\n\n"
        else:
            prompt = ""
        
        # Add examples if provided
        if request.examples:
            prompt += "Examples:\n"
            for example in request.examples:
                prompt += f"Q: {example.get('question', '')}\n"
                prompt += f"A: {example.get('answer', '')}\n\n"
        
        # Format main prompt
        prompt += template.format(
            query=request.query,
            context=request.context or "No specific context provided."
        )
        
        return prompt
    
    async def _generate_openai(
        self,
        model: str,
        prompt: str,
        request: GenerationRequest
    ) -> str:
        """Generate using OpenAI model"""
        # Simulated OpenAI response
        # In production, would make actual API call
        return f"OpenAI {model} response: Based on the context provided, {request.query[:50]}..."
    
    async def _generate_anthropic(
        self,
        model: str,
        prompt: str,
        request: GenerationRequest
    ) -> str:
        """Generate using Anthropic model"""
        # Simulated Anthropic response
        return f"Claude {model} response: Analyzing the context, {request.query[:50]}..."
    
    async def _generate_google(
        self,
        model: str,
        prompt: str,
        request: GenerationRequest
    ) -> str:
        """Generate using Google model"""
        # Simulated Google response
        return f"Gemini response: From the information given, {request.query[:50]}..."
    
    async def _generate_local(
        self,
        model: str,
        prompt: str,
        request: GenerationRequest
    ) -> str:
        """Generate using local model"""
        # Simulated local model response
        return f"Local LLM response: Based on analysis, {request.query[:50]}..."
    
    async def _assess_confidence(
        self,
        response: str,
        request: GenerationRequest
    ) -> float:
        """Assess confidence in generated response"""
        # Simple heuristic-based confidence
        confidence = 0.5
        
        # Check response length
        if len(response) > 100:
            confidence += 0.2
        
        # Check for uncertainty markers
        uncertainty_phrases = ["might be", "possibly", "unclear", "not sure", "approximately"]
        for phrase in uncertainty_phrases:
            if phrase.lower() in response.lower():
                confidence -= 0.1
        
        # Check for specificity
        if any(char.isdigit() for char in response):
            confidence += 0.1
        
        # Ensure confidence is in valid range
        return max(0.1, min(1.0, confidence))
    
    def _detect_intent(self, query: str) -> str:
        """Detect query intent"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["what", "who", "where", "when"]):
            return "information_seeking"
        elif any(word in query_lower for word in ["how", "guide", "tutorial"]):
            return "instructional"
        elif any(word in query_lower for word in ["compare", "versus", "difference"]):
            return "comparison"
        elif any(word in query_lower for word in ["analyze", "evaluate", "assess"]):
            return "analysis"
        elif any(word in query_lower for word in ["research", "investigate", "study"]):
            return "research"
        else:
            return "general"
    
    def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract entities from query"""
        # Simplified entity extraction
        entities = []
        
        # Extract potential dates
        date_pattern = r'\d{4}[-/]\d{2}[-/]\d{2}'
        dates = re.findall(date_pattern, query)
        for date in dates:
            entities.append({"type": "date", "value": date})
        
        # Extract numbers
        number_pattern = r'\b\d+\.?\d*\b'
        numbers = re.findall(number_pattern, query)
        for number in numbers:
            entities.append({"type": "number", "value": number})
        
        # Extract quoted strings
        quote_pattern = r'"([^"]*)"'
        quotes = re.findall(quote_pattern, query)
        for quote in quotes:
            entities.append({"type": "quote", "value": quote})
        
        return entities
    
    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        word_count = len(query.split())
        clause_count = query.count(",") + query.count(";") + 1
        
        if word_count < 10 and clause_count == 1:
            return "low"
        elif word_count < 25 and clause_count <= 2:
            return "medium"
        elif word_count < 50:
            return "high"
        else:
            return "very_high"
    
    def _extract_topics(self, query: str) -> List[str]:
        """Extract key topics from query"""
        # Simplified topic extraction
        # In production, would use NLP model
        
        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                     "what", "how", "why", "when", "where", "who", "which", "is", "are", "was", "were"}
        
        words = query.lower().split()
        topics = []
        
        for word in words:
            word = word.strip(".,!?;:'\"")
            if len(word) > 3 and word not in stop_words:
                topics.append(word)
        
        return topics[:5]  # Return top 5 topics
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        # Simplified language detection
        # Check for common patterns
        
        if any(ord(char) > 0x4E00 and ord(char) < 0x9FFF for char in text):
            return "zh"  # Chinese
        elif any(ord(char) > 0xAC00 and ord(char) < 0xD7AF for char in text):
            return "ko"  # Korean
        elif any(ord(char) > 0x3040 and ord(char) < 0x309F for char in text):
            return "ja"  # Japanese
        else:
            return "en"  # Default to English
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost estimate"""
        cost_per_1k = MODEL_CONFIGS[model]["cost_per_1k_tokens"]
        return (tokens / 1000) * cost_per_1k
    
    async def _assess_accuracy(self, text: str) -> float:
        """Assess accuracy of text"""
        # Simplified assessment
        # In production, would use fact-checking model
        return 0.85
    
    async def _assess_factuality(self, text: str) -> float:
        """Assess factuality of text"""
        # Check for factual indicators
        factual_indicators = ["according to", "research shows", "study found", 
                             "data indicates", "evidence suggests"]
        
        score = 0.7  # Base score
        for indicator in factual_indicators:
            if indicator.lower() in text.lower():
                score += 0.05
        
        return min(1.0, score)
    
    def _assess_completeness(self, text: str) -> float:
        """Assess completeness of text"""
        # Check text length and structure
        word_count = len(text.split())
        
        if word_count < 50:
            return 0.3
        elif word_count < 100:
            return 0.5
        elif word_count < 200:
            return 0.7
        else:
            return 0.9
    
    def _assess_coherence(self, text: str) -> float:
        """Assess coherence of text"""
        # Check for paragraph structure and transitions
        paragraphs = text.split('\n\n')
        
        if len(paragraphs) == 1:
            return 0.6
        
        # Check for transition words
        transitions = ["however", "therefore", "moreover", "furthermore", 
                      "additionally", "consequently", "meanwhile"]
        
        transition_count = sum(1 for t in transitions if t.lower() in text.lower())
        
        coherence = 0.7 + (transition_count * 0.05)
        return min(1.0, coherence)
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score"""
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        if sentences == 0:
            return 0.5
        
        avg_words_per_sentence = len(words) / sentences
        
        # Ideal is 15-20 words per sentence
        if 15 <= avg_words_per_sentence <= 20:
            return 1.0
        elif avg_words_per_sentence < 10:
            return 0.6
        elif avg_words_per_sentence > 30:
            return 0.5
        else:
            return 0.8

# Initialize AI model manager
ai_manager = AIModelManager()

# API Endpoints
@app.post("/api/v1/generate", response_model=GenerationResponse)
async def generate_response(request: GenerationRequest):
    """Generate AI response"""
    return await ai_manager.generate(request)

@app.post("/api/v1/analyze_query", response_model=QueryAnalysisResponse)
async def analyze_query(request: QueryAnalysisRequest):
    """Analyze query intent and characteristics"""
    return await ai_manager.analyze_query(request)

@app.post("/api/v1/assess_quality", response_model=QualityAssessmentResponse)
async def assess_quality(request: QualityAssessmentRequest):
    """Assess content quality"""
    return await ai_manager.assess_quality(request)

@app.post("/api/v1/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """Generate embeddings for texts"""
    return await ai_manager.generate_embeddings(request)

@app.get("/api/v1/models")
async def get_available_models():
    """Get available models and their configurations"""
    return {
        "models": [
            {
                "name": model,
                "provider": config["provider"],
                "capabilities": config["capabilities"],
                "max_tokens": config["max_tokens"],
                "cost_per_1k_tokens": config["cost_per_1k_tokens"],
                "estimated_latency_ms": config["latency_ms"]
            }
            for model, config in MODEL_CONFIGS.items()
        ]
    }

@app.get("/api/v1/performance")
async def get_model_performance():
    """Get model performance statistics"""
    stats = {}
    
    for model, history in ai_manager.performance_stats.items():
        if history:
            recent = history[-100:]  # Last 100 requests
            stats[model] = {
                "requests": len(recent),
                "avg_latency_ms": np.mean([h["latency"] for h in recent]),
                "avg_tokens": np.mean([h["tokens"] for h in recent]),
                "avg_confidence": np.mean([h["confidence"] for h in recent]),
                "p95_latency_ms": np.percentile([h["latency"] for h in recent], 95)
            }
    
    return stats

@app.post("/api/v1/compare_models")
async def compare_models(
    query: str,
    models: List[str] = None,
    context: Optional[str] = ""
):
    """Compare responses from multiple models"""
    if not models:
        models = ["gpt-3.5-turbo", "claude-3-sonnet", "llama-3"]
    
    results = []
    for model in models:
        try:
            request = GenerationRequest(
                query=query,
                context=context,
                model=model
            )
            response = await ai_manager.generate(request)
            results.append({
                "model": model,
                "response": response.answer,
                "latency_ms": response.latency_ms,
                "cost": response.cost_estimate,
                "confidence": response.confidence
            })
        except Exception as e:
            results.append({
                "model": model,
                "error": str(e)
            })
    
    return {"comparisons": results}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-model-service",
        "available_models": len(MODEL_CONFIGS),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)