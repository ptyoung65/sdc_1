# SDC Microservices Architecture (MSA) Documentation

## 📋 Overview

SDC (Smart Document Companion) 시스템은 완전한 마이크로서비스 아키텍처로 구현되어 있으며, 각 서비스는 독립적으로 배포 및 확장 가능한 컨테이너로 구성되어 있습니다.

## 🏗️ MSA 구성 요소

### 1. RAG 평가 시스템 (RAG Evaluation System)

#### 서비스 구성
```yaml
Services:
  - rag-evaluator (Port: 8006)
  - rag-dashboard (Port: 3001) 
  - rag-postgres (Port: 5433)
  - rag-redis (Port: 6379)
```

#### RAG Evaluator Service
- **목적**: RAG 시스템 성능 평가 및 모니터링
- **포트**: 8006
- **기술 스택**: FastAPI, Python 3.11
- **주요 기능**:
  - 7가지 RAG 성능 지표 계산
  - 실시간 성능 추적
  - 배치 평가 지원
  - 벤치마킹 기능

**평가 메트릭**:
| 메트릭 | 설명 | 계산 방식 |
|--------|------|-----------|
| Context Relevance | 문맥 관련성 | Jaccard 유사도 + 의미적 분석 |
| Context Sufficiency | 문맥 충분성 | 정보 적합성 점수 |
| Answer Relevance | 답변 관련성 | 쿼리-답변 유사도 |
| Answer Correctness | 답변 정확성 | Ground truth와 비교 |
| Hallucination Rate | 환각 비율 | 지원되지 않는 주장 감지 |
| Latency | 지연 시간 | 엔드투엔드 응답 시간 |
| Throughput | 처리량 | 초당 처리 요청 수 |

#### RAG Dashboard Service
- **목적**: RAG 성능 시각화 및 모니터링
- **포트**: 3001
- **기술 스택**: Next.js 14, TypeScript, React
- **주요 기능**:
  - 실시간 메트릭 대시보드
  - 히스토리컬 트렌드 분석
  - 세션별 상세 분석
  - 성능 벤치마킹 뷰

### 2. 벡터 데이터베이스 시스템 (Vector Database System)

#### 서비스 구성
```yaml
Services:
  - vector-db-service (Port: 8003)
  - document-processing-service (Port: 8004)
  - permission-service (Port: 8005)
  - milvus-standalone (Port: 19530)
  - permission-db (PostgreSQL, Port: 5434)
  - milvus-etcd (Internal)
  - milvus-minio (Port: 9000/9001)
  - vector-redis (Port: 6380)
  - vector-proxy (Nginx, Port: 8090)
```

### 3. AI 기반 큐레이션 RAG 파이프라인 (AI-Curated RAG Pipeline)

#### 서비스 구성
```yaml
Services:
  - ai-model-service (Port: 8007)
  - curation-service (Port: 8006)
  - rag-orchestrator (Port: 8008)
  - curation-dashboard (Port: 3002)
  - ollama (Port: 11434)
  - curated-rag-redis (Port: 6381)
  - curated-rag-postgres (Port: 5435)
  - curated-rag-proxy (Nginx, Port: 8091)
```

#### AI Model Service
- **목적**: 다중 AI 모델 관리 및 지능형 모델 선택
- **포트**: 8007
- **기술 스택**: FastAPI, Multiple LLM Providers (OpenAI, Anthropic, Google, Local)
- **주요 기능**:
  - 6개 AI 모델 지원 (GPT-4, Claude, Gemini, Llama-3 등)
  - 자동 모델 선택 및 최적화
  - 쿼리 분석 및 의도 파악
  - 콘텐츠 품질 평가
  - 임베딩 생성 및 모델 비교

