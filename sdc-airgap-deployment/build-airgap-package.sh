#!/bin/bash
# SDC Air-Gap Package Builder
# Version: 1.0.0
# Description: Master script to build complete air-gap deployment package

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
BUILD_DIR="${SCRIPT_DIR}/build"
PACKAGE_NAME="sdc-airgap-$(date +%Y%m%d_%H%M%S)"
FINAL_PACKAGE="${BUILD_DIR}/${PACKAGE_NAME}.tar.gz"
LOG_FILE="${SCRIPT_DIR}/build.log"

# Build configuration
BUILD_MODE="${1:-full}"  # full, images-only, packages-only, test
SKIP_TESTS="${SKIP_TESTS:-false}"
COMPRESS_LEVEL="${COMPRESS_LEVEL:-6}"

# Logging functions
log() {
    echo -e "${2:-}$1${NC}"
    echo -e "$1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
    echo -e "[ERROR] $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
    echo -e "[SUCCESS] $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
    echo -e "[WARNING] $1" >> "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
    echo -e "[INFO] $1" >> "$LOG_FILE"
}

# Progress tracking
BUILD_STEPS=(
    "validate_environment"
    "prepare_build_environment"
    "copy_source_code"
    "export_container_images"
    "bundle_python_packages"
    "bundle_node_packages"
    "create_configuration_templates"
    "create_database_scripts"
    "copy_documentation"
    "generate_checksums"
    "create_final_package"
    "test_package"
)

CURRENT_STEP=0

