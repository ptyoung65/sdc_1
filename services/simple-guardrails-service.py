#!/usr/bin/env python3
"""
Simple Arthur AI Guardrails Service for Admin Panel
Provides basic guardrail rule management without complex dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn
import logging
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Simple Arthur AI Guardrails Service",
    description="Basic guardrail rule management for Admin Panel",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
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

class ValidationRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

class ValidationResponse(BaseModel):
    passed: bool
    violations: List[Dict[str, Any]] = []
    modified_text: Optional[str] = None
    risk_score: float = 0.0

class CreateRuleRequest(BaseModel):
    name: str
    type: str = "toxicity"  # "content", "bias", "toxicity", "pii", "custom"
    threshold: float = 0.5
    action: str = "flag"  # "block", "flag", "modify"

# In-memory storage for rules
DEFAULT_RULES = [
    GuardrailRule(
        id="toxicity",
        name="Toxicity Detection",
        description="Detects toxic, harmful, or inappropriate content",
        type="toxicity",
        enabled=True,
        threshold=0.7,
        action="flag",
        parameters={"severity_levels": ["low", "medium", "high"]}
    ),
    GuardrailRule(
        id="bias",
        name="Bias Detection",
        description="Identifies potential bias in text content",
        type="bias",
        enabled=True,
        threshold=0.6,
        action="flag",
        parameters={"bias_types": ["gender", "racial", "religious", "age"]}
    ),
    GuardrailRule(
        id="pii",
        name="PII Detection", 
        description="Detects personally identifiable information",
        type="pii",
        enabled=True,
        threshold=0.8,
        action="modify",
        parameters={"pii_types": ["email", "phone", "ssn", "credit_card"]}
    ),
    GuardrailRule(
        id="content_safety",
        name="Content Safety",
        description="Ensures content meets safety guidelines",
        type="content",
        enabled=True,
        threshold=0.5,
        action="block",
        parameters={"categories": ["violence", "explicit", "illegal"]}
    )
]

# Global storage
guardrail_rules = {rule.id: rule for rule in DEFAULT_RULES}

# API Endpoints
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "simple-guardrails-service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/guardrails/rules", response_model=List[GuardrailRule])
async def get_rules():
    """Get all guardrail rules"""
    return list(guardrail_rules.values())

@app.post("/api/v1/guardrails/rules", response_model=GuardrailRule)
async def create_rule(rule_request: CreateRuleRequest):
    """Create new guardrail rule"""
    import time
    
    # Generate unique ID
    rule_id = f"{rule_request.type}_{int(time.time() * 1000)}"
    
    # Create full GuardrailRule with defaults
    new_rule = GuardrailRule(
        id=rule_id,
        name=rule_request.name,
        description=f"{rule_request.name} - Auto-generated rule",
        type=rule_request.type,
        enabled=True,
        threshold=rule_request.threshold,
        action=rule_request.action,
        parameters={}
    )
    
    guardrail_rules[rule_id] = new_rule
    logger.info(f"Created new guardrail rule: {rule_id}")
    return new_rule

@app.put("/api/v1/guardrails/rules/{rule_id}", response_model=GuardrailRule)
async def update_rule(rule_id: str, rule_update: GuardrailRule):
    """Update existing guardrail rule"""
    if rule_id not in guardrail_rules:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule_update.id = rule_id  # Ensure ID matches
    guardrail_rules[rule_id] = rule_update
    logger.info(f"Updated guardrail rule: {rule_id}")
    return rule_update

@app.delete("/api/v1/guardrails/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete guardrail rule"""
    if rule_id not in guardrail_rules:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    deleted_rule = guardrail_rules.pop(rule_id)
    logger.info(f"Deleted guardrail rule: {rule_id}")
    return {"message": f"Rule {rule_id} deleted successfully"}

@app.get("/api/v1/guardrails/rules/{rule_id}", response_model=GuardrailRule)
async def get_rule(rule_id: str):
    """Get specific guardrail rule"""
    if rule_id not in guardrail_rules:
        raise HTTPException(status_code=404, detail="Rule not found")
    return guardrail_rules[rule_id]

@app.post("/api/v1/guardrails/validate", response_model=ValidationResponse)
async def validate_content(request: ValidationRequest):
    """Validate content against guardrail rules"""
    violations = []
    risk_score = 0.0
    modified_text = request.text
    
    # Simple mock validation logic
    enabled_rules = [rule for rule in guardrail_rules.values() if rule.enabled]
    
    for rule in enabled_rules:
        # Mock validation - in real implementation, this would use actual AI models
        violation_score = len(request.text) % 10 / 10.0  # Mock score
        
        if violation_score > rule.threshold:
            violations.append({
                "rule_id": rule.id,
                "rule_name": rule.name,
                "violation_type": rule.type,
                "score": violation_score,
                "action": rule.action,
                "message": f"Content violates {rule.name} policy"
            })
            risk_score = max(risk_score, violation_score)
            
            # Apply action
            if rule.action == "modify":
                modified_text = f"[REDACTED - {rule.name}]"
    
    passed = len(violations) == 0
    
    return ValidationResponse(
        passed=passed,
        violations=violations,
        modified_text=modified_text if not passed else None,
        risk_score=risk_score
    )

@app.get("/api/v1/guardrails/stats")
async def get_stats():
    """Get guardrails statistics"""
    # Mock statistics data for Admin Panel
    import random
    
    return {
        "total_checks": 15247,
        "blocked_content": 234,
        "flagged_content": 567,
        "modified_content": 89,
        "success_rate": 98.4,
        "average_response_time_ms": 125,
        "top_violations": [
            {"type": "toxicity", "count": 134},
            {"type": "bias", "count": 89},
            {"type": "pii", "count": 67},
            {"type": "content", "count": 45}
        ]
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    
    logger.info(f"🛡️ Starting Simple Guardrails Service on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)