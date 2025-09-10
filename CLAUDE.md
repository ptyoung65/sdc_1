# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

This project uses a comprehensive Makefile for development tasks. All commands should be run from the project root.

### Essential Commands
- `make help` - Display all available commands
- `make setup` - Initial project setup (copies .env, installs dependencies, builds containers)
- `make up` - Start all services in containers
- `make dev` - Start development environment (databases only, then backend/frontend locally)
- `make down` - Stop all services
- `make health` - Check if all services are running properly

### Testing
- `make test` - Run all tests (backend + frontend)
- `make test-backend` - Run Python backend tests using pytest
- `make test-frontend` - Run Next.js frontend tests using Jest
- `make test-integration` - Run integration tests with full stack

### Code Quality
- `make lint` - Run all linters (backend: black, ruff, mypy; frontend: eslint)
- `make lint-backend` - Backend: `black --check`, `ruff check`, `mypy`
- `make lint-frontend` - Frontend: `npm run lint` 
- `make format` - Format all code (black for Python, prettier for TypeScript)

### Database Management
- `make db-migrate` - Run Alembic database migrations
- `make db-rollback` - Rollback last migration
- `make db-reset` - Reset database completely (destructive)

### Container Management
Uses Podman by default (can substitute Docker):
- `make build` - Build all containers
- `make build-backend` - Build only backend container
- `make build-frontend` - Build only frontend container

## Architecture Overview

SDC (Smart Document Companion) is a multi-LLM conversational AI platform with the following architecture:

### Layer Structure
```
Layer 5: CI/CD (Podman/Docker deployment)
Layer 4: Security & Monitoring (Rate limiting, JWT auth, metrics)
Layer 3: Hybrid Search Database (PostgreSQL + Milvus + Elasticsearch)
Layer 2: AI & RAG Orchestration (LangGraph, Multi-LLM, Embedding)
Layer 1: Application Layer (Next.js Frontend + FastAPI Backend)
```

### Core Services
- **Backend**: FastAPI application (`backend/app/main.py`)
- **Frontend**: Next.js application with Zustand state management
- **PostgreSQL**: Primary database with pgvector extension
- **Redis**: Caching and rate limiting
- **Milvus**: Vector database for embeddings
- **Elasticsearch**: Full-text search engine
- **Nginx**: Reverse proxy and load balancer

### Backend Structure (`backend/app/`)
- `api/routes/` - API endpoint definitions
- `core/` - Core functionality (config, database, middleware, security)
- `services/` - Business logic (auth, AI services, document processing)
- `schemas/` - Pydantic data validation models
- `services/ai/` - Multi-LLM orchestration, RAG pipeline, embeddings

### Frontend Structure (`frontend/`)
- `src/components/` - React components
- `src/hooks/` - Custom React hooks  
- `src/services/` - API service layer
- `src/store/` - Zustand state management
- Uses Radix UI components, Tailwind CSS, and React Hook Form

### Multi-LLM PRP System (`multi-llm-prp/`)
Separate TypeScript project implementing Problem Refinement Prompts methodology:
- `src/core/` - Core types and interfaces
- `src/agents/` - Agent orchestration system
- `src/providers/` - OpenAI, Anthropic, Google AI integrations
- `src/prp/` - PRP management and validation

## Key Technologies

### Backend Stack
- **FastAPI** - Python async web framework
- **SQLAlchemy** - Database ORM with async support
- **Alembic** - Database migrations
- **Pydantic** - Data validation and serialization
- **LangGraph** - RAG pipeline orchestration
- **JWT** - Authentication tokens
- **bcrypt** - Password hashing

### Frontend Stack  
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Zustand** - State management
- **Radix UI** - Accessible UI components
- **Tailwind CSS** - Utility-first styling
- **React Hook Form + Zod** - Form handling and validation
- **SWR** - Data fetching
- **Framer Motion** - Animations

### AI/ML Services
- **Multi-LLM Support**: OpenAI, Anthropic, Google, Ollama
- **KURE-v1**: Korean language optimized embedding model
- **Hybrid Search**: Vector + keyword search combination
- **RAG Pipeline**: Advanced retrieval-augmented generation

## Development Guidelines

### Environment Setup
- Copy `.env.example` to `.env` and configure API keys
- Requires Node.js 20+, Python 3.11+, PostgreSQL 16+, Redis 7+
- Use `make setup` for initial configuration

