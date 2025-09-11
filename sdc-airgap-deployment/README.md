# SDC Air-Gap Deployment Package

This package provides a complete offline installation solution for the SDC (Smart Document Companion) platform, designed for air-gapped environments where internet access is not available.

## 📋 Package Overview

### What's Included
- **Complete SDC Platform**: Frontend, Backend, and all microservices
- **Container Images**: All required Docker/Podman images (17 images)
- **Dependencies**: Python packages (~150 wheels) and Node.js packages (~80 packages)
- **Configuration Templates**: Production-ready configuration files
- **Database Scripts**: PostgreSQL initialization and migration scripts
- **Security Hardened Installation**: Enterprise-grade security features
- **Comprehensive Documentation**: Installation, troubleshooting, and operational guides

### Package Components
```
sdc-airgap-deployment/
├── build-airgap-package.sh     # Master build script
├── sdc-install.sh              # Standard installation script  
├── sdc-install-secure.sh       # Security-hardened installation
├── scripts/                    # Component build scripts
│   ├── export_images.sh        # Container image export
│   ├── bundle_python_packages.sh # Python package bundling
│   └── bundle_node_packages.sh   # Node.js package bundling
├── docs/                       # Documentation
├── configs/                    # Configuration templates
└── data/                       # Database initialization scripts
```

## 🚀 Quick Start

### Step 1: Build the Package

**On a system with internet access:**

```bash
# Full build (recommended for production)
./build-airgap-package.sh full

# Build only container images
./build-airgap-package.sh images-only

# Build only packages (Python + Node.js)
./build-airgap-package.sh packages-only
```

**Build Options:**
- `COMPRESS_LEVEL=9` - Maximum compression (slower build)
- `SKIP_TESTS=true` - Skip package validation tests
- `KEEP_BUILD=true` - Keep build directory after completion

### Step 2: Transfer to Air-Gap System

```bash
# Copy the generated package
scp sdc-airgap-*.tar.gz user@airgap-server:/tmp/
```

### Step 3: Install on Air-Gap System

```bash
# Extract package
tar -xzf sdc-airgap-*.tar.gz
cd sdc-airgap-*

# Standard installation
sudo ./sdc-install.sh

# Security-hardened installation (recommended)
sudo ./sdc-install-secure.sh
```

## 🔧 Build Requirements

### Development System (Internet Required)
- **Operating System**: Linux (Ubuntu 20.04+, RHEL 8+, CentOS 8+)
- **Resources**: 8+ CPU cores, 16GB+ RAM, 50GB+ disk space
- **Software**: 
  - Podman 4.0+ or Docker 20.10+
  - Node.js 20+
  - Python 3.11+
  - Git, tar, gzip, sha256sum

### Target System (Air-Gap)
- **Operating System**: Linux (same distributions)
- **Resources**: 8+ CPU cores, 16GB+ RAM, 100GB+ disk space
- **Software**: Podman 4.0+ (must be pre-installed)
- **Network**: Isolated/air-gapped environment

## 📦 Build Process Details

### Phase 1: Environment Validation
- Checks system requirements and available resources
- Validates project structure and dependencies
- Ensures adequate disk space for build process

### Phase 2: Source Code Preparation
- Copies frontend (Next.js 15) source code
- Copies backend (FastAPI) source code
- Copies all microservices source code
- Cleans build artifacts and node_modules

### Phase 3: Container Image Export
- Builds application container images
- Pulls infrastructure images (PostgreSQL, Redis, etc.)
- Exports all images as compressed tar files
- Generates image manifests and checksums

### Phase 4: Package Dependency Bundling
- **Python**: Downloads ~150 wheel files for all dependencies
- **Node.js**: Creates offline npm cache with ~80 packages
- Creates offline package repositories with indices
- Generates installation scripts for offline use

### Phase 5: Configuration Generation
- Creates production-ready .env templates
- Generates docker-compose.yml configurations
- Creates nginx reverse proxy configuration
- Prepares database initialization scripts

### Phase 6: Package Assembly
- Assembles all components into unified structure
- Generates comprehensive file checksums
- Creates package manifest with metadata
- Compresses final package with optimized settings

## 🔐 Security Features

### Security-Hardened Installation (`sdc-install-secure.sh`)
- **Credential Generation**: Auto-generates secure passwords and secrets
- **File Permissions**: Restrictive permissions (750/600) for all files
- **User Isolation**: Runs services under non-privileged user accounts
- **Network Isolation**: Creates isolated Podman/Docker networks
- **Audit Logging**: Comprehensive installation and runtime audit trails
- **Input Validation**: Validates all user inputs against security patterns
- **Encrypted Storage**: Sensitive data encrypted during installation

### Security Hardening Features
- JWT secrets (512-bit)
- Database passwords (256-bit)
- SCRAM-SHA-256 authentication
- TLS-ready configurations
- Rate limiting configurations
- CORS protection settings
- Security headers presets

