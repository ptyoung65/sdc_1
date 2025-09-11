#!/bin/bash
# Complete Container Image Download Script for Air-Gap Deployment
# Downloads ALL required container images for Korean RAG system

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGES_DIR="$SCRIPT_DIR/images"
LOG_FILE="$SCRIPT_DIR/image-download.log"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $(date '+%Y-%m-%d %H:%M:%S') $1${NC}"
    echo "[WARNING] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# Create directories
mkdir -p "$IMAGES_DIR"

log_info "=== Korean RAG Air-Gap Container Image Download ==="

# Complete list of ALL required images for Korean RAG system
INFRASTRUCTURE_IMAGES=(
    "docker.io/postgres:16-alpine"
    "docker.io/pgvector/pgvector:pg16"
    "docker.io/redis:7-alpine"
    "docker.io/milvusdb/milvus:v2.3.3"
    "docker.elastic.co/elasticsearch/elasticsearch:8.11.1"
    "docker.io/elastic/kibana:8.11.1"
    "docker.io/nginx:alpine"
    "docker.io/nginx:1.24-alpine"
    "docker.io/traefik:v3.0"
    "docker.io/python:3.11-slim"
    "docker.io/python:3.11-slim-bullseye"
    "docker.io/node:20-alpine"
    "docker.io/node:18-alpine"
)

# Korean Language and AI specific images
AI_IMAGES=(
    "docker.io/huggingface/transformers-pytorch-gpu:latest"
    "docker.io/pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime"
    "docker.io/tensorflow/tensorflow:2.13.0-gpu"
    "docker.io/legendofmk/docling-cpu-api:latest"
    "docker.io/searxng/searxng:latest"
)

# Monitoring and Management images
MONITORING_IMAGES=(
    "docker.io/prom/prometheus:latest"
    "docker.io/prom/node-exporter:latest"
    "docker.io/prom/alertmanager:latest"
    "docker.io/grafana/grafana:latest"
    "docker.io/jaegertracing/all-in-one:latest"
    "docker.io/zcube/cadvisor:latest"
)

# Database and Storage images
STORAGE_IMAGES=(
    "docker.io/minio/minio:latest"
    "docker.io/minio/mc:latest"
    "docker.io/bitnami/postgresql:16"
    "docker.io/bitnami/redis:7.0"
    "docker.io/opensearchproject/opensearch:2.11.0"
    "docker.io/opensearchproject/opensearch-dashboards:2.11.0"
)

# Security and Auth images
SECURITY_IMAGES=(
    "docker.io/keycloak/keycloak:22.0"
    "docker.io/bitnami/oauth2-proxy:7.4.0"
    "docker.io/vault:1.15"
)

# Development and Testing images
DEV_IMAGES=(
    "docker.io/jupyter/scipy-notebook:latest"
    "docker.io/jupyter/datascience-notebook:latest"
    "docker.io/mailhog/mailhog:latest"
    "docker.io/adminer:latest"
)

# Function to download and save image
download_image() {
    local image="$1"
    local image_file=$(echo "$image" | sed 's|[:/]|-|g' | sed 's|^docker\.io-||').tar
    
    log_info "Downloading image: $image"
    
    # Check if image already exists locally
    if podman image exists "$image" 2>/dev/null; then
        log_info "Image $image already exists locally"
    else
        if ! podman pull "$image"; then
            log_error "Failed to pull image: $image"
            return 1
        fi
        log_success "Successfully pulled: $image"
    fi
    
    # Save image to tar file (remove existing file first)
    log_info "Saving image to: $IMAGES_DIR/$image_file"
    if [ -f "$IMAGES_DIR/$image_file" ]; then
        log_info "Removing existing image file: $image_file"
        rm -f "$IMAGES_DIR/$image_file"
    fi
    if podman save -o "$IMAGES_DIR/$image_file" "$image"; then
        log_success "Saved: $image_file ($(du -sh "$IMAGES_DIR/$image_file" | cut -f1))"
        
        # Generate checksum
        sha256sum "$IMAGES_DIR/$image_file" > "$IMAGES_DIR/$image_file.sha256"
    else
        log_error "Failed to save image: $image"
        return 1
    fi
}