### Testing Requirements
- Backend: Use pytest with asyncio support
- Frontend: Jest for unit tests, Playwright for E2E
- Always run tests before committing: `make test`

### Code Standards
- Backend: Black formatting, Ruff linting, MyPy type checking
- Frontend: ESLint + Prettier, TypeScript strict mode
- Use `make lint` to check code quality

### Security Considerations
- JWT-based authentication with bcrypt password hashing  
- Rate limiting per user/IP
- CORS protection and security headers
- SQL injection prevention via SQLAlchemy
- Never commit API keys or secrets

### Container Development
- Uses Podman by default (Docker compatible)
- Multi-stage Containerfile for optimized builds
- Health checks for all services
- Volume mounts for development hot-reloading

## 완료된 기능 체크리스트

### ✅ Document Upload & RAG Service Integration (2025-09-05)
**Status**: COMPLETE - DO NOT MODIFY UNLESS EXPLICITLY REQUESTED

**Implemented Features**:
1. **Document Upload API** ✅
   - `POST /api/v1/documents` endpoint for frontend compatibility
   - `POST /api/v1/documents/upload` endpoint (legacy support)
   - File processing and storage in memory store
   - Support for multipart/form-data uploads

2. **Simple Document Search** ✅
   - Keyword-based document content matching
   - Context extraction (200-character snippets)
   - User-specific document isolation
   - Fallback to basic AI when no matches found

3. **RAG Integration** ✅
   - Enhanced AI responses using document context
   - Source attribution in responses
   - Hybrid approach: Full RAG service when available, simple search as fallback
   - Integration with existing chat endpoint

4. **Testing & Validation** ✅
   - Document upload endpoint tested and working
   - RAG-based chat responses verified
   - Frontend-backend integration confirmed
   - All API endpoints responding correctly

**Key Files Modified**:
- `backend/simple_api.py`: Main implementation
- Added document storage, search logic, and API endpoints
- Preserved all existing functionality

**Important**: This implementation uses a simple in-memory document store and keyword matching. Do not modify this working solution unless the user explicitly requests changes or improvements. The system is functioning correctly and serving uploaded documents in AI responses.

### ✅ Multi-Format Document Processing System (2025-09-05)
**Status**: COMPLETE - DO NOT MODIFY UNLESS EXPLICITLY REQUESTED
**Commit**: 11e58bd - "Implement multi-format document processing with Docling and alternative processors"

**Implemented Features**:

1. **Docker Container Integration** ✅
   - Added Docling service to `docker-compose.yml`
   - Container configured with health checks and proper networking
   - Environment variables for DOCLING_HOST and DOCLING_PORT
   - Volume mounts for document processing (`./uploads` and `./processed`)
   - Backend service dependency on Docling service

2. **Docling Client Service** ✅
   - **File**: `backend/app/services/document/docling_client.py`
   - HTTP client for Docling service communication
   - Support for PDF, PPT, PPTX, XLSX, XLS, DOC, DOCX formats
   - Automatic file type detection and validation
   - Comprehensive error handling with fallback mechanisms
   - Health check capabilities

3. **Alternative Document Processor** ✅
   - **File**: `backend/app/services/document/alternative_processor.py`
   - Local Python library fallback when Docling unavailable
   - **Libraries**: python-docx, python-pptx, openpyxl, PyPDF2
   - Format-specific processing methods for each document type
   - Graceful degradation with informative error messages

4. **Enhanced Upload Processing** ✅
   - **File**: `backend/simple_api.py` (507 lines added)
   - Smart document processing pipeline: Docling → Alternative → Basic
   - Automatic file extension detection and format routing
   - Temporary file handling with cleanup
   - Comprehensive logging and status tracking
   - Processing method attribution (docling/alternative_processor/basic)

5. **Dependencies & Environment** ✅
   - **Installed Libraries**: python-docx, python-pptx, openpyxl, PyPDF2, lxml, XlsxWriter
   - **Requirements Updated**: `requirements.txt` and `requirements-minimal.txt`
   - All document processing dependencies available in virtual environment
   - Import error handling with graceful fallbacks

6. **Database Migrations Setup** ✅
   - **Alembic Configuration**: `backend/alembic.ini`
   - Database migration scripts in `backend/alembic/`
   - Proper database model support for document metadata

