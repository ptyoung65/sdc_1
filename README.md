# SDC - Smart Document Companion

Multi-LLM 기반 대화형 AI 서비스 플랫폼

## 🚀 Features

- **Multi-LLM Support**: OpenAI, Anthropic, Google, Ollama 등 다양한 LLM 제공자 지원
- **Advanced RAG Pipeline**: LangGraph 기반 고급 RAG 파이프라인
- **Hybrid Search**: 벡터 검색과 키워드 검색을 결합한 하이브리드 검색
- **Korean Language Optimized**: KURE-v1 한국어 임베딩 모델 지원
- **Enterprise Security**: JWT 인증, Rate Limiting, 보안 헤더
- **Scalable Architecture**: Podman 기반 컨테이너화 및 마이크로서비스 아키텍처

## 📋 Prerequisites

- Docker or Podman
- Node.js 20+
- Python 3.11+
- PostgreSQL 16+
- Redis 7+

## 🛠 Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/sdc.git
cd sdc

# Setup environment
make setup

# Start services
make up

# Check health
make health
```

### Manual Setup

1. **Environment Setup**
```bash
cp .env.example .env
# Edit .env with your configuration
```

2. **Install Dependencies**
```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
pip install -r requirements.txt
```

3. **Start Services**
```bash
# Using Docker Compose
docker-compose up -d

# Using Podman
podman-compose up -d
```

4. **Run Migrations**
```bash
make db-migrate
```

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Layer 5: CI/CD                    │
│         (GitLab CI, GitHub Actions, Podman)         │
├─────────────────────────────────────────────────────┤
│              Layer 4: Security & Monitoring         │
│     (Rate Limiter, Auth Middleware, Metrics)        │
├─────────────────────────────────────────────────────┤
│            Layer 3: Hybrid Search Database          │
│    (PostgreSQL + Milvus + Elasticsearch)            │
├─────────────────────────────────────────────────────┤
│         Layer 2: AI & RAG Orchestration             │
│    (LangGraph, Multi-LLM, Embedding Service)        │
├─────────────────────────────────────────────────────┤
│              Layer 1: Application Layer             │
│         (Next.js Frontend + FastAPI Backend)        │
└─────────────────────────────────────────────────────┘
```

## 🔧 Development

### Running Tests
```bash
# Run all tests
make test

# Backend tests only
make test-backend

# Frontend tests only
make test-frontend
```

### Code Quality
```bash
# Run linters
make lint

# Format code
make format

# Security scan
make security-scan
```

### Database Management
```bash
# Run migrations
make db-migrate

# Rollback migration
make db-rollback

# Reset database
make db-reset
```

## 📊 Monitoring

### Health Check
```bash
make health
```

### View Metrics
```bash
make metrics
```

### View Logs
```bash
# All services
make logs

# Specific service
make logs-backend
make logs-frontend
```

## 🚢 Deployment

### Staging Deployment
```bash
make deploy-staging
```

### Production Deployment
```bash
make deploy-production
```

## 📁 Project Structure

```
sdc/
├── frontend/               # Next.js frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API services
│   │   └── store/         # Zustand state management
│   └── public/            # Static assets
├── backend/               # FastAPI backend application
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   └── tests/            # Test files
├── scripts/              # Utility scripts
├── nginx/                # Nginx configuration
├── docker-compose.yml    # Docker compose configuration
├── Containerfile         # Podman/Docker build file
└── Makefile             # Build automation
```

## 🔐 Security

- JWT-based authentication
- Rate limiting per user/IP
- CORS protection
- SQL injection prevention
- XSS protection headers
- CSRF protection
- Secure password hashing (bcrypt)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- LangGraph for advanced RAG orchestration
- OpenAI, Anthropic, Google for LLM APIs
- Milvus for vector database
- Elasticsearch for full-text search
- FastAPI and Next.js communities

## 📞 Support

For support, email support@sdc.example.com or open an issue in the repository.

## 🚦 Status

- Backend API: ✅ Operational
- Frontend UI: ✅ Operational
- Vector Database: ✅ Operational
- Search Engine: ✅ Operational
- AI Services: ✅ Operational

---

Made with ❤️ by the SDC Team