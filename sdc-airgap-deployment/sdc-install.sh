#!/bin/bash
# SDC Air-Gap Installation Script
# Version: 1.0.0
# Description: Complete offline installation of SDC platform

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/install.log"
ERROR_LOG="${SCRIPT_DIR}/install_err.md"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
INSTALL_TRACKER="${SCRIPT_DIR}/.install_progress"

# Default values
DEFAULT_EXTRACT_DIR="/tmp/sdc-extract-${TIMESTAMP}"
DEFAULT_INSTALL_DIR="/opt/sdc"
PODMAN_NETWORK="sdc-network"
SUBNET="172.20.0.0/16"

# Function definitions
log() {
    echo -e "${2:-}$1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    echo "## Error at $(date '+%Y-%m-%d %H:%M:%S')" >> "$ERROR_LOG"
    echo "$1" >> "$ERROR_LOG"
    echo "" >> "$ERROR_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

# Save progress
save_progress() {
    echo "$1" > "$INSTALL_TRACKER"
}

# Get last progress
get_progress() {
    if [ -f "$INSTALL_TRACKER" ]; then
        cat "$INSTALL_TRACKER"
    else
        echo "0"
    fi
}

# Check if running as root or with sudo
check_privileges() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run with sudo privileges"
        exit 1
    fi
}

# Validate system requirements
validate_system() {
    log_info "Validating system requirements..."
    
    # Check OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "Operating System: $NAME $VERSION"
    else
        log_warning "Cannot determine OS version"
    fi
    
    # Check CPU cores
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 8 ]; then
        log_warning "CPU cores: $CPU_CORES (recommended: 8+)"
    else
        log_success "CPU cores: $CPU_CORES ✓"
    fi
    
    # Check RAM
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_RAM" -lt 16 ]; then
        log_warning "RAM: ${TOTAL_RAM}GB (recommended: 16GB+)"
    else
        log_success "RAM: ${TOTAL_RAM}GB ✓"
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df -BG "$SCRIPT_DIR" | awk 'NR==2 {print int($4)}')
    if [ "$AVAILABLE_SPACE" -lt 100 ]; then
        log_error "Insufficient disk space: ${AVAILABLE_SPACE}GB (required: 100GB+)"
        return 1
    else
        log_success "Available disk space: ${AVAILABLE_SPACE}GB ✓"
    fi
    
    # Check Podman
    if ! command -v podman &> /dev/null; then
        log_error "Podman is not installed. Please install Podman 4.0+ first."
        return 1
    else
        PODMAN_VERSION=$(podman --version | awk '{print $3}')
        log_success "Podman version: $PODMAN_VERSION ✓"
    fi
    
    # Check podman-compose
    if ! command -v podman-compose &> /dev/null; then
        log_warning "podman-compose not found, will use podman directly"
    else
        COMPOSE_VERSION=$(podman-compose --version 2>/dev/null || echo "unknown")
        log_success "podman-compose version: $COMPOSE_VERSION ✓"
    fi
    
    return 0
}

# Get user input for directories
get_user_input() {
    log_info "=== Installation Configuration ==="
    
    # Get extraction directory
    read -p "Enter extraction directory [${DEFAULT_EXTRACT_DIR}]: " EXTRACT_DIR
    EXTRACT_DIR=${EXTRACT_DIR:-$DEFAULT_EXTRACT_DIR}
    
    # Get installation directory
    read -p "Enter installation directory [${DEFAULT_INSTALL_DIR}]: " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}
    
    # Confirm settings
    log_info "Configuration Summary:"
    log_info "  Extraction Directory: $EXTRACT_DIR"
    log_info "  Installation Directory: $INSTALL_DIR"
    
    read -p "Proceed with these settings? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Installation cancelled by user"
        exit 1
    fi
    
    # Create directories
    mkdir -p "$EXTRACT_DIR"
    mkdir -p "$INSTALL_DIR"
    
    save_progress "1"
}

# Check port availability
check_ports() {
    log_info "Checking port availability..."
    
    local REQUIRED_PORTS=(3000 3003 3004 8000 8001 8002 8006 8007 8008 5432 6379 9200 19530)
    local PORT_CONFLICTS=0
    
    for PORT in "${REQUIRED_PORTS[@]}"; do
        if ss -tuln | grep -q ":$PORT "; then
            log_warning "Port $PORT is already in use"
            PORT_CONFLICTS=$((PORT_CONFLICTS + 1))
        else
            log_success "Port $PORT is available ✓"
        fi
    done
    
    if [ "$PORT_CONFLICTS" -gt 0 ]; then
        log_warning "$PORT_CONFLICTS port(s) are in use. Services may need port remapping."
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Installation cancelled due to port conflicts"
            exit 1
        fi
    fi
    
    save_progress "2"
}