7. **Monitoring & Metrics** ✅
   - **File**: `backend/app/core/monitoring/enhanced_metrics.py`
   - Document processing performance tracking
   - Success/failure rate monitoring for different processors

8. **Frontend Integration** ✅
   - **File**: `frontend/src/components/chat/conversation-sidebar.tsx`
   - UI components for document management
   - Compatible with existing upload workflow

**Processing Flow**:
```
File Upload → Extension Detection → Structured Format Check
    ↓
If PDF/PPT/XLSX/DOC:
    Try Docling Service → If Failed → Alternative Processor → If Failed → Basic Processing
Else:
    Basic Text Processing
    ↓
Store with Processing Method Metadata → RAG Integration
```

**Supported Formats**:
- ✅ **PDF**: PyPDF2 library
- ✅ **Word**: python-docx (DOCX, DOC)  
- ✅ **PowerPoint**: python-pptx (PPTX, PPT)
- ✅ **Excel**: openpyxl (XLSX, XLS)
- ✅ **Text**: Built-in (TXT, MD)

**Key Files Modified/Created**:
- `docker-compose.yml`: Added Docling service configuration
- `backend/simple_api.py`: Enhanced with multi-format processing (507 lines added)
- `backend/app/services/document/`: Complete document processing module
- `backend/requirements.txt`: Updated with document processing libraries
- `backend/alembic/`: Database migration setup
- Frontend conversation components

**Testing Status**: ✅ VERIFIED
- Document upload working with all supported formats
- Fallback mechanisms tested (Docling → Alternative → Basic)
- Integration with existing RAG pipeline confirmed
- Frontend-backend communication verified
- All processing methods functional

**Important**: This is a complete, production-ready multi-format document processing system with intelligent fallback mechanisms. The system automatically detects file types and uses the most appropriate processing method. Do not modify this implementation unless specifically requested, as it provides comprehensive document processing capabilities while maintaining backward compatibility.

## ⚠️ CRITICAL DEVELOPMENT GUIDELINES

### Completed Features Protection
**BEFORE modifying any file related to completed features, you MUST:**

1. **Check CLAUDE.md Completion Checklist** - Review the "완료된 기능 체크리스트" section
2. **Verify Feature Status** - If marked as "COMPLETE - DO NOT MODIFY", get explicit user confirmation
3. **Preserve Existing Functionality** - Never break working features during modifications
4. **Test Before Commit** - Verify all existing features still work after changes

### Multi-Format Document Processing - Protection Rules
**Status**: COMPLETE (Commit: 11e58bd) - PROTECTED SYSTEM

**DO NOT MODIFY these files without explicit user request:**
- `docker-compose.yml` (Docling service configuration)
- `backend/simple_api.py` (Document processing pipeline)  
- `backend/app/services/document/` (Document processing modules)
- `backend/requirements.txt` (Document processing dependencies)

**IF modification is requested:**
1. Backup existing functionality
2. Test all document formats (PDF, DOCX, PPTX, XLSX)  
3. Verify fallback mechanisms work
4. Confirm RAG integration remains functional
5. Update completion checklist if changes are made

### Code Modification Priority
1. **Preserve Completed Features** (Highest Priority)
2. **Implement New Requirements**
3. **Optimize/Refactor** (Lowest Priority)

This ensures stable, working features are not accidentally broken during development.

## 🔌 포트 관리 및 서비스 매핑

### 현재 사용 중인 포트 목록
**이 섹션은 모든 프로젝트 재실행 시 확인해야 하며, 신규 서비스 생성 시 포트 충돌을 방지하기 위해 반드시 참조해야 합니다.**

