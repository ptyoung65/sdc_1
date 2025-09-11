# SDC Air-Gap 배포 가이드
Version: 1.0.0  
Date: 2025-09-10

## 🎯 개요

이 가이드는 인터넷이 차단된 air-gap 환경에서 SDC(Smart Document Companion) 플랫폼을 완전히 오프라인으로 설치하는 방법을 설명합니다.

## 📋 사전 준비사항

### 개발 시스템 (인터넷 연결 필요)
- **OS**: Ubuntu 20.04+, RHEL 8+, CentOS 8+
- **CPU**: 8코어 이상
- **RAM**: 16GB 이상  
- **디스크**: 50GB 이상 여유 공간
- **소프트웨어**: Podman 4.0+, Node.js 20+, Python 3.11+, Git

### 대상 시스템 (Air-gap 환경)
- **OS**: Linux (동일 배포판 권장)
- **CPU**: 8코어 이상
- **RAM**: 16GB 이상
- **디스크**: 100GB 이상 여유 공간
- **소프트웨어**: Podman 4.0+ (사전 설치 필수)
- **네트워크**: 완전 격리된 환경

## 🏗️ 단계 1: 배포 패키지 생성 (인터넷 환경)

### 1-1. 소스 코드 준비
```bash
# 프로젝트 클론 및 이동
git clone <SDC_REPOSITORY>
cd sdc_i

# Air-gap 배포 디렉토리로 이동
cd sdc-airgap-deployment
```

### 1-2. 빌드 스크립트 실행
```bash
# 전체 빌드 (권장)
./build-airgap-package.sh full

# 또는 고압축 빌드 (시간 더 소요, 크기 최적화)
COMPRESS_LEVEL=9 ./build-airgap-package.sh full

# 또는 빠른 개발 빌드
SKIP_TESTS=true COMPRESS_LEVEL=1 ./build-airgap-package.sh full
```

### 1-3. 빌드 과정 모니터링
빌드 과정은 다음 단계로 진행됩니다:
1. **환경 검증** (8%) - 시스템 요구사항 확인
2. **빌드 환경 준비** (16%) - 디렉토리 구조 생성
3. **소스 코드 복사** (25%) - Frontend, Backend, Services 복사
4. **컨테이너 이미지 추출** (33%) - 17개 이미지 빌드/추출
5. **Python 패키지 번들링** (41%) - ~150개 wheel 파일 다운로드
6. **Node.js 패키지 번들링** (50%) - ~80개 패키지 다운로드
7. **설정 템플릿 생성** (58%) - 프로덕션 설정 파일 생성
8. **데이터베이스 스크립트 생성** (66%) - PostgreSQL/Redis 초기화
9. **문서 복사** (75%) - 설치/운영 가이드 포함
10. **체크섬 생성** (83%) - 파일 무결성 검증 데이터
11. **최종 패키지 압축** (91%) - tar.gz 압축 생성
12. **패키지 테스트** (100%) - 무결성 및 구문 검사

### 1-4. 빌드 결과 확인
```bash
# 생성된 패키지 확인
ls -la build/sdc-airgap-*.tar.gz

# 패키지 정보 확인
cat build/sdc-airgap-*.tar.gz.info

# 체크섬 확인
sha256sum build/sdc-airgap-*.tar.gz
```

## 📦 단계 2: 패키지 전송

### 2-1. USB/외장 저장매체 사용
```bash
# USB 마운트
sudo mount /dev/sdX1 /mnt/usb

# 패키지 복사
cp build/sdc-airgap-*.tar.gz /mnt/usb/
cp build/sdc-airgap-*.tar.gz.info /mnt/usb/

# 안전하게 언마운트
sudo umount /mnt/usb
```

### 2-2. 네트워크 전송 (허용된 경우)
```bash
# SCP 전송
scp build/sdc-airgap-*.tar.gz user@target-server:/tmp/

# rsync 전송
rsync -avz --progress build/sdc-airgap-*.tar.gz user@target-server:/tmp/
```