**지원 모델**:
| 모델 | 제공업체 | 특성 | 비용/1K토큰 | 지연시간 |
|------|----------|------|-------------|----------|
| GPT-4 | OpenAI | 고품질 추론 | $0.03 | 2000ms |
| Claude-3 Opus | Anthropic | 창의적 분석 | $0.015 | 2500ms |
| Claude-3 Sonnet | Anthropic | 균형잡힌 성능 | $0.003 | 1500ms |
| Gemini Pro | Google | 멀티모달 | $0.001 | 1200ms |
| GPT-3.5 Turbo | OpenAI | 빠른 응답 | $0.002 | 1000ms |
| Llama-3 | Local | 로컬 처리 | 무료 | 500ms |

#### Curation Service
- **목적**: 지능형 콘텐츠 큐레이션 및 품질 관리
- **포트**: 8006
- **기술 스택**: FastAPI, NumPy, Advanced Analytics
- **주요 기능**:
  - 5가지 큐레이션 전략 지원
  - 실시간 콘텐츠 품질 평가
  - 개인화 및 다양성 최적화
  - 시간적 관련성 평가
  - 사용자 프로파일링

**큐레이션 전략**:
| 전략 | 설명 | 사용 사례 |
|------|------|-----------|
| Relevance-Based | 쿼리 관련성 우선 | 정확한 검색 |
| Quality-Based | 콘텐츠 품질 우선 | 신뢰성 중요 |
| Diversity-Based | 다양성 최대화 | 탐색적 검색 |
| Temporal-Based | 최신성 우선 | 뉴스/트렌드 |
| Hybrid | 균형잡힌 조합 | 일반적 사용 |

#### RAG Orchestrator
- **목적**: 지능형 RAG 파이프라인 오케스트레이션
- **포트**: 8008
- **기술 스택**: FastAPI, AsyncIO, Advanced Pipeline Management
- **주요 기능**:
  - 4가지 파이프라인 모드 지원
  - 동적 최적화 전략 적용
  - 실시간 스트리밍 응답
  - 병렬 처리 및 캐싱
  - 성능 모니터링

**파이프라인 모드**:
```mermaid
graph TD
    A[Query Input] --> B{Intent Analysis}
    B -->|Simple| C[Standard Pipeline]
    B -->|Complex| D[Curated Pipeline]
    B -->|Balanced| E[Hybrid Pipeline]
    B -->|Research| F[Experimental Pipeline]
    
    C --> G[Direct Generation]
    D --> H[AI Curation] --> I[Enhanced Generation]
    E --> J[Selective Curation] --> K[Optimized Generation]
    F --> L[Advanced Processing] --> M[Experimental Features]
```

#### Curation Dashboard
- **목적**: 실시간 큐레이션 모니터링 및 테스트
- **포트**: 3002
- **기술 스택**: Next.js 14, React, Recharts, Radix UI
- **주요 기능**:
  - 실시간 성능 대시보드
  - 큐레이션 품질 분석
  - AI 모델 성능 비교
  - 라이브 테스트 인터페이스
  - 메트릭 시각화

**대시보드 탭**:
- **Overview**: 전체 시스템 메트릭
- **Curation**: 큐레이션 성능 분석
- **Pipeline**: 파이프라인 처리 현황
- **AI Models**: 모델별 성능 비교
- **Realtime**: 실시간 테스트 도구

#### Vector DB Service
- **목적**: 벡터 데이터베이스 관리 및 검색
- **포트**: 8003
- **기술 스택**: FastAPI, Milvus, Sentence-Transformers
- **주요 기능**:
  - 384차원 벡터 임베딩
  - 권한 필터링된 벡터 검색
  - 메타데이터 기반 필터링
  - 실시간 인덱싱

**벡터 DB 스키마**:
```python
{
    "id": "doc-123_chunk-01",
    "vector": [384-dimensional float array],
    "text": "chunk content",
    "doc_id": "document UUID",
    "chunk_id": "chunk_001",
    "filename": "document.pdf",
    "access_control_list": ["user-A", "group-B"],
    "roles": ["employee", "manager"],
    "classification": "Confidential",
    "department": "Engineering",
    "project_id": "proj-2024-001",
    "attributes": {"region": "US", "team": "AI"},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "metadata": {}
}
```

