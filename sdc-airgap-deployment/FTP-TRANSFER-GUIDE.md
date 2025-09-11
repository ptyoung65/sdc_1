# SDC Air-Gap 배포 - FTP 전송 가이드

## 📦 전송해야 할 파일 목록

### 🎯 전체 디렉토리 (권장)
```bash
# 전체 sdc-airgap-deployment 디렉토리 (12GB)
/home/ptyoung/work/sdc_i/sdc-airgap-deployment/
```

## 📋 주요 구성 요소별 상세

### 1. 🐍 Python 패키지 (3.3GB) - 필수
```
packages/python/
├── *.whl (147개 Python 패키지)
├── *.tar.gz (소스 배포판)
├── manifest.json (패키지 목록 & 체크섬)
├── install_packages.sh (설치 스크립트)
├── pip.conf (오프라인 pip 설정)
└── index.html (로컬 PyPI 인덱스)
```

### 2. 📦 Node.js 패키지 (422MB) - 필수
```
packages/node/
├── repository/ (9개 핵심 npm 패키지)
├── npm-cache/ (npm 캐시 390MB)
├── manifest.json (패키지 목록)
├── install_packages.sh (설치 스크립트)
├── package-lock.json
└── .npmrc (오프라인 npm 설정)
```

### 3. 🐳 컨테이너 이미지 (4.0GB) - 필수
```
images/
├── postgres-16-alpine.tar (PostgreSQL)
├── redis-7-alpine.tar (Redis)
├── milvusdb-milvus-v2.3.3.tar (벡터 DB)
├── elasticsearch-8.11.1.tar (검색 엔진)
├── nginx-1.24-alpine.tar (웹서버)
├── *.tar.sha256 (각 이미지별 체크섬)
└── ... (총 12개 이미지 + 체크섬)
```

### 4. 🤖 AI 모델 (3.9GB) - 필수
```
models/
└── ai-models-venv/ (Korean AI 모델)
    ├── KURE-v1 임베딩 모델
    ├── sentence-transformers 캐시
    └── 한국어 자연어 처리 모델
```

### 5. 🔧 설치 스크립트 (필수)
```
sdc-install-secure.sh (보안 설치 스크립트)
sdc-install.sh (메인 설치 스크립트)  
build-airgap-package.sh (빌드 스크립트)
download-all-images.sh (이미지 로드 스크립트)
```

### 6. ⚙️ 설정 파일 (필수)
```
configs/ (Docker Compose, 환경설정)
docs/ (설치 문서)
PRODUCTION-DEPLOYMENT-COMPLETE.md (완료 보고서)
README.md (전체 가이드)
```

### 7. 🈚 언어 리소스 (선택사항, 8KB)
```
fonts/ (한국어 폰트)
language-resources/ (언어 팩)
```

## 🚀 FTP 전송 방법

### Option 1: 전체 디렉토리 압축 전송 (권장)
```bash
# 1. 전체 디렉토리 압축
cd /home/ptyoung/work/sdc_i/
tar -czf sdc-airgap-complete-$(date +%Y%m%d).tar.gz sdc-airgap-deployment/

# 2. FTP 전송
ftp target-server
put sdc-airgap-complete-20250910.tar.gz
```

### Option 2: 디렉토리 직접 전송
```bash
# SCP 사용 (더 안정적)
scp -r sdc-airgap-deployment/ user@target-server:/opt/

# 또는 rsync 사용
rsync -avz sdc-airgap-deployment/ user@target-server:/opt/sdc-airgap-deployment/
```

### Option 3: 구성요소별 분할 전송
```bash
# 큰 파일들을 분할해서 전송
split -b 1G sdc-airgap-complete.tar.gz sdc-part-
# 결과: sdc-part-aa, sdc-part-ab, sdc-part-ac... (1GB씩)

# 타겟 서버에서 재조립
cat sdc-part-* > sdc-airgap-complete.tar.gz
tar -xzf sdc-airgap-complete.tar.gz
```

## ⚡ 빠른 전송을 위한 우선순위

### 필수 파일 (11.2GB)
1. **packages/** (3.3GB) - Python/Node.js 패키지
2. **images/** (4.0GB) - 컨테이너 이미지  
3. **models/** (3.9GB) - AI 모델
4. **설치 스크립트들** (1MB)
5. **설정 파일들** (1MB)

### 선택적 파일 (8KB)
- fonts/ - 한국어 폰트 (필요시)
- language-resources/ - 추가 언어팩

## 🔐 전송 후 검증

### 타겟 서버에서 실행
```bash
# 1. 압축 해제 후 무결성 검증
cd /opt/sdc-airgap-deployment
./verify-integrity.sh

# 2. 패키지 매니페스트 확인
sha256sum packages/python/manifest.json packages/node/manifest.json

# 3. 컨테이너 이미지 검증
find images/ -name "*.sha256" -exec sha256sum -c {} \;
```

## 📊 전송 크기 요약
```
총 전송 크기: ~12GB
├── Python 패키지: 3.3GB
├── 컨테이너 이미지: 4.0GB  
├── AI 모델: 3.9GB
├── Node.js 패키지: 422MB
└── 설정/스크립트: ~50MB
```

## ⚠️ 주의사항
1. **전송 시간**: 12GB 기준 약 2-4시간 (네트워크 속도에 따라)
2. **디스크 공간**: 타겟 서버에 최소 20GB 여유 공간 필요
3. **권한**: 전송 후 실행 권한 복구 필요 (`chmod +x *.sh`)
4. **검증**: 반드시 전송 후 무결성 검사 실행

---
**전송 준비 완료** ✅  
**Zero Error Tolerance** ✅  
**프로덕션 준비** ✅