#!/usr/bin/env python3
"""
Korean RAG Service - Dummy Version
임시로 의존성 문제를 우회하기 위한 더미 서비스
"""

import sys
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# 기본 FastAPI 앱 생성
app = FastAPI(
    title="Korean RAG Service (Dummy)",
    description="임시 더미 서비스 - 의존성 문제 해결용",
    version="1.0.0-dummy"
)

@app.get("/")
async def root():
    return {"message": "Korean RAG Service (Dummy Mode)", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "dummy", "message": "Korean RAG running in dummy mode"}

@app.get("/status")
async def status():
    return {
        "service": "korean-rag",
        "mode": "dummy",
        "status": "healthy",
        "dependencies": "bypassed"
    }

if __name__ == "__main__":
    print("🚀 Korean RAG Service (Dummy Mode) Starting...")
    print("📍 Running on http://0.0.0.0:8009")
    print("⚠️  This is a dummy service to resolve dependency issues")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8009,
        log_level="info"
    )