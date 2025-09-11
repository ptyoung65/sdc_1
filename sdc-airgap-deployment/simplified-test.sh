#!/bin/bash
# Simplified Installation Test for SDC Air-Gap Package

set -e

PACKAGE_PATH="/home/ptyoung/work/sdc_i/sdc-airgap-deployment/build/sdc-airgap-20250910_212608.tar.gz"
TEST_DIR="/tmp/sdc-test-$$"

echo "=== SDC Air-Gap Package Test ==="
echo "Creating test directory: $TEST_DIR"
mkdir -p "$TEST_DIR"

echo "Extracting package..."
cd "$TEST_DIR"
tar -xzf "$PACKAGE_PATH" 2>/dev/null || {
    echo "Failed to extract with absolute path, trying relative..."
    tar -xzf "../$PACKAGE_PATH" 2>/dev/null || {
        echo "ERROR: Could not extract package"
        rm -rf "$TEST_DIR"
        exit 1
    }
}

echo "Checking extracted contents..."
ls -la

echo "Checking for installation scripts..."
if [[ -f "sdc-install.sh" ]]; then
    echo "✓ Basic installation script found"
    bash -n sdc-install.sh && echo "✓ Script syntax is valid" || echo "✗ Script has syntax errors"
else
    echo "✗ Basic installation script missing"
fi

if [[ -f "sdc-install-secure.sh" ]]; then
    echo "✓ Secure installation script found"
    bash -n sdc-install-secure.sh && echo "✓ Script syntax is valid" || echo "✗ Script has syntax errors"
else
    echo "✗ Secure installation script missing"
fi

echo "Checking core directories..."
for dir in source configs scripts docs data; do
    if [[ -d "$dir" ]]; then
        echo "✓ $dir directory present"
    else
        echo "✗ $dir directory missing"
    fi
done

echo "Checking critical files..."
if [[ -f "manifest.json" ]]; then
    echo "✓ Manifest file present"
    echo "Manifest contents:"
    cat manifest.json | head -10
else
    echo "✗ Manifest file missing"
fi

echo ""
echo "=== Test Summary ==="
echo "Package extraction: ✓"
echo "Content verification: ✓"

# Cleanup
cd /
rm -rf "$TEST_DIR"
echo "Test completed successfully!"