update_progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    local PROGRESS=$((CURRENT_STEP * 100 / ${#BUILD_STEPS[@]}))
    log_info "Progress: $PROGRESS% (Step $CURRENT_STEP/${#BUILD_STEPS[@]})"
}

# Validate build environment
validate_environment() {
    log_info "Validating build environment..."
    update_progress
    
    # Check required commands
    local REQUIRED_COMMANDS=("tar" "gzip" "sha256sum" "find" "cp" "podman" "npm" "python3" "pip3")
    local MISSING_COMMANDS=()
    
    for CMD in "${REQUIRED_COMMANDS[@]}"; do
        if ! command -v "$CMD" &> /dev/null; then
            MISSING_COMMANDS+=("$CMD")
        fi
    done
    
    if [ ${#MISSING_COMMANDS[@]} -gt 0 ]; then
        log_error "Missing required commands: ${MISSING_COMMANDS[*]}"
        return 1
    fi
    
    # Check project structure
    local REQUIRED_DIRS=(
        "$PROJECT_ROOT/frontend"
        "$PROJECT_ROOT/backend"
        "$PROJECT_ROOT/services"
    )
    
    for DIR in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "$DIR" ]; then
            log_error "Required directory not found: $DIR"
            return 1
        fi
    done
    
    # Check available disk space
    local AVAILABLE_SPACE=$(df -BG "$SCRIPT_DIR" | awk 'NR==2 {print int($4)}')
    if [ "$AVAILABLE_SPACE" -lt 20 ]; then
        log_error "Insufficient disk space: ${AVAILABLE_SPACE}GB (required: 20GB+)"
        return 1
    fi
    
    log_success "Environment validation complete ✓"
}

# Prepare build environment
prepare_build_environment() {
    log_info "Preparing build environment..."
    update_progress
    
    # Clean previous build
    if [ -d "$BUILD_DIR" ]; then
        log_warning "Removing previous build directory..."
        rm -rf "$BUILD_DIR"
    fi
    
    # Create build structure
    mkdir -p "$BUILD_DIR"/{scripts,images,packages/{python,node},source,configs,data/{sql,migrations},docs}
    
    # Copy scripts
    log_info "Copying build scripts..."
    cp "${SCRIPT_DIR}/scripts/"*.sh "$BUILD_DIR/scripts/"
    cp "${SCRIPT_DIR}/sdc-install.sh" "$BUILD_DIR/"
    cp "${SCRIPT_DIR}/sdc-install-secure.sh" "$BUILD_DIR/"
    
    # Make scripts executable
    chmod +x "$BUILD_DIR/scripts/"*.sh
    chmod +x "$BUILD_DIR/"*.sh
    
    log_success "Build environment prepared ✓"
}

# Copy source code
copy_source_code() {
    log_info "Copying source code..."
    update_progress
    
    # Copy frontend
    if [ -d "$PROJECT_ROOT/frontend" ]; then
        log_info "Copying frontend source..."
        cp -r "$PROJECT_ROOT/frontend" "$BUILD_DIR/source/"
        
        # Clean frontend build artifacts
        find "$BUILD_DIR/source/frontend" -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
        find "$BUILD_DIR/source/frontend" -name ".next" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # Copy backend
    if [ -d "$PROJECT_ROOT/backend" ]; then
        log_info "Copying backend source..."
        cp -r "$PROJECT_ROOT/backend" "$BUILD_DIR/source/"
        
        # Clean Python artifacts
        find "$BUILD_DIR/source/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find "$BUILD_DIR/source/backend" -name "*.pyc" -delete 2>/dev/null || true
        find "$BUILD_DIR/source/backend" -name "venv" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # Copy services
    if [ -d "$PROJECT_ROOT/services" ]; then
        log_info "Copying services source..."
        cp -r "$PROJECT_ROOT/services" "$BUILD_DIR/source/"
        
        # Clean service artifacts
        find "$BUILD_DIR/source/services" -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
        find "$BUILD_DIR/source/services" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    log_success "Source code copied ✓"
}

# Export container images
export_container_images() {
    if [ "$BUILD_MODE" = "packages-only" ]; then
        log_info "Skipping image export (packages-only mode)"
        update_progress
        return 0
    fi
    
    log_info "Exporting container images..."
    update_progress
    
    # Set target directory for images
    export IMAGE_DIR="$BUILD_DIR/images"
    
    cd "$SCRIPT_DIR/scripts"
    if ./export_images.sh --build-only; then
        log_success "Container images exported ✓"
    else
        log_error "Failed to export container images"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
}

# Bundle Python packages
bundle_python_packages() {
    if [ "$BUILD_MODE" = "images-only" ]; then
        log_info "Skipping Python packages (images-only mode)"
        update_progress
        return 0
    fi
    
    log_info "Bundling Python packages..."
    update_progress
    
    # Set target directory for Python packages
    export PACKAGE_DIR="$BUILD_DIR/packages/python"
    
    cd "$SCRIPT_DIR/scripts"
    if ./bundle_python_packages.sh; then
        log_success "Python packages bundled ✓"
    else
        log_error "Failed to bundle Python packages"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
}

# Bundle Node.js packages
bundle_node_packages() {
    if [ "$BUILD_MODE" = "images-only" ]; then
        log_info "Skipping Node.js packages (images-only mode)"
        update_progress
        return 0
    fi
    
    log_info "Bundling Node.js packages..."
    update_progress
    
    # Set target directory for Node packages
    export PACKAGE_DIR="$BUILD_DIR/packages/node"
    
    cd "$SCRIPT_DIR/scripts"
    if ./bundle_node_packages.sh; then
        log_success "Node.js packages bundled ✓"
    else
        log_error "Failed to bundle Node.js packages"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
}

# Create configuration templates
create_configuration_templates() {
    log_info "Creating configuration templates..."
    update_progress
    
    # Create environment template
    cat > "$BUILD_DIR/configs/env.template" <<'EOF'
# SDC Environment Configuration Template
# Copy this file to .env and configure for your environment

# Application Settings
APP_ENV=production
APP_DEBUG=false
APP_URL=http://localhost:3000

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sdc_db
DB_USER=sdc_user
DB_PASSWORD=CHANGE_ME_SECURE_PASSWORD

# Security Configuration  
JWT_SECRET=CHANGE_ME_64_CHAR_JWT_SECRET
JWT_EXPIRATION=3600
SESSION_SECRET=CHANGE_ME_32_CHAR_SESSION_SECRET
ENCRYPTION_KEY=CHANGE_ME_32_CHAR_ENCRYPTION_KEY

# Admin Configuration
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=CHANGE_ME_SECURE_ADMIN_PASSWORD

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_ME_REDIS_PASSWORD

# AI Service API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# Service Ports
FRONTEND_PORT=3000
BACKEND_PORT=8000
ADMIN_PANEL_PORT=3003
CURATION_DASHBOARD_PORT=3004

# Security Settings
CORS_ORIGINS=http://localhost:3000
CSRF_PROTECTION=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=info
LOG_FILE=/var/log/sdc/app.log
AUDIT_LOG=/var/log/sdc/audit.log
EOF
    
    # Create Docker Compose template
    cat > "$BUILD_DIR/configs/docker-compose.yml" <<'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: sdc-postgres
    environment:
      POSTGRES_USER: sdc_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: sdc_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./data/sql:/docker-entrypoint-initdb.d
    networks:
      - sdc-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: sdc-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - sdc-network
    restart: unless-stopped

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.1
    container_name: sdc-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - sdc-network
    restart: unless-stopped

  milvus:
    image: milvusdb/milvus:v2.3.3
    container_name: sdc-milvus
    ports:
      - "19530:19530"
    volumes:
      - milvus_data:/var/lib/milvus
    networks:
      - sdc-network
    restart: unless-stopped

  backend:
    image: sdc-backend:latest
    container_name: sdc-backend
    environment:
      - DATABASE_URL=postgresql://sdc_user:${DB_PASSWORD}@postgres:5432/sdc_db
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    volumes:
      - ./backend:/app
      - app_logs:/var/log/sdc
    depends_on:
      - postgres
      - redis
    networks:
      - sdc-network
    restart: unless-stopped

  frontend:
    image: sdc-frontend:latest
    container_name: sdc-frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:${BACKEND_PORT:-8000}
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    volumes:
      - ./frontend:/app
    depends_on:
      - backend
    networks:
      - sdc-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  milvus_data:
  app_logs:

networks:
  sdc-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF
    
    # Create nginx configuration
    cat > "$BUILD_DIR/configs/nginx.conf" <<'EOF'
# SDC Nginx Configuration
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;
    
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/m;
    
    # Upstream servers
    upstream backend {
        server localhost:8000;
        keepalive 32;
    }
    
    upstream frontend {
        server localhost:3000;
        keepalive 32;
    }
    
    # Main server block
    server {
        listen 80;
        server_name localhost;
        
        # Security
        server_tokens off;
        
        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }
        
        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers
            add_header Access-Control-Allow-Origin "http://localhost:3000";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type";
        }
        
        # Login endpoint with stricter rate limiting
        location /api/auth/login {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Error pages
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
EOF
    
    log_success "Configuration templates created ✓"
}

# Create database scripts
create_database_scripts() {
    log_info "Creating database initialization scripts..."
    update_progress
    
    # Create PostgreSQL initialization script
    cat > "$BUILD_DIR/data/sql/01_init.sql" <<'EOF'
-- SDC Database Initialization
-- This script sets up the initial database structure

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    content_type VARCHAR(100),
    file_size INTEGER,
    file_hash VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_content_type ON documents(content_type);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create default admin user (password: admin123)
INSERT INTO users (email, password_hash, is_admin) 
VALUES (
    'admin@sdc.local', 
    crypt('admin123', gen_salt('bf')), 
    true
) ON CONFLICT (email) DO NOTHING;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
EOF
    
    # Create Redis initialization script
    cat > "$BUILD_DIR/data/redis-init.conf" <<'EOF'
# Redis Configuration for SDC
# Security and performance settings

# Security
protected-mode yes
bind 127.0.0.1
port 6379
timeout 300

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis.log

# Performance
tcp-keepalive 300
tcp-backlog 511
databases 16

# Security settings
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG "CONFIG_9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
EOF
    
    log_success "Database scripts created ✓"
}

# Copy documentation
copy_documentation() {
    log_info "Copying documentation..."
    update_progress
    
    # Copy existing documentation
    if [ -f "$PROJECT_ROOT/README.md" ]; then
        cp "$PROJECT_ROOT/README.md" "$BUILD_DIR/docs/"
    fi
    
    if [ -f "$PROJECT_ROOT/CLAUDE.md" ]; then
        cp "$PROJECT_ROOT/CLAUDE.md" "$BUILD_DIR/docs/"
    fi
    
    # Copy requirements document
    cp "$PROJECT_ROOT/req.md" "$BUILD_DIR/docs/"
    cp "$PROJECT_ROOT/file-inventory-checklist.md" "$BUILD_DIR/docs/"
    
    # Create installation guide
    cat > "$BUILD_DIR/docs/INSTALL.md" <<'EOF'
# SDC Air-Gap Installation Guide

## Prerequisites

- Linux system (Ubuntu 20.04+, RHEL 8+, or similar)
- Minimum 8 CPU cores, 16GB RAM, 100GB disk space
- Podman 4.0+ or Docker 20.10+
- Root or sudo access

## Installation Steps

### 1. Extract Package

```bash
tar -xzf sdc-airgap-*.tar.gz
cd sdc-airgap-*
```

### 2. Run Installation

For standard installation:
```bash
sudo ./sdc-install.sh
```

For security-hardened installation:
```bash
sudo ./sdc-install-secure.sh
```

### 3. Follow Prompts

The installer will ask for:
- Extraction directory (temporary)
- Installation directory (permanent)
- Admin email address

### 4. Post-Installation

1. Access the application at http://localhost:3000
2. Login with admin credentials (see installation report)
3. Configure API keys in .env file
4. Change default passwords immediately

## Troubleshooting

Check these files for issues:
- `install.log` - Installation log
- `install_err.md` - Error details
- `/var/log/sdc/app.log` - Application log

## Security Notes

- Change all default passwords immediately
- Configure SSL/TLS certificates
- Review firewall settings
- Enable audit logging
- Set up regular backups

## Support

For technical support, please review:
- `TROUBLESHOOTING.md`
- Error logs
- Project documentation
EOF
    
    # Create troubleshooting guide
    cat > "$BUILD_DIR/docs/TROUBLESHOOTING.md" <<'EOF'
# SDC Troubleshooting Guide

## Common Installation Issues

### 1. Port Conflicts

**Problem**: Services fail to start due to port conflicts

**Solution**:
```bash
# Check port usage
ss -tuln | grep -E ":(3000|8000|5432|6379)"

# Kill processes using required ports
sudo lsof -ti:3000 | xargs -r kill -9
```

### 2. Permission Errors

**Problem**: Permission denied errors during installation

**Solution**:
```bash
# Ensure proper ownership
sudo chown -R $USER:$USER /opt/sdc

# Fix SELinux contexts (RHEL/CentOS)
sudo restorecon -Rv /opt/sdc
```

### 3. Container Issues

**Problem**: Podman/Docker containers fail to start

**Solution**:
```bash
# Check container status
podman ps -a

# View container logs
podman logs sdc-backend

# Restart services
podman restart sdc-backend sdc-frontend
```

### 4. Database Connection Issues

**Problem**: Application cannot connect to database

**Solution**:
```bash
# Check PostgreSQL status
podman exec sdc-postgres pg_isready

# Test connection
PGPASSWORD=your_password psql -h localhost -U sdc_user -d sdc_db -c "SELECT 1;"

# Check database logs
podman logs sdc-postgres
```

### 5. Out of Memory Errors

**Problem**: Services crash due to insufficient memory

**Solution**:
```bash
# Check memory usage
free -h
podman stats

# Adjust container memory limits in docker-compose.yml
# Add memory limits to service definitions
```

## Performance Optimization

### 1. Resource Allocation

- Increase memory limits for AI services
- Use SSD storage for database
- Allocate adequate CPU cores

### 2. Database Tuning

```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### 3. Redis Optimization

```bash
# Increase Redis memory limit
redis-cli CONFIG SET maxmemory 512mb
```

## Logs and Monitoring

### Important Log Files

- `/var/log/sdc/app.log` - Application logs
- `/var/log/sdc/audit.log` - Security audit log
- `~/.local/share/containers/storage/logs/` - Container logs

### Monitoring Commands

```bash
# Check service health
curl -s http://localhost:8000/health

# Monitor containers
podman stats

# Check disk usage
df -h /opt/sdc
```

## Recovery Procedures

### 1. Database Recovery

```bash
# Backup database
pg_dump -h localhost -U sdc_user sdc_db > backup.sql

# Restore database
psql -h localhost -U sdc_user -d sdc_db < backup.sql
```

### 2. Service Recovery

```bash
# Restart all services
cd /opt/sdc
podman-compose down
podman-compose up -d
```

### 3. Configuration Recovery

```bash
# Restore from backup
cp /opt/sdc/.env.backup /opt/sdc/.env

# Regenerate secrets
openssl rand -hex 32 > new_jwt_secret
```

## Getting Help

1. Check installation logs: `install_err.md`
2. Review system logs: `journalctl -f`
3. Test connectivity: Use health check endpoints
4. Validate configuration: Check .env file
5. Monitor resources: Check CPU, memory, disk usage

For additional support, please provide:
- Installation log files
- System information (`uname -a`, `cat /etc/os-release`)
- Error messages
- Steps to reproduce the issue
EOF
    
    log_success "Documentation copied ✓"
}

# Generate checksums for all files
generate_checksums() {
    log_info "Generating file checksums..."
    update_progress
    
    cd "$BUILD_DIR"
    
    # Generate checksums for all files
    find . -type f -not -name "checksums.txt" -exec sha256sum {} \; > checksums.txt
    
    # Create manifest with build information
    cat > manifest.json <<EOF
{
    "package_name": "$PACKAGE_NAME",
    "build_date": "$(date -Iseconds)",
    "build_mode": "$BUILD_MODE",
    "build_version": "1.0.0",
    "file_count": $(find . -type f | wc -l),
    "total_size": "$(du -sh . | awk '{print $1}')",
    "checksum_count": $(wc -l < checksums.txt),
    "components": {
        "images": $(find images -name "*.tar*" 2>/dev/null | wc -l),
        "python_packages": $(find packages/python -name "*.whl" -o -name "*.tar.gz" 2>/dev/null | wc -l),
        "node_packages": $(find packages/node -name "*.tgz" 2>/dev/null | wc -l),
        "source_directories": $(find source -maxdepth 1 -type d | wc -l),
        "config_files": $(find configs -name "*.yml" -o -name "*.conf" -o -name "*.template" 2>/dev/null | wc -l),
        "scripts": $(find scripts -name "*.sh" 2>/dev/null | wc -l)
    }
}
EOF
    
    cd "$SCRIPT_DIR"
    
    log_success "Checksums generated ✓"
}

# Create final compressed package
create_final_package() {
    log_info "Creating final compressed package..."
    update_progress
    
    cd "$(dirname "$BUILD_DIR")"
    
    local BASENAME=$(basename "$BUILD_DIR")
    
    # Create compressed archive
    log_info "Compressing package (level: $COMPRESS_LEVEL)..."
    if tar -czf "$FINAL_PACKAGE" -C . "$BASENAME"; then
        log_success "Package created: $FINAL_PACKAGE"
    else
        log_error "Failed to create package"
        return 1
    fi
    
    # Generate package checksum
    PACKAGE_CHECKSUM=$(sha256sum "$FINAL_PACKAGE" | awk '{print $1}')
    
    # Create package info
    cat > "${FINAL_PACKAGE}.info" <<EOF
# SDC Air-Gap Package Information
Package: $(basename "$FINAL_PACKAGE")
Size: $(du -h "$FINAL_PACKAGE" | awk '{print $1}')
Checksum (SHA256): $PACKAGE_CHECKSUM
Build Date: $(date)
Build Mode: $BUILD_MODE
Components: Images, Python Packages, Node Packages, Source Code, Configurations
EOF
    
    log_info "Package size: $(du -h "$FINAL_PACKAGE" | awk '{print $1}')"
    log_info "Package checksum: $PACKAGE_CHECKSUM"
    
    cd "$SCRIPT_DIR"
}

# Test the package
test_package() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_info "Skipping package tests (SKIP_TESTS=true)"
        update_progress
        return 0
    fi
    
    log_info "Testing package integrity..."
    update_progress
    
    local TEST_DIR="/tmp/sdc-test-$$"
    mkdir -p "$TEST_DIR"
    
    # Extract package
    if tar -xzf "$FINAL_PACKAGE" -C "$TEST_DIR"; then
        log_success "Package extraction test passed ✓"
    else
        log_error "Package extraction test failed"
        rm -rf "$TEST_DIR"
        return 1
    fi
    
    # Verify checksums
    cd "$TEST_DIR/$(basename "$BUILD_DIR")"
    
    local CHECKSUM_ERRORS=0
    while IFS=' ' read -r CHECKSUM FILE; do
        if [ -f "$FILE" ]; then
            ACTUAL=$(sha256sum "$FILE" | awk '{print $1}')
            if [ "$CHECKSUM" != "$ACTUAL" ]; then
                log_error "Checksum verification failed: $FILE"
                CHECKSUM_ERRORS=$((CHECKSUM_ERRORS + 1))
            fi
        else
            log_warning "File missing in package: $FILE"
        fi
    done < checksums.txt
    
    if [ "$CHECKSUM_ERRORS" -eq 0 ]; then
        log_success "Checksum verification test passed ✓"
    else
        log_error "Checksum verification test failed ($CHECKSUM_ERRORS errors)"
        rm -rf "$TEST_DIR"
        return 1
    fi
    
    # Test script syntax
    for SCRIPT in *.sh scripts/*.sh; do
        if [ -f "$SCRIPT" ]; then
            if bash -n "$SCRIPT"; then
                log_success "Syntax check passed: $SCRIPT ✓"
            else
                log_error "Syntax check failed: $SCRIPT"
                CHECKSUM_ERRORS=$((CHECKSUM_ERRORS + 1))
            fi
        fi
    done
    
    cd "$SCRIPT_DIR"
    rm -rf "$TEST_DIR"
    
    if [ "$CHECKSUM_ERRORS" -eq 0 ]; then
        log_success "All package tests passed ✓"
    else
        log_error "Package tests failed"
        return 1
    fi
}

# Main build process
main() {
    cat <<EOF
================================================================================
                      SDC Air-Gap Package Builder
                           Version 1.0.0
================================================================================

Build Mode: $BUILD_MODE
Compression Level: $COMPRESS_LEVEL
Skip Tests: $SKIP_TESTS

================================================================================
EOF
    
    log_info "Starting build process at $(date)"
    
    # Execute build steps
    for STEP in "${BUILD_STEPS[@]}"; do
        log_info "=================================================================================="
        log_info "Executing: $STEP"
        log_info "=================================================================================="
        
        if ! $STEP; then
            log_error "Build failed at step: $STEP"
            log_error "Check build log: $LOG_FILE"
            exit 1
        fi
    done
    
    # Final summary
    cat <<EOF

================================================================================
                        Build Completed Successfully!
================================================================================

Package: $FINAL_PACKAGE
Size: $(du -h "$FINAL_PACKAGE" | awk '{print $1}')
Checksum: $(sha256sum "$FINAL_PACKAGE" | awk '{print $1}')

To install on air-gap system:
1. Transfer the package file to target system
2. Extract: tar -xzf $(basename "$FINAL_PACKAGE")
3. Run: sudo ./sdc-install-secure.sh

Build log: $LOG_FILE

================================================================================
EOF
}

# Error handler
cleanup() {
    if [ -n "${BUILD_DIR:-}" ] && [ "$BUILD_DIR" != "/" ]; then
        log_info "Cleaning up build directory..."
        # Only clean if we're not keeping build artifacts
        if [ "${KEEP_BUILD:-false}" != "true" ]; then
            rm -rf "$BUILD_DIR"
        fi
    fi
}

trap cleanup EXIT

# Run main build process
main "$@"