## 🚀 단계 3: Air-gap 환경에서 설치

### 3-1. 패키지 검증 및 압축 해제
```bash
# 패키지 이동
cd /tmp  # 또는 적절한 임시 디렉토리

# 체크섬 검증 (권장)
sha256sum sdc-airgap-*.tar.gz

# 압축 해제
tar -xzf sdc-airgap-*.tar.gz
cd sdc-airgap-*

# 구조 확인
ls -la
```

### 3-2. 설치 실행

#### 🔒 보안 강화 설치 (권장)
```bash
# 보안 강화 설치 스크립트 실행
sudo ./sdc-install-secure.sh
```

설치 과정에서 다음 정보 입력 요구:
- **압축 해제 디렉토리**: 임시 파일 저장 위치
- **설치 디렉토리**: 최종 설치 위치 (기본값: `/opt/sdc`)
- **관리자 이메일**: 시스템 알림용 이메일 주소

#### 📋 표준 설치 (대안)
```bash
# 표준 설치 스크립트 실행
sudo ./sdc-install.sh
```

### 3-3. 설치 과정 모니터링
설치는 다음 단계로 진행됩니다:
1. **권한 확인** - sudo 권한 및 사용자 검증
2. **보안 초기화** - 크리덴셜 자동 생성
3. **시스템 검증** - 하드웨어/소프트웨어 요구사항 확인
4. **사용자 입력** - 설치 경로 및 설정 확인
5. **포트 확인** - 포트 충돌 검사 및 해결
6. **네트워크 설정** - 격리된 컨테이너 네트워크 생성
7. **패키지 추출** - 설치 파일 압축 해제
8. **파일 검증** - SHA256 체크섬 확인
9. **이미지 로드** - 컨테이너 이미지 Podman에 로드
10. **Python 설치** - 가상환경 생성 및 패키지 설치
11. **Node.js 설치** - npm 패키지 오프라인 설치
12. **소스 복사** - 애플리케이션 소스 코드 배포
13. **환경 설정** - .env 파일 및 보안 설정 생성
14. **데이터베이스 초기화** - PostgreSQL/Redis 설정 및 마이그레이션
15. **서비스 시작** - 모든 서비스 컨테이너 시작
16. **헬스 체크** - 서비스 상태 검증
17. **보고서 생성** - 설치 완료 보고서 생성

## 🔐 단계 4: 보안 설정 (중요!)

### 4-1. 크리덴셜 관리
```bash
# 생성된 크리덴셜 파일 확인 (설치 중 표시됨)
cat /tmp/sdc-secure-*/credentials.enc

# 크리덴셜 파일을 안전한 위치로 이동
sudo mv /tmp/sdc-secure-*/credentials.enc /opt/sdc/credentials.enc
sudo chmod 600 /opt/sdc/credentials.enc
```

### 4-2. 기본 패스워드 변경
```bash
# SDC 웹 인터페이스 접속 후
# 1. http://localhost:3000 접속
# 2. 설치 보고서에서 제공된 admin 크리덴셜로 로그인
# 3. 즉시 패스워드 변경
```

### 4-3. AI 서비스 API 키 설정
```bash
# 환경 파일 편집
sudo nano /opt/sdc/.env

# 다음 항목들 설정
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# 서비스 재시작
cd /opt/sdc
sudo podman-compose restart
```

## ✅ 단계 5: 설치 검증

### 5-1. 서비스 상태 확인
```bash
# 컨테이너 상태 확인
podman ps

# 서비스 헬스 체크
curl http://localhost:3000      # Frontend
curl http://localhost:8000/health   # Backend API
curl http://localhost:3003      # Admin Panel
```

### 5-2. 로그 확인
```bash
# 애플리케이션 로그
tail -f /var/log/sdc/app.log

# 설치 로그
cat /opt/sdc/installation_report.md

# 에러 로그 (문제 발생 시)
cat install_err.md
```