# Check and configure network
setup_network() {
    log_info "Setting up Podman network..."
    
    # Check if network exists
    if podman network exists "$PODMAN_NETWORK" 2>/dev/null; then
        log_warning "Network $PODMAN_NETWORK already exists"
        read -p "Remove and recreate network? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            podman network rm "$PODMAN_NETWORK" 2>/dev/null || true
        else
            log_info "Using existing network"
            return 0
        fi
    fi
    
    # Create network
    if podman network create --subnet="$SUBNET" "$PODMAN_NETWORK"; then
        log_success "Created network $PODMAN_NETWORK with subnet $SUBNET"
    else
        log_error "Failed to create network"
        return 1
    fi
    
    save_progress "3"
}

# Extract package
extract_package() {
    log_info "Extracting installation package..."
    
    # Find the tar.gz file
    PACKAGE_FILE=$(find "$SCRIPT_DIR" -maxdepth 1 -name "sdc-airgap-*.tar.gz" | head -1)
    
    if [ -z "$PACKAGE_FILE" ]; then
        log_error "No installation package found (sdc-airgap-*.tar.gz)"
        return 1
    fi
    
    log_info "Found package: $PACKAGE_FILE"
    
    # Extract to specified directory
    if tar -xzf "$PACKAGE_FILE" -C "$EXTRACT_DIR" --strip-components=1; then
        log_success "Package extracted successfully"
    else
        log_error "Failed to extract package"
        return 1
    fi
    
    save_progress "4"
}

# Verify checksums
verify_files() {
    log_info "Verifying file integrity..."
    
    if [ -f "$EXTRACT_DIR/checksums.txt" ]; then
        cd "$EXTRACT_DIR"
        local FAILED=0
        
        while IFS= read -r line; do
            CHECKSUM=$(echo "$line" | awk '{print $1}')
            FILE=$(echo "$line" | awk '{print $2}')
            
            if [ -f "$FILE" ]; then
                ACTUAL=$(sha256sum "$FILE" | awk '{print $1}')
                if [ "$CHECKSUM" != "$ACTUAL" ]; then
                    log_error "Checksum mismatch: $FILE"
                    FAILED=$((FAILED + 1))
                fi
            else
                log_warning "File not found: $FILE"
            fi
        done < checksums.txt
        
        if [ "$FAILED" -gt 0 ]; then
            log_error "$FAILED files failed checksum verification"
            return 1
        else
            log_success "All files verified successfully"
        fi
        
        cd "$SCRIPT_DIR"
    else
        log_warning "No checksums.txt found, skipping verification"
    fi
    
    save_progress "5"
}