# Function to download image category
download_category() {
    local category_name="$1"
    shift
    local images=("$@")
    
    log_info "=== Downloading $category_name Images ==="
    
    local failed_count=0
    local total_count=${#images[@]}
    
    for image in "${images[@]}"; do
        if ! download_image "$image"; then
            ((failed_count++))
        fi
        sleep 2  # Rate limiting
    done
    
    if [ $failed_count -eq 0 ]; then
        log_success "All $category_name images downloaded successfully ($total_count/$total_count)"
    else
        log_warning "$failed_count/$total_count $category_name images failed to download"
    fi
    
    return $failed_count
}

# Main execution
main() {
    log_info "Starting complete Korean RAG air-gap image download"
    log_info "Target directory: $IMAGES_DIR"
    log_info "Log file: $LOG_FILE"
    
    local total_failed=0
    
    # Download all image categories
    download_category "Infrastructure" "${INFRASTRUCTURE_IMAGES[@]}"
    total_failed=$((total_failed + $?))
    
    download_category "AI/ML" "${AI_IMAGES[@]}"
    total_failed=$((total_failed + $?))
    
    download_category "Monitoring" "${MONITORING_IMAGES[@]}"
    total_failed=$((total_failed + $?))
    
    download_category "Storage" "${STORAGE_IMAGES[@]}"
    total_failed=$((total_failed + $?))
    
    download_category "Security" "${SECURITY_IMAGES[@]}"
    total_failed=$((total_failed + $?))
    
    download_category "Development" "${DEV_IMAGES[@]}"
    total_failed=$((total_failed + $?))
    
    # Generate manifest
    log_info "Generating image manifest..."
    cat > "$IMAGES_DIR/image-manifest.txt" << EOF
# Korean RAG Air-Gap Container Images
# Generated: $(date)
# Total images: $(find "$IMAGES_DIR" -name "*.tar" | wc -l)
# Total size: $(du -sh "$IMAGES_DIR" | cut -f1)

## Infrastructure Images
$(printf '%s\n' "${INFRASTRUCTURE_IMAGES[@]}")

## AI/ML Images  
$(printf '%s\n' "${AI_IMAGES[@]}")

## Monitoring Images
$(printf '%s\n' "${MONITORING_IMAGES[@]}")

## Storage Images
$(printf '%s\n' "${STORAGE_IMAGES[@]}")

## Security Images
$(printf '%s\n' "${SECURITY_IMAGES[@]}")

## Development Images
$(printf '%s\n' "${DEV_IMAGES[@]}")
EOF
    
    # Generate checksum file for all images
    log_info "Generating checksums for all images..."
    find "$IMAGES_DIR" -name "*.tar" -exec sha256sum {} \; > "$IMAGES_DIR/all-images-checksums.txt"
    
    # Final summary
    local total_images=$(find "$IMAGES_DIR" -name "*.tar" | wc -l)
    local total_size=$(du -sh "$IMAGES_DIR" | cut -f1)
    
    if [ $total_failed -eq 0 ]; then
        log_success "=== ALL IMAGES DOWNLOADED SUCCESSFULLY ==="
    else
        log_warning "=== DOWNLOAD COMPLETED WITH $total_failed FAILURES ==="
    fi
    
    log_info "Total images downloaded: $total_images"
    log_info "Total size: $total_size"
    log_info "Images directory: $IMAGES_DIR"
    log_info "Manifest file: $IMAGES_DIR/image-manifest.txt"
    log_info "Checksums file: $IMAGES_DIR/all-images-checksums.txt"
    
    return $total_failed
}

# Execute main function
main "$@"