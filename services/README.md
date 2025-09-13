# RAG Performance Evaluation Microservices

A comprehensive microservices architecture for evaluating and monitoring RAG (Retrieval-Augmented Generation) system performance.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Dashboard │    │  RAG Evaluator  │    │  Metrics DB     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 3002    │    │   Port: 8002    │    │   Port: 5433    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          ▲                        ▲
          │                        │
          └────────────────────────┘
                     ▲
┌─────────────────────────────────────────────────────────────────┐
│                    Nginx Proxy                                 │
│                    Port: 8080                                  │
└─────────────────────────────────────────────────────────────────┘
                     ▲
┌─────────────────────────────────────────────────────────────────┐
│                 Main Backend API                               │
│              (RAG Evaluation Client)                          │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Features

### 🎯 Core RAG Metrics
- **Context Relevance**: 검색된 문서가 질의에 얼마나 관련성 있는지
- **Context Sufficiency**: 검색된 컨텍스트만으로 답변 생성에 충분한지  
- **Answer Relevance**: 최종 답변이 질의에 얼마나 부합하는지
- **Answer Correctness**: 답변이 정답과 얼마나 일치하는지
- **Hallucination Rate**: 허위 정보를 생성하는 비율
- **Latency**: 질의부터 응답까지의 총 시간 및 단계별 소요 시간
- **Throughput**: 초당 처리 가능한 질의 수

### 📈 Advanced Analytics
- Real-time performance monitoring
- Historical trend analysis
- Quality score aggregations
- Latency percentile tracking (P50, P95, P99)
- Throughput analysis

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### 1. Build and Start Services
```bash
# Using Make (recommended)
cd services/
make build
make up

# Or using Docker Compose directly
docker-compose -f docker-compose.rag-eval.yml build
docker-compose -f docker-compose.rag-eval.yml up -d
```

### 2. Verify Services
```bash
# Check all services health
make health

# View service status
make status
```

### 3. Access Services
- **RAG Dashboard**: http://localhost:3002
- **RAG Evaluator API**: http://localhost:8002
- **Unified Access (via Proxy)**: http://localhost:8080
- **Database**: localhost:5433

## 🛠️ Development

### Available Commands
```bash
make help          # Show all available commands
make build         # Build containers
make up            # Start services
make down          # Stop services
make logs          # View all logs
make logs-eval     # View evaluator logs
make logs-dash     # View dashboard logs
make health        # Check service health
make test          # Run API tests
make clean         # Clean containers and volumes
make rebuild       # Full rebuild
```

### Service Management
```bash
# Start with logs visible
make up-logs

# Access service shells
make shell-eval    # RAG evaluator container
make shell-dash    # RAG dashboard container
make shell-db      # Database container

# Database operations
make db-reset      # Reset metrics database
```

## 🔧 Configuration

### Environment Variables
Set these in your `.env` file or container environment:

```env
# Database
DATABASE_URL=postgresql://rag_metrics_user:rag_metrics_password@rag-metrics-db:5432/rag_metrics

# RAG Evaluator Service
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1

# RAG Dashboard
NEXT_PUBLIC_RAG_EVALUATOR_API=http://rag-evaluator:8002
NODE_ENV=production
```

### Database Schema
The metrics database includes:
- `rag_sessions`: Session tracking
- `rag_evaluations`: Detailed evaluation results
- `rag_performance_aggregations`: Pre-computed hourly metrics

## 📡 API Usage

### Evaluate RAG Session
```bash
curl -X POST http://localhost:8002/api/v1/rag/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "query": "What is machine learning?",
    "retrieval_stage": {
      "stage": "retrieval",
      "start_time": 1640995200.0,
      "end_time": 1640995200.5,
      "latency_ms": 500,
      "retrieved_chunks": [...],
      "num_chunks": 5
    },
    "generation_stage": {
      "stage": "generation", 
      "start_time": 1640995200.5,
      "end_time": 1640995202.0,
      "latency_ms": 1500,
      "llm_response": "Machine learning is...",
      "model_name": "gemini-pro"
    },
    "user_id": "user-456"
  }'
```

### Get Evaluation Results
```bash
# Get session evaluation
curl http://localhost:8002/api/v1/rag/sessions/session-123

# Get metrics summary  
curl http://localhost:8002/api/v1/rag/metrics/summary

# Get real-time metrics
curl http://localhost:8002/api/v1/rag/metrics/realtime
```

## 🔍 Monitoring

### Health Checks
All services include health check endpoints:
- RAG Evaluator: `GET /health`
- RAG Dashboard: `GET /health` 
- Database: PostgreSQL `pg_isready`
- Nginx Proxy: `GET /health`

### Logs
```bash
# View specific service logs
make logs-eval     # RAG evaluator
make logs-dash     # RAG dashboard  
make logs-db       # Database
make logs-proxy    # Nginx proxy

# Resource monitoring
make stats         # Container resource usage
```

## 🧪 Testing

### API Tests
```bash
make test          # Run comprehensive API tests
```

### Manual Testing
```bash
# Test evaluator API
curl -X POST http://localhost:8002/api/v1/rag/evaluate \
  -H "Content-Type: application/json" \
  -d @test-data.json

# Test dashboard access
curl -f http://localhost:3002
```

## 📂 Project Structure

```
services/
├── docker-compose.rag-eval.yml    # Service orchestration
├── Makefile                       # Development commands
├── nginx/
│   └── rag-eval.conf             # Reverse proxy config
├── rag-evaluator/                # Evaluation microservice
│   ├── Containerfile             # Docker build config
│   ├── main.py                   # FastAPI application
│   ├── requirements.txt          # Python dependencies
│   └── init.sql                  # Database schema
└── rag-dashboard/                # Monitoring dashboard
    ├── Containerfile             # Docker build config
    ├── package.json              # Node.js dependencies
    └── src/                      # Next.js application
```

## 🤝 Integration

The RAG evaluation system integrates with your main application through the client:

```python
from app.services.rag_evaluation_client import RAGPerformanceTracker

# Initialize tracker
tracker = RAGPerformanceTracker(
    session_id="session-123",
    query="User question",
    user_id="user-456"
)

# Track retrieval phase
tracker.start_retrieval()
# ... perform RAG retrieval ...
tracker.end_retrieval(retrieved_chunks)

# Track generation phase  
tracker.start_generation()
# ... perform LLM generation ...
tracker.end_generation(response, model_name)

# Evaluate performance
evaluation_result = await tracker.evaluate()
```

## 🐛 Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure ports 3002, 8002, 8080, 5433 are available
2. **Database connection**: Wait for database to be ready before starting other services
3. **Memory issues**: Ensure sufficient Docker memory allocation

### Debug Commands
```bash
make logs          # Check all service logs
make health        # Verify service health
make ps            # Show container status
make stats         # Monitor resource usage
```

## 📄 License
This RAG evaluation system is part of the SDC (Smart Document Companion) project.