#### Document Processing Service
- **목적**: 멀티포맷 문서 처리 및 청킹
- **포트**: 8004
- **기술 스택**: FastAPI, Python-Magic, PyPDF2, Docx2txt
- **주요 기능**:
  - 8가지 문서 포맷 지원 (PDF, DOCX, XLSX, HTML, TXT, CSV, JSON, XML)
  - 3가지 청킹 전략 (Semantic, Sentence, Fixed)
  - 자동 메타데이터 추출
  - 권한 템플릿 적용

**청킹 전략**:
| 전략 | 설명 | 사용 사례 |
|------|------|-----------|
| Semantic | 의미적 단위로 분할 | 구조화된 문서 |
| Sentence | 문장 단위로 분할 | 일반 텍스트 |
| Fixed | 고정 크기로 분할 | 대용량 문서 |

#### Permission Service
- **목적**: RBAC/ABAC 권한 관리
- **포트**: 8005
- **기술 스택**: FastAPI, SQLAlchemy, PostgreSQL
- **주요 기능**:
  - 역할 기반 접근 제어 (RBAC)
  - 속성 기반 접근 제어 (ABAC)
  - 보안 등급 관리 (Public → Top Secret)
  - 부서/프로젝트 기반 권한

**권한 평가 흐름**:
```mermaid
graph LR
    A[사용자 요청] --> B[RBAC 평가]
    B --> C{역할 매치?}
    C -->|Yes| D[접근 허용]
    C -->|No| E[ABAC 평가]
    E --> F{속성 매치?}
    F -->|Yes| D
    F -->|No| G[접근 거부]
```

### 4. 인프라 서비스 (Infrastructure Services)

#### Nginx Reverse Proxy
- **목적**: API 게이트웨이 및 로드 밸런싱
- **포트**: 8090
- **주요 기능**:
  - 통합 API 엔드포인트
  - 서비스 라우팅
  - 헬스 체크 프록시
  - 대용량 파일 업로드 지원 (100MB)

**라우팅 규칙**:
```nginx
/api/v1/search → vector-db-service:8003
/api/v1/process/ → document-processing-service:8004
/api/v1/permissions/ → permission-service:8005
/api/v1/users → permission-service:8005
/health/* → 각 서비스 헬스 체크
```

#### Milvus Vector Database
- **목적**: 고성능 벡터 검색 엔진
- **포트**: 19530 (gRPC), 9091 (메트릭)
- **구성요소**:
  - Milvus Standalone: 벡터 검색 엔진
  - etcd: 메타데이터 저장소
  - MinIO: 벡터 데이터 저장소
- **인덱싱**: IVF_FLAT with nlist=100

#### PostgreSQL Databases
- **Permission DB (Port: 5434)**: 권한 관리 데이터
- **RAG DB (Port: 5433)**: RAG 평가 데이터
- **스키마 관리**: Alembic migrations

#### Redis Cache
- **Vector Redis (Port: 6380)**: 벡터 검색 캐싱
- **RAG Redis (Port: 6379)**: RAG 평가 캐싱
- **용도**: 세션 관리, 결과 캐싱, 레이트 리미팅

## 🚀 배포 및 운영

### Docker Compose 구성

#### RAG 시스템 실행
```bash
# 빌드 및 실행
make -f Makefile.rag-system build
make -f Makefile.rag-system up

# 헬스 체크
make -f Makefile.rag-system health

# 로그 확인
make -f Makefile.rag-system logs
```

#### 벡터 시스템 실행
```bash
# 빌드 및 실행
make -f Makefile.vector-system build
make -f Makefile.vector-system up

# 헬스 체크
make -f Makefile.vector-system health

# 통합 테스트
python3 test-vector-system.py
```