#### ✅ 활성 포트 (Active Ports)
| 포트 | 서비스명 | 설명 | 상태 | 시작 명령 |
|------|---------|------|------|-----------|
| 3000 | SDC Frontend | 메인 AI 챗봇 UI | ✅ 활성 | `cd frontend && npm run dev` |
| 3001 | - | 미사용 | ⭕ 미사용 | - |
| 3002 | Dify | AI Workflow Builder | ✅ 활성 | Docker 컨테이너로 실행 중 |
| 3003 | Admin Panel / RAG Dashboard | 관리자 페이지 (Guardrails/RBAC) | ✅ 활성 | `cd services/admin-panel && npm run dev` |
| 3004 | Curation Dashboard | AI 큐레이션 모니터링 대시보드 | ✅ 활성 | `cd services/curation-dashboard && npm run dev` |
| 8000 | SDC Backend API | 메인 백엔드 서비스 | ✅ 활성 | `cd backend && python simple_api.py` |
| 8001 | Guardrails Service | AI 안전 가드레일 서비스 | ✅ 활성 | `cd services && python simple-guardrails-service.py --port 8001` |
| 8002 | RAG Evaluator | RAG 성과 평가 서비스 | ✅ 활성 | `cd services/rag-evaluator && python main.py --port 8002` |
| 8003 | - | 미사용 | ⭕ 미사용 | - |
| 8004 | - | 미사용 | ⭕ 미사용 | - |
| 8005 | - | 미사용 | ⭕ 미사용 | - |
| 8006 | Curation Service | 큐레이션 API 서비스 | ✅ 활성 | `cd services && python simple-curation-service.py --port 8006` |
| 8007 | AI Model Service | AI 모델 관리 서비스 | ✅ 활성 | `cd services/ai-model-service && python main.py --port 8007` |
| 8008 | RAG Orchestrator | RAG 파이프라인 오케스트레이터 | ✅ 활성 | `cd services/rag-orchestrator && python main.py --port 8008` |
| 8080 | SearxNG | 검색 엔진 | ⚠️ 가능 | Docker 컨테이너 |
| 5432 | PostgreSQL | 데이터베이스 | ⚠️ 가능 | Docker/시스템 서비스 |
| 6379 | Redis | 캐시/세션 스토어 | ⚠️ 가능 | Docker/시스템 서비스 |

### 📝 포트 확인 명령어
프로젝트 재실행 전 반드시 실행해야 할 명령어:

```bash
# 포트 상태 빠른 확인
for port in 3000 3001 3002 3003 3004 8000 8001 8002 8003 8004 8005 8006 8007 8008; do 
  echo -n "Port $port: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$port 2>/dev/null || echo "Not Available"
done

# 프로세스 확인
ps aux | grep -E "(node|python|uvicorn)" | grep -E "(3000|3001|3002|3003|3004|8000|8006|8007|8008)"

# 포트 강제 종료 (필요시)
lsof -ti:포트번호 | xargs -r kill -9
```

### 🚀 전체 서비스 시작 스크립트
```bash
# 1. 백엔드 서비스 시작
cd backend && source venv/bin/activate && python simple_api.py &

# 2. 프론트엔드 시작
cd frontend && npm run dev &

# 3. AI 큐레이션 서비스들 시작
cd services && python simple-curation-service.py --port 8006 &
cd services/ai-model-service && python main.py --port 8007 &
cd services/rag-orchestrator && python main.py --port 8008 &

# 4. 대시보드 시작
cd services/curation-dashboard && npm run dev &
```

### ⚠️ 포트 충돌 방지 가이드라인
1. **신규 서비스 생성 시**: 
   - 위 표에서 미사용(⭕) 포트를 우선 사용
   - 3005-3099 (프론트엔드), 8009-8099 (백엔드) 범위 권장

2. **프로젝트 재실행 시**:
   - 위의 포트 확인 명령어 실행
   - 이미 사용 중인 포트 확인 후 종료 또는 다른 포트 사용

3. **Docker/Podman 서비스**:
   - docker-compose.yml 파일에서 포트 매핑 확인
   - 컨테이너 실행 전 호스트 포트 확인

4. **포트 변경 시**:
   - package.json (프론트엔드)
   - main.py의 uvicorn.run() (백엔드)
   - docker-compose.yml (컨테이너)
   - 환경 변수 파일 (.env)

### 🔄 자동 포트 관리 함수
```bash
# ~/.bashrc 또는 프로젝트 스크립트에 추가
check_sdc_ports() {
  echo "=== SDC 프로젝트 포트 상태 ==="
  for port in 3000 3001 3002 3003 3004 8000 8006 8007 8008; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
      echo "✅ Port $port: 사용 중"
    else
      echo "⭕ Port $port: 사용 가능"
    fi
  done
}

# 사용: check_sdc_ports
```

**중요**: 이 포트 매핑 정보는 프로젝트의 안정적인 운영을 위해 항상 최신 상태로 유지되어야 합니다.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.