## 📊 Package Specifications

### Estimated Package Sizes
- **Full Package**: ~15-25GB compressed (~40-60GB uncompressed)
- **Images Only**: ~10-15GB compressed
- **Packages Only**: ~2-5GB compressed

### Component Breakdown
- **Container Images**: 17 images (~8-12GB uncompressed)
- **Python Packages**: ~150 wheels (~1-2GB)
- **Node.js Packages**: ~80 packages (~500MB-1GB)
- **Source Code**: ~500MB
- **Configuration & Documentation**: ~50MB

### Supported Architectures
- **Primary**: x86_64 (AMD64)
- **Containers**: Multi-arch support where available
- **OS Compatibility**: RHEL/CentOS 8+, Ubuntu 20.04+, Rocky Linux, AlmaLinux

## 🛠️ Advanced Usage

### Build Customization

```bash
# High compression build
COMPRESS_LEVEL=9 ./build-airgap-package.sh full

# Quick development build
SKIP_TESTS=true COMPRESS_LEVEL=1 ./build-airgap-package.sh

# Build with custom package retention
KEEP_BUILD=true ./build-airgap-package.sh full
```

### Component-Only Builds

```bash
# Export only container images
./scripts/export_images.sh

# Bundle only Python packages  
./scripts/bundle_python_packages.sh

# Bundle only Node.js packages
./scripts/bundle_node_packages.sh
```

### Installation Modes

```bash
# Resume interrupted installation
sudo ./sdc-install-secure.sh  # Automatically detects and resumes

# Installation with custom directories
sudo ./sdc-install-secure.sh
# Follow prompts for custom paths

# Debug installation
DEBUG=true sudo ./sdc-install-secure.sh
```

## 📋 Verification & Testing

### Package Integrity Verification
```bash
# Verify package checksum
sha256sum -c sdc-airgap-*.tar.gz.sha256

# Test package extraction
tar -tzf sdc-airgap-*.tar.gz | head -20

# Verify internal checksums
tar -xzf sdc-airgap-*.tar.gz
cd sdc-airgap-*
sha256sum -c checksums.txt
```

### Post-Installation Verification
```bash
# Check service health
curl http://localhost:3000  # Frontend
curl http://localhost:8000/health  # Backend API

# Check containers
podman ps

# Check logs
tail -f /var/log/sdc/app.log
```

## 🚨 Troubleshooting

### Common Build Issues

**Issue**: Container image export fails
```bash
# Solution: Ensure Podman/Docker is running
systemctl start podman
podman info
```

**Issue**: Python package download fails
```bash
# Solution: Check internet connectivity and PyPI access
pip install --upgrade pip
pip index versions fastapi
```

**Issue**: Node.js package bundling fails
```bash
# Solution: Clear npm cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
```

### Common Installation Issues

**Issue**: Port conflicts during installation
```bash
# Solution: Check and kill conflicting processes
ss -tuln | grep :3000
sudo lsof -ti:3000 | xargs kill -9
```

**Issue**: Permission errors
```bash
# Solution: Ensure proper sudo usage
sudo chown -R $USER:$USER /opt/sdc
```

**Issue**: Container startup failures
```bash
# Solution: Check container logs
podman logs sdc-backend
podman logs sdc-postgres
```

## 📚 Documentation Structure

- **`docs/INSTALL.md`**: Detailed installation guide
- **`docs/TROUBLESHOOTING.md`**: Comprehensive troubleshooting guide
- **`req.md`**: Original requirements specification
- **`file-inventory-checklist.md`**: Complete file inventory
- **Installation Report**: Generated post-installation with access details

## 🔄 Update Process

### For New SDC Versions
1. Update source code in project directory
2. Run build process to create new package
3. Test new package in staging environment
4. Deploy to air-gap systems using standard process

### For Security Updates
1. Update base container images
2. Update Python/Node.js dependencies
3. Rebuild and revalidate package
4. Deploy with priority scheduling

## 📞 Support & Maintenance

### Log Files
- **Build Logs**: `build.log`
- **Installation Logs**: `install_*.log`
- **Error Logs**: `install_err.md`
- **Runtime Logs**: `/var/log/sdc/`

### Health Monitoring
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000/health`
- **Admin Panel**: `http://localhost:3003`
- **Database**: `podman exec sdc-postgres pg_isready`

### Backup Recommendations
- Database: Daily PostgreSQL dumps
- Configuration: Version-controlled .env files
- Application data: Regular file system backups
- Container images: Registry or file-based backups

## 🏷️ Version Information

- **Package Version**: 1.0.0
- **SDC Platform**: Latest stable
- **Build System**: Production-ready
- **Security Level**: Enterprise-grade
- **Maintenance**: Active development

---

**For technical support or questions, please review the comprehensive documentation in the `docs/` directory or check the generated installation reports after deployment.**