### 5-3. 데이터베이스 연결 확인
```bash
# PostgreSQL 연결 테스트
PGPASSWORD='<DB_PASSWORD>' psql -h localhost -U sdc_user -d sdc_db -c "SELECT 1;"

# Redis 연결 테스트
redis-cli ping
```

## 🛠️ 문제 해결

### 일반적인 문제들

#### 포트 충돌
```bash
# 포트 사용 확인
ss -tuln | grep -E ":(3000|8000|5432|6379)"

# 충돌하는 프로세스 종료
sudo lsof -ti:3000 | xargs -r kill -9
```

#### 권한 문제
```bash
# 파일 소유권 수정
sudo chown -R $USER:$USER /opt/sdc

# SELinux 컨텍스트 복원 (RHEL/CentOS)
sudo restorecon -Rv /opt/sdc
```

#### 컨테이너 문제
```bash
# 컨테이너 상태 확인
podman ps -a

# 컨테이너 로그 확인
podman logs sdc-backend
podman logs sdc-postgres

# 서비스 재시작
podman restart sdc-backend
```

#### 메모리 부족
```bash
# 메모리 사용량 확인
free -h
podman stats

# 컨테이너 메모리 제한 확인/조정
# docker-compose.yml에서 memory limits 설정
```

## 📊 시스템 사양 및 성능

### 예상 리소스 사용량
- **디스크**: 60-80GB (압축 해제 후)
- **RAM**: 8-16GB (정상 운영)
- **CPU**: 4-8코어 (동시 사용자 50명 기준)

### 성능 최적화
```bash
# PostgreSQL 최적화
sudo -u postgres psql -d sdc_db -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
"

# Redis 메모리 제한 설정
redis-cli CONFIG SET maxmemory 512mb
```

## 🔄 업데이트 프로세스

### 새 버전 배포
1. 인터넷 환경에서 새 패키지 빌드
2. Air-gap 환경으로 전송
3. 기존 시스템 백업
4. 새 패키지로 업그레이드 설치

### 백업 절차
```bash
# 데이터베이스 백업
pg_dump -h localhost -U sdc_user sdc_db > /backup/sdc_db_$(date +%Y%m%d).sql

# 설정 파일 백업
cp -r /opt/sdc/.env /backup/

# 애플리케이션 데이터 백업
tar -czf /backup/sdc_data_$(date +%Y%m%d).tar.gz /opt/sdc/data/
```

## 📞 지원 및 유지보수

### 로그 파일 위치
- **설치 로그**: `install_*.log`
- **애플리케이션 로그**: `/var/log/sdc/app.log`
- **감사 로그**: `/var/log/sdc/audit.log`
- **컨테이너 로그**: `podman logs <container_name>`

### 모니터링 명령어
```bash
# 시스템 상태 종합 체크
curl -s http://localhost:8000/health | jq '.'

# 리소스 모니터링
htop
podman stats
df -h

# 서비스 상태
systemctl status sdc-backend
systemctl status sdc-frontend
```

---

## 🎯 요약

1. **인터넷 환경**: `./build-airgap-package.sh full` 실행
2. **패키지 전송**: USB/네트워크로 air-gap 시스템에 전송
3. **압축 해제**: `tar -xzf sdc-airgap-*.tar.gz`
4. **보안 설치**: `sudo ./sdc-install-secure.sh`
5. **보안 설정**: 크리덴셜 관리 및 패스워드 변경
6. **검증**: 서비스 상태 및 접속 확인

완전한 오프라인 환경에서 SDC 플랫폼이 성공적으로 설치됩니다!

**접속 URL**:
- 메인 애플리케이션: http://localhost:3000
- API 문서: http://localhost:8000/docs
- 관리자 패널: http://localhost:3003

**중요**: 설치 완료 후 반드시 기본 패스워드를 변경하고 API 키를 설정하세요!