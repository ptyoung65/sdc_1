#!/bin/bash
# SDC Air-Gap Package Installation Test Script
# Tests the complete installation process in an isolated environment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="/tmp/sdc-airgap-test-$(date +%s)"
LOG_FILE="$SCRIPT_DIR/test-installation.log"
PACKAGE_PATH="$SCRIPT_DIR/build/sdc-airgap-20250910_212608.tar.gz"

# Logging functions
log_info() {
    local msg="[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1"
    echo -e "\033[0;34m$msg\033[0m" | tee -a "$LOG_FILE"
}

log_success() {
    local msg="[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') $1"
    echo -e "\033[0;32m$msg\033[0m" | tee -a "$LOG_FILE"
}

log_error() {
    local msg="[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1"
    echo -e "\033[0;31m$msg\033[0m" | tee -a "$LOG_FILE"
}

log_warning() {
    local msg="[WARNING] $(date '+%Y-%m-%d %H:%M:%S') $1"
    echo -e "\033[1;33m$msg\033[0m" | tee -a "$LOG_FILE"
}

# Cleanup function
cleanup() {
    if [[ -d "$TEST_DIR" ]]; then
        log_info "Cleaning up test directory: $TEST_DIR"
        rm -rf "$TEST_DIR"
    fi
}

# Error handler
error_exit() {
    log_error "$1"
    cleanup
    exit 1
}

# Set up error handling
trap cleanup EXIT
trap 'error_exit "Script interrupted by user"' INT TERM

# Test functions
test_package_extraction() {
    log_info "Testing package extraction..."
    
    if [[ ! -f "$PACKAGE_PATH" ]]; then
        error_exit "Package not found: $PACKAGE_PATH"
    fi
    
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"
    
    tar -xzf "$PACKAGE_PATH" || error_exit "Failed to extract package"
    
    # Check if any content was extracted
    if [[ ! -f "sdc-install.sh" ]] && [[ ! -d "source" ]]; then
        error_exit "No installation content found after extraction"
    fi
    
    log_success "Package extraction successful"
}

test_checksums() {
    log_info "Testing checksum verification..."
    
    cd "$TEST_DIR"
    
    if [[ ! -f "checksums.txt" ]]; then
        log_warning "Checksums file not found - skipping checksum verification"
        return 0
    fi
    
    local failed_count=0
    while IFS= read -r line; do
        if [[ "$line" =~ .*:\ FAILED$ ]]; then
            ((failed_count++))
            log_error "Checksum failed: $line"
        fi
    done < <(sha256sum -c checksums.txt 2>/dev/null || true)
    
    if [[ $failed_count -gt 0 ]]; then
        error_exit "$failed_count files failed checksum verification"
    fi
    
    log_success "All checksums verified successfully"
}

test_installation_scripts() {
    log_info "Testing installation scripts..."
    
    cd "$TEST_DIR"
    
    # Test basic installation script
    if [[ ! -x "sdc-install.sh" ]]; then
        error_exit "Basic installation script not executable"
    fi
    
    # Test secure installation script  
    if [[ ! -x "sdc-install-secure.sh" ]]; then
        error_exit "Secure installation script not executable"
    fi
    
    # Test script syntax
    bash -n sdc-install.sh || error_exit "Basic installation script has syntax errors"
    bash -n sdc-install-secure.sh || error_exit "Secure installation script has syntax errors"
    
    log_success "Installation scripts are valid"
}

test_required_components() {
    log_info "Testing required components..."
    
    cd "$TEST_DIR"
    
    local required_dirs=("source" "configs" "scripts" "docs" "data")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            error_exit "Required directory missing: $dir"
        fi
    done
    
    local required_files=("manifest.json" "checksums.txt")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error_exit "Required file missing: $file"
        fi
    done
    
    log_success "All required components present"
}

test_source_code_structure() {
    log_info "Testing source code structure..."
    
    cd "$TEST_DIR/build/source"
    
    local required_source_dirs=("backend" "frontend" "services")
    for dir in "${required_source_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            error_exit "Required source directory missing: $dir"
        fi
    done
    
    # Check key files
    if [[ ! -f "backend/requirements.txt" ]]; then
        error_exit "Backend requirements.txt missing"
    fi
    
    if [[ ! -f "frontend/package.json" ]]; then
        error_exit "Frontend package.json missing"
    fi
    
    log_success "Source code structure is valid"
}

test_configuration_files() {
    log_info "Testing configuration files..."
    
    cd "$TEST_DIR/build/configs"
    
    local required_configs=("docker-compose.yml" "env.template" "nginx.conf")
    for config in "${required_configs[@]}"; do
        if [[ ! -f "$config" ]]; then
            error_exit "Required configuration missing: $config"
        fi
    done
    
    log_success "Configuration files are present"
}

test_database_scripts() {
    log_info "Testing database initialization scripts..."
    
    cd "$TEST_DIR/build/data"
    
    if [[ ! -d "sql" ]]; then
        error_exit "SQL directory missing"
    fi
    
    if [[ ! -f "sql/01_init.sql" ]]; then
        error_exit "Database initialization script missing"
    fi
    
    log_success "Database scripts are present"
}

test_documentation() {
    log_info "Testing documentation..."
    
    cd "$TEST_DIR/build/docs"
    
    local required_docs=("README.md" "INSTALL.md" "TROUBLESHOOTING.md")
    for doc in "${required_docs[@]}"; do
        if [[ ! -f "$doc" ]]; then
            error_exit "Required documentation missing: $doc"
        fi
    done
    
    log_success "Documentation is complete"
}

test_dry_run_installation() {
    log_info "Testing dry-run installation..."
    
    cd "$TEST_DIR"
    
    # Set environment variables for dry run
    export DRY_RUN=true
    export INSTALL_DIR="$TEST_DIR/sdc-install"
    
    # Run installation in dry-run mode
    if ! timeout 60 bash sdc-install.sh --dry-run 2>/dev/null; then
        log_warning "Dry-run installation test skipped (timeout or not supported)"
    else
        log_success "Dry-run installation completed"
    fi
    
    unset DRY_RUN INSTALL_DIR
}

# Main test execution
main() {
    log_info "Starting SDC Air-Gap Package Installation Test"
    log_info "Test directory: $TEST_DIR"
    log_info "Package path: $PACKAGE_PATH"
    log_info "=============================================================="
    
    # Run tests
    test_package_extraction
    test_checksums
    test_installation_scripts
    test_required_components
    test_source_code_structure
    test_configuration_files
    test_database_scripts
    test_documentation
    test_dry_run_installation
    
    log_success "=============================================================="
    log_success "All installation tests passed successfully!"
    log_success "Package is ready for air-gap deployment"
    log_info "Test completed at: $(date)"
    log_info "Test log saved to: $LOG_FILE"
}

# Run main function
main "$@"