# Load container images
load_images() {
    log_info "Loading container images..."
    
    local IMAGE_DIR="$EXTRACT_DIR/images"
    
    if [ ! -d "$IMAGE_DIR" ]; then
        log_error "Image directory not found: $IMAGE_DIR"
        return 1
    fi
    
    # Load each tar file
    for IMAGE_FILE in "$IMAGE_DIR"/*.tar; do
        if [ -f "$IMAGE_FILE" ]; then
            IMAGE_NAME=$(basename "$IMAGE_FILE" .tar)
            log_info "Loading image: $IMAGE_NAME"
            
            if podman load -i "$IMAGE_FILE"; then
                log_success "Loaded: $IMAGE_NAME"
            else
                log_error "Failed to load: $IMAGE_NAME"
                return 1
            fi
        fi
    done
    
    # List loaded images
    log_info "Loaded images:"
    podman images --format "table {{.Repository}}:{{.Tag}}" | tee -a "$LOG_FILE"
    
    save_progress "6"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    local PYTHON_PKG_DIR="$EXTRACT_DIR/packages/python"
    
    if [ ! -d "$PYTHON_PKG_DIR" ]; then
        log_error "Python package directory not found: $PYTHON_PKG_DIR"
        return 1
    fi
    
    # Create virtual environment in installation directory
    log_info "Creating Python virtual environment..."
    python3 -m venv "$INSTALL_DIR/venv"
    
    # Activate and install packages
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Install from wheels
    log_info "Installing Python packages from wheels..."
    pip install --no-index --find-links "$PYTHON_PKG_DIR" -r "$EXTRACT_DIR/requirements.txt"
    
    if [ $? -eq 0 ]; then
        log_success "Python dependencies installed successfully"
    else
        log_error "Failed to install Python dependencies"
        return 1
    fi
    
    deactivate
    
    save_progress "7"
}

# Install Node.js dependencies
install_node_deps() {
    log_info "Installing Node.js dependencies..."
    
    local NODE_PKG_DIR="$EXTRACT_DIR/packages/node"
    
    if [ ! -d "$NODE_PKG_DIR" ]; then
        log_error "Node package directory not found: $NODE_PKG_DIR"
        return 1
    fi
    
    # Copy frontend source
    cp -r "$EXTRACT_DIR/source/frontend" "$INSTALL_DIR/"
    
    cd "$INSTALL_DIR/frontend"
    
    # Set npm cache to offline packages
    npm config set cache "$NODE_PKG_DIR"
    
    # Install from offline cache
    log_info "Installing Node.js packages..."
    npm ci --offline --prefer-offline
    
    if [ $? -eq 0 ]; then
        log_success "Node.js dependencies installed successfully"
    else
        log_error "Failed to install Node.js dependencies"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    
    save_progress "8"
}

# Copy source code
copy_source() {
    log_info "Copying source code to installation directory..."
    
    # Copy backend
    cp -r "$EXTRACT_DIR/source/backend" "$INSTALL_DIR/"
    
    # Copy services
    cp -r "$EXTRACT_DIR/source/services" "$INSTALL_DIR/"
    
    # Set permissions
    chown -R $(logname):$(logname) "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    
    log_success "Source code copied successfully"
    
    save_progress "9"
}

# Configure environment
configure_environment() {
    log_info "Configuring environment..."
    
    # Copy and configure .env files
    if [ -f "$EXTRACT_DIR/configs/env.template" ]; then
        cp "$EXTRACT_DIR/configs/env.template" "$INSTALL_DIR/.env"
        
        # Update paths in .env
        sed -i "s|/opt/sdc|$INSTALL_DIR|g" "$INSTALL_DIR/.env"
        
        log_info "Environment file configured"
    fi
    
    # Copy docker-compose files
    cp "$EXTRACT_DIR/configs/docker-compose.yml" "$INSTALL_DIR/"
    
    # Update compose file with correct paths
    sed -i "s|/opt/sdc|$INSTALL_DIR|g" "$INSTALL_DIR/docker-compose.yml"
    
    log_success "Environment configured successfully"
    
    save_progress "10"
}

# Initialize databases
init_databases() {
    log_info "Initializing databases..."
    
    # Start PostgreSQL first
    podman run -d \
        --name sdc-postgres \
        --network "$PODMAN_NETWORK" \
        -e POSTGRES_USER=sdc \
        -e POSTGRES_PASSWORD=sdc_password \
        -e POSTGRES_DB=sdc_db \
        -p 5432:5432 \
        postgres:16-alpine
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Run migrations
    if [ -d "$INSTALL_DIR/backend/alembic" ]; then
        cd "$INSTALL_DIR/backend"
        source "$INSTALL_DIR/venv/bin/activate"
        
        log_info "Running database migrations..."
        alembic upgrade head
        
        if [ $? -eq 0 ]; then
            log_success "Database initialized successfully"
        else
            log_error "Failed to run migrations"
            return 1
        fi
        
        deactivate
        cd "$SCRIPT_DIR"
    fi
    
    save_progress "11"
}

# Start services
start_services() {
    log_info "Starting all services..."
    
    cd "$INSTALL_DIR"
    
    # Create systemd service files
    create_systemd_services
    
    # Start services using podman-compose or individual containers
    if command -v podman-compose &> /dev/null; then
        log_info "Starting services with podman-compose..."
        podman-compose up -d
    else
        log_info "Starting services individually..."
        start_individual_services
    fi
    
    log_success "All services started"
    
    save_progress "12"
}

# Create systemd service files
create_systemd_services() {
    log_info "Creating systemd service files..."
    
    # SDC Backend Service
    cat > /etc/systemd/system/sdc-backend.service <<EOF
[Unit]
Description=SDC Backend API Service
After=network.target

[Service]
Type=simple
User=$(logname)
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$INSTALL_DIR/venv/bin/python simple_api.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # SDC Frontend Service
    cat > /etc/systemd/system/sdc-frontend.service <<EOF
[Unit]
Description=SDC Frontend Service
After=network.target

[Service]
Type=simple
User=$(logname)
WorkingDirectory=$INSTALL_DIR/frontend
ExecStart=/usr/bin/npm run start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    
    log_success "Systemd services created"
}

# Start individual services (fallback)
start_individual_services() {
    # Redis
    podman run -d \
        --name sdc-redis \
        --network "$PODMAN_NETWORK" \
        -p 6379:6379 \
        redis:7-alpine
    
    # Elasticsearch
    podman run -d \
        --name sdc-elasticsearch \
        --network "$PODMAN_NETWORK" \
        -e "discovery.type=single-node" \
        -e "xpack.security.enabled=false" \
        -p 9200:9200 \
        elasticsearch:8.11.0
    
    # Start backend service
    systemctl start sdc-backend
    systemctl enable sdc-backend
    
    # Start frontend service
    systemctl start sdc-frontend
    systemctl enable sdc-frontend
    
    log_info "Individual services started"
}

# Health check
health_check() {
    log_info "Running health checks..."
    
    local SERVICES=(
        "http://localhost:3000:Frontend"
        "http://localhost:8000/health:Backend API"
        "http://localhost:5432:PostgreSQL"
        "http://localhost:6379:Redis"
        "http://localhost:9200:Elasticsearch"
    )
    
    local FAILED=0
    
    for SERVICE in "${SERVICES[@]}"; do
        IFS=':' read -r -a PARTS <<< "$SERVICE"
        URL="${PARTS[0]}:${PARTS[1]}:${PARTS[2]}"
        NAME="${PARTS[3]}"
        
        if curl -s -o /dev/null -w "%{http_code}" "$URL" | grep -q "200\|000"; then
            log_success "$NAME is healthy ✓"
        else
            log_error "$NAME is not responding"
            FAILED=$((FAILED + 1))
        fi
    done
    
    if [ "$FAILED" -gt 0 ]; then
        log_warning "$FAILED service(s) failed health check"
        return 1
    else
        log_success "All services are healthy"
    fi
    
    save_progress "13"
}

# Generate completion report
generate_report() {
    log_info "Generating installation report..."
    
    cat > "$INSTALL_DIR/installation_report.md" <<EOF
# SDC Installation Report
Generated: $(date)

## Installation Summary
- Installation Directory: $INSTALL_DIR
- Extraction Directory: $EXTRACT_DIR
- Installation Status: SUCCESS

## Services Status
$(podman ps --format "table {{.Names}}\t{{.Status}}" | grep sdc-)

## Access URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin Panel: http://localhost:3003
- Curation Dashboard: http://localhost:3004

## Default Credentials
- Username: admin
- Password: admin123 (change immediately)

## Next Steps
1. Change default passwords
2. Configure SSL certificates
3. Review security settings
4. Set up backup procedures

## Log Files
- Installation Log: $LOG_FILE
- Error Log: $ERROR_LOG

## Support
For issues, check:
- $INSTALL_DIR/docs/TROUBLESHOOTING.md
- Error log at $ERROR_LOG
EOF
    
    log_success "Installation report generated: $INSTALL_DIR/installation_report.md"
    
    save_progress "14"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    
    # Remove extraction directory if not same as install
    if [ "$EXTRACT_DIR" != "$INSTALL_DIR" ]; then
        rm -rf "$EXTRACT_DIR"
    fi
    
    # Remove progress tracker
    rm -f "$INSTALL_TRACKER"
    
    log_success "Cleanup completed"
}

# Main installation flow
main() {
    cat <<EOF
================================================================================
                     SDC Air-Gap Installation Script
                              Version 1.0.0
================================================================================
EOF
    
    # Initialize logs
    echo "# SDC Installation Error Log" > "$ERROR_LOG"
    echo "Generated: $(date)" >> "$ERROR_LOG"
    echo "" >> "$ERROR_LOG"
    
    log_info "Starting installation at $(date)"
    
    # Check if resuming
    LAST_PROGRESS=$(get_progress)
    if [ "$LAST_PROGRESS" -gt 0 ]; then
        log_info "Resuming installation from step $LAST_PROGRESS"
    fi
    
    # Request sudo password upfront
    log_info "This installation requires administrative privileges."
    
    # Run installation steps
    STEPS=(
        "check_privileges"
        "validate_system"
        "get_user_input"
        "check_ports"
        "setup_network"
        "extract_package"
        "verify_files"
        "load_images"
        "install_python_deps"
        "install_node_deps"
        "copy_source"
        "configure_environment"
        "init_databases"
        "start_services"
        "health_check"
        "generate_report"
        "cleanup"
    )
    
    for i in "${!STEPS[@]}"; do
        STEP_NUM=$((i + 1))
        
        # Skip completed steps
        if [ "$STEP_NUM" -le "$LAST_PROGRESS" ]; then
            log_info "Skipping completed step: ${STEPS[$i]}"
            continue
        fi
        
        log_info "=================================================================================="
        log_info "Step $STEP_NUM/${#STEPS[@]}: ${STEPS[$i]}"
        log_info "=================================================================================="
        
        if ! ${STEPS[$i]}; then
            log_error "Installation failed at step: ${STEPS[$i]}"
            log_error "Check $ERROR_LOG for details"
            log_info "You can resume installation by running this script again"
            exit 1
        fi
    done
    
    # Final message
    cat <<EOF

================================================================================
                        Installation Completed Successfully!
================================================================================

SDC Platform has been installed successfully.

Access the application at:
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs

Installation Report: $INSTALL_DIR/installation_report.md

To start services manually:
  systemctl start sdc-backend
  systemctl start sdc-frontend

To check service status:
  systemctl status sdc-backend
  systemctl status sdc-frontend
  podman ps

Thank you for installing SDC!

================================================================================
EOF
}

# Error handler
trap 'log_error "Installation interrupted at line $LINENO"' ERR

# Run main installation
main "$@"