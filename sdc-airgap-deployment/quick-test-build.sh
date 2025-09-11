#!/bin/bash
# Quick Test Build for SDC Air-Gap Package
# This script creates a minimal test package to verify the build system works

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_BUILD_DIR="${SCRIPT_DIR}/test-build"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== SDC Air-Gap Quick Test Build ==="
echo "Creating minimal test package..."

# Clean previous test build
rm -rf "$TEST_BUILD_DIR"

# Create test structure
mkdir -p "$TEST_BUILD_DIR"/{scripts,packages/{python,node},source,configs,docs}

# Copy essential scripts
cp "${SCRIPT_DIR}"/*.sh "$TEST_BUILD_DIR/"
cp -r "${SCRIPT_DIR}/scripts" "$TEST_BUILD_DIR/"

# Create minimal source structure
mkdir -p "$TEST_BUILD_DIR/source"/{frontend,backend,services}
echo '{"name": "sdc-frontend", "version": "1.0.0"}' > "$TEST_BUILD_DIR/source/frontend/package.json"
echo 'print("SDC Backend Test")' > "$TEST_BUILD_DIR/source/backend/main.py"
echo '# SDC Test Service' > "$TEST_BUILD_DIR/source/services/test-service.py"

# Create minimal configs
cat > "$TEST_BUILD_DIR/configs/env.template" <<'EOF'
# SDC Test Environment
APP_ENV=production
DB_PASSWORD=test_password_123
JWT_SECRET=test_jwt_secret_456
EOF

cat > "$TEST_BUILD_DIR/configs/docker-compose.yml" <<'EOF'
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
EOF

# Create test documentation
cat > "$TEST_BUILD_DIR/docs/README.md" <<'EOF'
# SDC Air-Gap Test Package

This is a minimal test package to verify the air-gap deployment system.

## Contents
- Installation scripts
- Configuration templates  
- Source code structure
- Documentation

## Installation
1. Extract package
2. Run sudo ./sdc-install-secure.sh
3. Follow prompts
EOF

# Create package manifest
cat > "$TEST_BUILD_DIR/manifest.json" <<EOF
{
    "package_name": "sdc-airgap-test-${TIMESTAMP}",
    "build_date": "$(date -Iseconds)",
    "build_mode": "test",
    "build_version": "1.0.0-test",
    "file_count": $(find "$TEST_BUILD_DIR" -type f | wc -l),
    "total_size": "$(du -sh "$TEST_BUILD_DIR" | awk '{print $1}')",
    "components": {
        "scripts": $(find "$TEST_BUILD_DIR/scripts" -name "*.sh" 2>/dev/null | wc -l),
        "configs": $(find "$TEST_BUILD_DIR/configs" -type f 2>/dev/null | wc -l),
        "docs": $(find "$TEST_BUILD_DIR/docs" -type f 2>/dev/null | wc -l)
    }
}
EOF

# Generate checksums
cd "$TEST_BUILD_DIR"
find . -type f -exec sha256sum {} \; > checksums.txt
cd "$SCRIPT_DIR"

# Create compressed package
PACKAGE_NAME="sdc-airgap-test-${TIMESTAMP}.tar.gz"
tar -czf "$PACKAGE_NAME" -C "$(dirname "$TEST_BUILD_DIR")" "$(basename "$TEST_BUILD_DIR")"

# Generate package info
PACKAGE_SIZE=$(du -h "$PACKAGE_NAME" | awk '{print $1}')
PACKAGE_CHECKSUM=$(sha256sum "$PACKAGE_NAME" | awk '{print $1}')

cat > "${PACKAGE_NAME}.info" <<EOF
# SDC Air-Gap Test Package Information
Package: $PACKAGE_NAME
Size: $PACKAGE_SIZE
Checksum (SHA256): $PACKAGE_CHECKSUM
Build Date: $(date)
Build Mode: test
Components: Scripts, Configs, Documentation (No images/packages for quick test)
EOF

echo "=== Test Package Created Successfully ==="
echo "Package: $PACKAGE_NAME"
echo "Size: $PACKAGE_SIZE"
echo "Checksum: $PACKAGE_CHECKSUM"
echo ""
echo "To test installation:"
echo "1. tar -xzf $PACKAGE_NAME"
echo "2. cd $(basename "$PACKAGE_NAME" .tar.gz)"
echo "3. sudo ./sdc-install-secure.sh"
echo ""
echo "Note: This is a test package without actual images or dependencies."

# Test extraction
echo "Testing package extraction..."
TEST_EXTRACT_DIR="/tmp/sdc-test-extract-$$"
mkdir -p "$TEST_EXTRACT_DIR"

if tar -xzf "$PACKAGE_NAME" -C "$TEST_EXTRACT_DIR"; then
    echo "✅ Package extraction test PASSED"
    
    # Test checksum verification
    cd "$TEST_EXTRACT_DIR/$(basename "$TEST_BUILD_DIR")"
    if sha256sum -c checksums.txt >/dev/null 2>&1; then
        echo "✅ Checksum verification test PASSED"
    else
        echo "❌ Checksum verification test FAILED"
    fi
    
    cd "$SCRIPT_DIR"
    rm -rf "$TEST_EXTRACT_DIR"
else
    echo "❌ Package extraction test FAILED"
    rm -rf "$TEST_EXTRACT_DIR"
    exit 1
fi

echo ""
echo "🎉 Test package generation completed successfully!"
echo "Full build can be performed with: ./build-airgap-package.sh full"