#### AI 큐레이션 RAG 시스템 실행
```bash
# 빌드 및 실행
make -f Makefile.curated-rag build
make -f Makefile.curated-rag up

# 헬스 체크
make -f Makefile.curated-rag health

# 통합 테스트
python3 test-curated-rag.py

# 성능 벤치마크
make -f Makefile.curated-rag benchmark
```

### 서비스 헬스 체크

모든 서비스는 헬스 체크 엔드포인트를 제공합니다:

| 서비스 | 헬스 체크 URL |
|--------|---------------|
| RAG Evaluator | http://localhost:8006/health |
| RAG Dashboard | http://localhost:3001/api/health |
| Vector DB | http://localhost:8003/health |
| Document Processing | http://localhost:8004/health |
| Permission Service | http://localhost:8005/health |
| System Proxy | http://localhost:8090/health |
| **AI 큐레이션 RAG 시스템** |
| AI Model Service | http://localhost:8007/health |
| Curation Service | http://localhost:8006/health |
| RAG Orchestrator | http://localhost:8008/health |
| Curation Dashboard | http://localhost:3002/api/health |
| Curated RAG Proxy | http://localhost:8091/health |

### 컨테이너 리소스 요구사항

| 서비스 | CPU | Memory | 비고 |
|--------|-----|--------|------|
| **벡터 DB 시스템** |
| Milvus | 2 cores | 8GB | 벡터 검색 엔진 |
| Vector DB Service | 1 core | 2GB | API 서버 |
| Document Processing | 1 core | 2GB | 문서 처리 |
| Permission Service | 0.5 core | 1GB | 권한 관리 |
| **AI 큐레이션 RAG 시스템** |
| AI Model Service | 1.5 cores | 3GB | 다중 모델 관리 |
| Curation Service | 1 core | 2GB | 콘텐츠 큐레이션 |
| RAG Orchestrator | 1 core | 2GB | 파이프라인 오케스트레이션 |
| Curation Dashboard | 0.5 core | 1GB | React 대시보드 |
| Ollama | 4 cores | 16GB | 로컬 LLM 서버 |
| **공통 인프라** |
| PostgreSQL | 1 core | 2GB | 데이터베이스 |
| Redis | 0.5 core | 1GB | 캐싱 |
| Nginx | 0.5 core | 512MB | 프록시 |

## 🔧 개발 및 디버깅

### 서비스별 쉘 접근
```bash
# RAG 시스템
make -f Makefile.rag-system shell-evaluator
make -f Makefile.rag-system shell-dashboard

# 벡터 시스템
make -f Makefile.vector-system shell-vector
make -f Makefile.vector-system shell-docs
make -f Makefile.vector-system shell-perm

# AI 큐레이션 RAG 시스템
make -f Makefile.curated-rag shell-orchestrator
make -f Makefile.curated-rag shell-curation
make -f Makefile.curated-rag shell-ai-models
```

### 로그 모니터링
```bash
# 전체 로그
docker-compose -f docker-compose.vector-system.yml logs -f

# 특정 서비스 로그
make -f Makefile.vector-system logs-vector
make -f Makefile.vector-system logs-milvus
```

### 성능 모니터링
```bash
# 리소스 사용량
make -f Makefile.vector-system stats

# 성능 테스트
make -f Makefile.vector-system perf-test
```

## 📊 API 엔드포인트 요약

### RAG 평가 API
- `POST /api/v1/evaluate` - RAG 세션 평가
- `GET /api/v1/metrics/{session_id}` - 세션 메트릭 조회
- `POST /api/v1/benchmark` - 벤치마킹 실행
- `GET /api/v1/history` - 평가 히스토리

### 벡터 검색 API
- `POST /api/v1/search` - 권한 필터링 벡터 검색
- `POST /api/v1/ingest` - 문서 벡터 저장
- `GET /api/v1/stats` - 컬렉션 통계

