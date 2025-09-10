#!/usr/bin/env python3
"""
Simple Curation Service for temporary dashboard connection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime
import argparse

app = FastAPI(
    title="Simple Curation Service",
    description="Temporary curation service for dashboard connection",
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

# Mock data for dashboard
@app.get("/api/v1/metrics")
async def get_metrics():
    """Get curation metrics"""
    return {
        "total_sessions": 150,
        "total_curations": 450,
        "avg_processing_time": 1250,
        "success_rate": 0.95,
        "strategies": [
            {"name": "relevance", "usage": 35.5, "success_rate": 0.92},
            {"name": "quality", "usage": 28.3, "success_rate": 0.96},
            {"name": "diversity", "usage": 20.1, "success_rate": 0.88},
            {"name": "temporal", "usage": 10.4, "success_rate": 0.85},
            {"name": "hybrid", "usage": 5.7, "success_rate": 0.98}
        ]
    }

@app.get("/api/v1/strategies")
async def get_strategies():
    """Get available curation strategies"""
    return {
        "strategies": [
            {"id": "relevance", "name": "Relevance-based", "description": "Focus on content relevance"},
            {"id": "quality", "name": "Quality-based", "description": "Focus on content quality"},
            {"id": "diversity", "name": "Diversity-based", "description": "Ensure content diversity"},
            {"id": "temporal", "name": "Temporal-based", "description": "Time-aware curation"},
            {"id": "hybrid", "name": "Hybrid", "description": "Combined strategies"}
        ]
    }

@app.get("/api/v1/performance")
async def get_performance():
    """Get performance metrics"""
    return {
        "latency": {"avg": 1250, "p95": 2100, "p99": 3500},
        "throughput": {"requests_per_second": 45},
        "quality": {"avg_score": 0.85, "consistency": 0.92},
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/status")
async def get_status():
    """Get service status"""
    return {
        "status": "healthy",
        "service": "simple-curation-service",
        "version": "1.0.0",
        "uptime": 3600,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/curate")
async def curate_content():
    """Mock curation endpoint"""
    return {
        "session_id": "mock-session-123",
        "strategy": "relevance",
        "curated_items": 15,
        "processing_time": 1250,
        "quality_score": 0.88,
        "status": "completed"
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8006)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port)