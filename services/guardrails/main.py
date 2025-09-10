"""
Arthur AI Guardrails Microservice
- Content moderation
- Safety checks
- Risk assessment
- Compliance validation
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import arthur_bench as ab
from arthur_bench.client.bench import BenchClient
import logging
import os
from contextlib import asynccontextmanager
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
guardrails_client = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global guardrails_client, redis_client
    
    # Startup
    logger.info("🛡️ Starting Arthur AI Guardrails Microservice...")
    
    try:
        # Initialize Arthur AI Guardrails
        guardrails_client = BenchClient()
        logger.info("✅ Arthur AI Guardrails initialized successfully")
        
        # Initialize Redis connection
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        logger.info("✅ Redis connection established")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        # Continue without Arthur AI if it fails
        pass
    
    yield
    
    # Shutdown
    logger.info("🛡️ Shutting down Arthur AI Guardrails Microservice...")
    if redis_client:
        await redis_client.close()

# Create FastAPI app with lifespan
app = FastAPI(
    title="Arthur AI Guardrails Service",
    description="AI Safety and Content Moderation Microservice",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class GuardrailRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    rules: Optional[List[str]] = None

class GuardrailResponse(BaseModel):
    allowed: bool
    risk_score: float
    violations: List[Dict[str, Any]]
    filtered_text: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = {}

class GuardrailRule(BaseModel):
    id: str
    name: str
    description: str
    type: str  # "content", "bias", "toxicity", "pii", "custom"
    enabled: bool
    threshold: float
    action: str  # "block", "flag", "modify"
    parameters: Dict[str, Any] = {}

class GuardrailConfig(BaseModel):
    rules: List[GuardrailRule]
    global_settings: Dict[str, Any] = {}

# In-memory storage for rules (in production, use database)
DEFAULT_RULES = [
    GuardrailRule(
        id="toxicity",
        name="Toxicity Detection",
        description="Detect toxic and harmful content",
        type="toxicity",
        enabled=True,
        threshold=0.7,
        action="block",
        parameters={"model": "perspective_api"}
    ),
    GuardrailRule(
        id="pii",
        name="PII Detection",
        description="Detect personally identifiable information",
        type="pii",
        enabled=True,
        threshold=0.8,
        action="flag",
        parameters={"patterns": ["email", "phone", "ssn"]}
    ),
    GuardrailRule(
        id="bias",
        name="Bias Detection",
        description="Detect biased language and content",
        type="bias",
        enabled=True,
        threshold=0.6,
        action="flag",
        parameters={"categories": ["gender", "race", "age"]}
    ),
    GuardrailRule(
        id="profanity",
        name="Profanity Filter",
        description="Filter profane and inappropriate language",
        type="content",
        enabled=True,
        threshold=0.5,
        action="modify",
        parameters={"replacement": "***"}
    )
]

current_config = GuardrailConfig(rules=DEFAULT_RULES)

# Dependency to get current config
async def get_config() -> GuardrailConfig:
    return current_config

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "arthur-ai-guardrails",
        "arthur_ai_available": guardrails_client is not None,
        "redis_available": redis_client is not None
    }

@app.post("/api/v1/guardrails/check", response_model=GuardrailResponse)
async def check_content(
    request: GuardrailRequest,
    config: GuardrailConfig = Depends(get_config)
):
    """Check content against guardrails"""
    logger.info(f"🛡️ Checking content: {request.text[:100]}...")
    
    violations = []
    risk_score = 0.0
    filtered_text = request.text
    allowed = True
    
    try:
        # Check each enabled rule
        for rule in config.rules:
            if not rule.enabled:
                continue
                
            violation = await _check_rule(request.text, rule, request.context)
            if violation:
                violations.append(violation)
                risk_score = max(risk_score, violation.get("score", 0.0))
                
                if rule.action == "block" and violation.get("score", 0.0) >= rule.threshold:
                    allowed = False
                elif rule.action == "modify":
                    filtered_text = _apply_modification(filtered_text, rule, violation)
        
        # Cache result if Redis available
        if redis_client and request.user_id:
            cache_key = f"guardrail:{request.user_id}:{hash(request.text)}"
            await redis_client.setex(
                cache_key, 
                3600,  # 1 hour
                f"{allowed}:{risk_score}"
            )
        
        return GuardrailResponse(
            allowed=allowed,
            risk_score=risk_score,
            violations=violations,
            filtered_text=filtered_text if filtered_text != request.text else None,
            reason=_generate_reason(violations) if violations else None,
            metadata={
                "rules_checked": len([r for r in config.rules if r.enabled]),
                "processing_time_ms": 150  # Placeholder
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error checking content: {e}")
        # Fail open - allow content if service fails
        return GuardrailResponse(
            allowed=True,
            risk_score=0.0,
            violations=[],
            reason="Service unavailable - content allowed by default",
            metadata={"error": str(e)}
        )

async def _check_rule(text: str, rule: GuardrailRule, context: Optional[Dict] = None) -> Optional[Dict]:
    """Check a specific rule against text"""
    
    if rule.type == "toxicity":
        # Simulate toxicity detection
        import re
        toxic_patterns = ["hate", "kill", "stupid", "idiot", "death"]
        matches = sum(1 for pattern in toxic_patterns if pattern.lower() in text.lower())
        score = min(matches * 0.3, 1.0)
        
        if score >= rule.threshold:
            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "type": rule.type,
                "score": score,
                "details": f"Detected {matches} toxic patterns",
                "action": rule.action
            }
    
    elif rule.type == "pii":
        # Simulate PII detection
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b'
        
        pii_found = []
        if re.search(email_pattern, text):
            pii_found.append("email")
        if re.search(phone_pattern, text):
            pii_found.append("phone")
            
        if pii_found:
            score = len(pii_found) * 0.4
            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "type": rule.type,
                "score": score,
                "details": f"Detected PII: {', '.join(pii_found)}",
                "action": rule.action
            }
    
    elif rule.type == "bias":
        # Simulate bias detection
        bias_words = ["man", "woman", "black", "white", "young", "old"]
        matches = sum(1 for word in bias_words if word.lower() in text.lower())
        score = min(matches * 0.2, 1.0)
        
        if score >= rule.threshold:
            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "type": rule.type,
                "score": score,
                "details": f"Potential bias detected: {matches} indicators",
                "action": rule.action
            }
    
    elif rule.type == "content":
        # Simulate profanity detection
        profane_words = ["damn", "hell", "crap", "stupid"]
        matches = sum(1 for word in profane_words if word.lower() in text.lower())
        score = min(matches * 0.25, 1.0)
        
        if score >= rule.threshold:
            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "type": rule.type,
                "score": score,
                "details": f"Profanity detected: {matches} instances",
                "action": rule.action
            }
    
    return None

def _apply_modification(text: str, rule: GuardrailRule, violation: Dict) -> str:
    """Apply modification based on rule"""
    if rule.type == "content" and rule.action == "modify":
        # Simple profanity replacement
        profane_words = ["damn", "hell", "crap", "stupid"]
        for word in profane_words:
            text = text.replace(word, rule.parameters.get("replacement", "***"))
    
    return text

def _generate_reason(violations: List[Dict]) -> str:
    """Generate human-readable reason for violations"""
    if not violations:
        return None
    
    reasons = []
    for v in violations:
        reasons.append(f"{v['rule_name']}: {v['details']}")
    
    return "; ".join(reasons)

# Configuration Management APIs
@app.get("/api/v1/guardrails/config", response_model=GuardrailConfig)
async def get_guardrail_config():
    """Get current guardrail configuration"""
    return current_config

@app.put("/api/v1/guardrails/config")
async def update_guardrail_config(config: GuardrailConfig):
    """Update guardrail configuration"""
    global current_config
    current_config = config
    logger.info(f"🛡️ Configuration updated: {len(config.rules)} rules")
    return {"message": "Configuration updated successfully"}

@app.get("/api/v1/guardrails/rules", response_model=List[GuardrailRule])
async def get_rules():
    """Get all guardrail rules"""
    return current_config.rules

@app.post("/api/v1/guardrails/rules", response_model=GuardrailRule)
async def create_rule(rule: GuardrailRule):
    """Create new guardrail rule"""
    current_config.rules.append(rule)
    logger.info(f"🛡️ New rule created: {rule.name}")
    return rule

@app.put("/api/v1/guardrails/rules/{rule_id}", response_model=GuardrailRule)
async def update_rule(rule_id: str, rule_update: GuardrailRule):
    """Update existing guardrail rule"""
    for i, rule in enumerate(current_config.rules):
        if rule.id == rule_id:
            current_config.rules[i] = rule_update
            logger.info(f"🛡️ Rule updated: {rule_update.name}")
            return rule_update
    
    raise HTTPException(status_code=404, detail="Rule not found")

@app.delete("/api/v1/guardrails/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete guardrail rule"""
    for i, rule in enumerate(current_config.rules):
        if rule.id == rule_id:
            deleted_rule = current_config.rules.pop(i)
            logger.info(f"🛡️ Rule deleted: {deleted_rule.name}")
            return {"message": "Rule deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Rule not found")

# Statistics and Monitoring
@app.get("/api/v1/guardrails/stats")
async def get_statistics():
    """Get guardrail usage statistics"""
    # In production, get from database/analytics
    return {
        "total_checks": 1250,
        "blocked_content": 85,
        "flagged_content": 203,
        "modified_content": 47,
        "top_violations": [
            {"type": "toxicity", "count": 45},
            {"type": "pii", "count": 32},
            {"type": "bias", "count": 28},
            {"type": "profanity", "count": 60}
        ],
        "success_rate": 98.5,
        "average_response_time_ms": 145
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)