### 문서 처리 API
- `POST /api/v1/process/upload` - 문서 업로드 및 처리
- `GET /api/v1/formats` - 지원 포맷 목록
- `GET /api/v1/chunking/templates` - 청킹 템플릿

### 권한 관리 API
- `POST /api/v1/permissions/evaluate` - 권한 평가
- `POST /api/v1/users` - 사용자 생성
- `GET /api/v1/roles` - 역할 관리
- `POST /api/v1/policies` - ABAC 정책 관리

### AI 큐레이션 RAG API
- `POST /api/v1/curate` - 콘텐츠 큐레이션 실행
- `POST /api/v1/process` - RAG 파이프라인 처리
- `POST /api/v1/generate` - AI 텍스트 생성
- `POST /api/v1/analyze_query` - 쿼리 분석 및 의도 파악
- `POST /api/v1/assess_quality` - 콘텐츠 품질 평가
- `POST /api/v1/embeddings` - 임베딩 생성
- `GET /api/v1/models` - 사용 가능한 AI 모델 목록
- `GET /api/v1/strategies` - 큐레이션 전략 목록
- `GET /api/v1/pipelines` - 파이프라인 구성 정보
- `POST /api/v1/compare_models` - AI 모델 성능 비교
- `GET /api/v1/performance` - 성능 메트릭 조회
- `GET /api/v1/metrics` - 서비스별 메트릭 조회
- `POST /api/v1/optimize` - 파이프라인 최적화

## 🔒 보안 고려사항

### 네트워크 격리
- 모든 서비스는 독립된 Docker 네트워크에서 실행
- 외부 접근은 Nginx 프록시를 통해서만 가능
- 내부 서비스 간 통신은 서비스 이름 사용

### 인증 및 권한
- JWT 기반 인증 (Permission Service)
- RBAC/ABAC 다층 권한 체계
- API 키 기반 서비스 간 인증

### 데이터 보안
- PostgreSQL 데이터 암호화
- Redis AOF 영속성
- MinIO 객체 저장소 접근 제어

## 🚦 프로덕션 배포 가이드

### 1. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수
DATABASE_URL=postgresql://user:pass@host:5432/db
MILVUS_HOST=milvus-production
JWT_SECRET_KEY=your-secret-key
REDIS_URL=redis://redis:6379
```

### 2. 컨테이너 레지스트리 설정
```bash
# 이미지 태깅
docker tag services-vector-db-service:latest registry.company.com/vector-db:v1.0.0

# 레지스트리 푸시
docker push registry.company.com/vector-db:v1.0.0
```

### 3. Kubernetes 배포
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vector-db-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vector-db
  template:
    metadata:
      labels:
        app: vector-db
    spec:
      containers:
      - name: vector-db
        image: registry.company.com/vector-db:v1.0.0
        ports:
        - containerPort: 8003
        env:
        - name: MILVUS_HOST
          value: "milvus-service"
```

### 4. 모니터링 설정
- Prometheus 메트릭 수집
- Grafana 대시보드 구성
- ELK 스택 로그 집계
- Jaeger 분산 트레이싱

## 📈 확장성 고려사항

### 수평 확장
- **API 서비스**: 로드 밸런서 뒤에 다중 인스턴스 배포
- **Milvus**: 클러스터 모드로 전환
- **PostgreSQL**: 읽기 복제본 추가
- **Redis**: Redis Cluster 구성

### 성능 최적화
- **캐싱 전략**: Redis 캐시 적극 활용
- **인덱싱**: Milvus IVF_FLAT → IVF_PQ 전환
- **청킹 크기**: 문서 타입별 최적화
- **배치 처리**: 대량 문서 처리 시 배치 API 사용

## 🎯 결론

SDC MSA 시스템은 완전히 컨테이너화된 마이크로서비스 아키텍처로 구현되어 있으며, 각 서비스는 독립적으로 개발, 배포, 확장이 가능합니다. **3개의 주요 시스템**이 완벽하게 통합되어 엔터프라이즈급 AI 서비스를 제공합니다.

### 🏆 완성된 3대 MSA 시스템

#### 1️⃣ **RAG 평가 시스템** (Ports: 8006, 3001)
- 7가지 성능 지표로 RAG 품질 측정
- 실시간 대시보드와 벤치마킹 도구
- 히스토리컬 분석 및 트렌드 모니터링

#### 2️⃣ **벡터 데이터베이스 시스템** (Ports: 8003-8005, 8090)
- Milvus 기반 고성능 벡터 검색
- RBAC/ABAC 엔터프라이즈 권한 관리
- 멀티포맷 문서 처리 및 청킹

#### 3️⃣ **AI 기반 큐레이션 RAG 파이프라인** (Ports: 8006-8008, 3002, 8091) ⭐ **NEW**
- 6개 AI 모델 통합 관리 (GPT-4, Claude, Gemini, Llama-3 등)
- 5가지 지능형 큐레이션 전략
- 4가지 파이프라인 모드 (Standard, Curated, Hybrid, Experimental)
- 실시간 스트리밍 및 성능 최적화
- 포괄적인 모니터링 대시보드

### 🚀 핵심 특징
- ✅ **완전한 MSA 구현** (총 20+ 마이크로서비스)
- ✅ **Docker Compose 오케스트레이션** (3개 독립 시스템)
- ✅ **엔터프라이즈급 보안** (RBAC/ABAC + JWT)
- ✅ **고성능 벡터 검색** (Milvus + 권한 필터링)
- ✅ **AI 기반 지능형 큐레이션** ⭐ **NEW**
- ✅ **다중 AI 모델 통합** (OpenAI, Anthropic, Google, Local) ⭐ **NEW**
- ✅ **포괄적인 모니터링 및 평가**
- ✅ **프로덕션 레디 아키텍처**

### 📈 시스템 규모
- **총 서비스 수**: 20개 이상 마이크로서비스
- **지원 AI 모델**: 6개 (GPT-4, Claude-3, Gemini 등)
- **큐레이션 전략**: 5가지 (Relevance, Quality, Diversity, Temporal, Hybrid)
- **파이프라인 모드**: 4가지 (Standard, Curated, Hybrid, Experimental)
- **문서 포맷**: 8가지 (PDF, DOCX, XLSX, HTML, TXT, CSV, JSON, XML)
- **총 포트**: 15개 (8006-8008, 3001-3002, 8090-8091, 5433-5435, 6379-6381, 11434, 19530)

### 🎛️ 관리 및 운영
```bash
# 전체 시스템 순서대로 시작
make -f Makefile.rag-system up          # RAG 평가 시스템
make -f Makefile.vector-system up       # 벡터 DB 시스템  
make -f Makefile.curated-rag up         # AI 큐레이션 시스템

# 통합 헬스 체크
make -f Makefile.rag-system health
make -f Makefile.vector-system health
make -f Makefile.curated-rag health

# 통합 테스트
python3 test-rag-system.py
python3 test-vector-system.py  
python3 test-curated-rag.py
```

### 📊 접속 URL
- **RAG 대시보드**: http://localhost:3001
- **큐레이션 대시보드**: http://localhost:3002 ⭐ **NEW**
- **벡터 시스템 API**: http://localhost:8090
- **큐레이션 시스템 API**: http://localhost:8091 ⭐ **NEW**

### 🔗 문의 및 지원
- **기술 문서**: `/services/README-*.md`, `MSA.md`
- **API 문서**: 각 서비스의 `/docs` 엔드포인트
- **테스트 스크립트**: `test-*.py` (3개 시스템)
- **관리 도구**: `Makefile.*` (3개 시스템)
- **Docker 구성**: `docker-compose.*.yml` (3개 시스템)