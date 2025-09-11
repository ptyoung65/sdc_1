#!/bin/bash
# Korean RAG AI Models and Language Resources Download Script
# Downloads ALL AI models, Korean language resources, and fonts for offline use

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/models"
FONTS_DIR="$SCRIPT_DIR/fonts"
LANG_DIR="$SCRIPT_DIR/language-resources"
LOG_FILE="$SCRIPT_DIR/models-download.log"

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
mkdir -p "$MODELS_DIR" "$FONTS_DIR" "$LANG_DIR"

log_info "=== Korean RAG AI Models & Language Resources Download ==="

# Korean Language Models - 완전한 오프라인 지원 필요
download_korean_models() {
    log_info "=== Downloading Korean Language Models ==="
    
    # Create Python virtual environment for model downloads
    local venv_dir="$MODELS_DIR/ai-models-venv"
    log_info "Creating virtual environment: $venv_dir"
    python3 -m venv "$venv_dir"
    
    # Activate virtual environment
    source "$venv_dir/bin/activate"
    
    # Install required Python packages in virtual environment
    log_info "Installing packages in virtual environment..."
    "$venv_dir/bin/pip" install --quiet --upgrade pip setuptools wheel
    "$venv_dir/bin/pip" install --quiet sentence-transformers transformers torch kiwipiepy datasets
    
    # KURE-v1 Korean Embedding Model
    log_info "Downloading KURE-v1 Korean embedding model..."
    "$venv_dir/bin/python" << 'EOF'
import os
import shutil
from sentence_transformers import SentenceTransformer

models_dir = os.environ.get('MODELS_DIR', './models')
os.makedirs(models_dir, exist_ok=True)

try:
    # Download KURE-v1 model
    model = SentenceTransformer('KURE')
    model_path = os.path.join(models_dir, 'kure-v1')
    model.save(model_path)
    print(f"KURE-v1 model saved to: {model_path}")
    
    # Also save the cache
    cache_dir = os.path.expanduser('~/.cache/sentence_transformers')
    if os.path.exists(cache_dir):
        cache_target = os.path.join(models_dir, 'sentence_transformers_cache')
        shutil.copytree(cache_dir, cache_target, dirs_exist_ok=True)
        print(f"Sentence transformers cache saved to: {cache_target}")
        
except Exception as e:
    print(f"Error downloading KURE-v1: {e}")
EOF
    
    # Korean BERT Models
    log_info "Downloading Korean BERT models..."
    "$venv_dir/bin/python" << 'EOF'
import os
from transformers import AutoTokenizer, AutoModel

models_dir = os.environ.get('MODELS_DIR', './models')

korean_models = [
    'klue/bert-base',
    'monologg/kobert',
    'skt/kobert-base-v1',
    'beomi/kcbert-base',
]

for model_name in korean_models:
    try:
        safe_name = model_name.replace('/', '_')
        model_path = os.path.join(models_dir, safe_name)
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        
        tokenizer.save_pretrained(model_path)
        model.save_pretrained(model_path)
        
        print(f"Downloaded {model_name} to {model_path}")
    except Exception as e:
        print(f"Error downloading {model_name}: {e}")
EOF

    # Korean language processing models
    log_info "Downloading Korean morphological analyzer..."
    "$venv_dir/bin/python" << 'EOF'
import os
import shutil
from kiwipiepy import Kiwi

models_dir = os.environ.get('MODELS_DIR', './models')
kiwi_dir = os.path.join(models_dir, 'kiwipiepy')
os.makedirs(kiwi_dir, exist_ok=True)

try:
    # Initialize Kiwi to download models
    kiwi = Kiwi()
    
    # Copy kiwi cache
    cache_dir = os.path.expanduser('~/.cache/kiwipiepy')
    if os.path.exists(cache_dir):
        shutil.copytree(cache_dir, os.path.join(kiwi_dir, 'cache'), dirs_exist_ok=True)
        print("Kiwipiepy models cached successfully")
        
except Exception as e:
    print(f"Error with kiwipiepy: {e}")
EOF

    log_success "Korean models download completed"
    
    # Deactivate virtual environment
    deactivate
}

# Korean Fonts Download
download_korean_fonts() {
    log_info "=== Downloading Korean Fonts ==="
    
    # Essential Korean fonts
    local font_urls=(
        "https://github.com/naver/nanumfont/releases/download/VER2.5/NanumFont_TTF_ALL.zip"
        "https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/NotoSansCJK-Regular.ttc"
        "https://github.com/googlefonts/noto-cjk/releases/download/Serif2.001/NotoSerifCJK-Regular.ttc"
    )
    
    for url in "${font_urls[@]}"; do
        local filename=$(basename "$url")
        log_info "Downloading font: $filename"
        
        if wget -q -O "$FONTS_DIR/$filename" "$url"; then
            log_success "Downloaded: $filename"
            
            # Extract zip files
            if [[ "$filename" == *.zip ]]; then
                cd "$FONTS_DIR"
                unzip -q "$filename"
                rm "$filename"
                cd "$SCRIPT_DIR"
            fi
        else
            log_error "Failed to download: $filename"
        fi
    done
    
    # Create fonts manifest
    cat > "$FONTS_DIR/fonts-manifest.txt" << 'EOF'
# Korean Fonts for Air-Gap Deployment
# Install these fonts on the target system for proper Korean text rendering

## Nanum Fonts
- NanumBarunGothic.ttf
- NanumGothic.ttf  
- NanumMyeongjo.ttf

## Google Noto Fonts
- NotoSansCJK-Regular.ttc
- NotoSerifCJK-Regular.ttc

## Installation Instructions:
# Linux: Copy to /usr/share/fonts/korean/
# sudo mkdir -p /usr/share/fonts/korean
# sudo cp *.ttf *.ttc /usr/share/fonts/korean/
# sudo fc-cache -fv
EOF

    log_success "Korean fonts download completed"
}

# Language Resource Download
download_language_resources() {
    log_info "=== Downloading Korean Language Resources ==="
    
    # Korean dictionary and language packs
    python3 << 'EOF'
import os
import urllib.request
import json

lang_dir = os.environ.get('LANG_DIR', './language-resources')
os.makedirs(lang_dir, exist_ok=True)

# Korean stop words
korean_stopwords = [
    "이", "그", "저", "것", "들", "의", "가", "에", "을", "를", "은", "는", "과", "와", "도", "로", "으로",
    "하다", "있다", "되다", "그리고", "또는", "그러나", "하지만", "그래서", "따라서", "만약", "만일",
    "아니다", "없다", "같다", "다르다", "크다", "작다", "좋다", "나쁘다", "많다", "적다"
]

# Save stopwords
with open(os.path.join(lang_dir, 'korean_stopwords.txt'), 'w', encoding='utf-8') as f:
    for word in korean_stopwords:
        f.write(word + '\n')

# Korean number words
korean_numbers = {
    '영': 0, '일': 1, '이': 2, '삼': 3, '사': 4, '오': 5, '육': 6, '칠': 7, '팔': 8, '구': 9,
    '십': 10, '백': 100, '천': 1000, '만': 10000, '억': 100000000, '조': 1000000000000
}

with open(os.path.join(lang_dir, 'korean_numbers.json'), 'w', encoding='utf-8') as f:
    json.dump(korean_numbers, f, ensure_ascii=False, indent=2)

# Korean common words
korean_common = [
    "안녕하세요", "감사합니다", "죄송합니다", "괜찮습니다", "좋습니다", "나쁩니다",
    "사람", "시간", "일", "년", "월", "일", "오늘", "내일", "어제", "지금", "여기", "저기"
]

with open(os.path.join(lang_dir, 'korean_common_words.txt'), 'w', encoding='utf-8') as f:
    for word in korean_common:
        f.write(word + '\n')

print("Korean language resources created successfully")
EOF
    
    # Create installation script
    cat > "$LANG_DIR/install-korean-support.sh" << 'EOF'
#!/bin/bash
# Korean Language Support Installation Script

echo "Installing Korean language support..."

# Install Korean locale
sudo locale-gen ko_KR.UTF-8
sudo update-locale LANG=ko_KR.UTF-8

# Install Korean input method
sudo apt-get update
sudo apt-get install -y \
    language-pack-ko \
    fonts-nanum \
    ibus-hangul \
    fcitx-hangul

# Configure environment
echo "export LANG=ko_KR.UTF-8" >> ~/.bashrc
echo "export LC_ALL=ko_KR.UTF-8" >> ~/.bashrc

echo "Korean support installation completed"
echo "Please reboot or log out/in to apply changes"
EOF
    
    chmod +x "$LANG_DIR/install-korean-support.sh"
    
    log_success "Korean language resources download completed"
}

# PyTorch and ML Libraries Offline Wheels
download_ml_wheels() {
    log_info "=== Downloading ML Library Wheels ==="
    
    local wheels_dir="$MODELS_DIR/wheels"
    mkdir -p "$wheels_dir"
    
    # Create virtual environment for wheel downloads
    local venv_dir="$MODELS_DIR/wheels-venv"
    log_info "Creating wheels virtual environment: $venv_dir"
    python3 -m venv "$venv_dir"
    
    # Activate virtual environment
    source "$venv_dir/bin/activate"
    
    # Download specific ML wheels for offline installation
    pip download --dest "$wheels_dir" \
        torch==2.0.1 \
        torchvision==0.15.2 \
        torchaudio==2.0.2 \
        transformers==4.36.2 \
        sentence-transformers==2.2.2 \
        datasets==2.14.0 \
        accelerate==0.23.0 \
        tokenizers==0.14.1 \
        safetensors==0.4.0 \
        huggingface-hub==0.17.3 \
        --platform linux_x86_64 \
        --python-version 3.11 \
        --no-deps
    
    # Create installation script
    cat > "$wheels_dir/install-ml-wheels.sh" << 'EOF'
#!/bin/bash
# Install ML wheels offline

echo "Installing ML libraries from wheels..."
pip install --no-index --find-links . *.whl
echo "ML libraries installation completed"
EOF
    
    chmod +x "$wheels_dir/install-ml-wheels.sh"
    
    # Deactivate virtual environment
    deactivate
    
    log_success "ML wheels download completed"
}

# Main execution
main() {
    log_info "Starting Korean RAG models and resources download"
    log_info "Models directory: $MODELS_DIR"
    log_info "Fonts directory: $FONTS_DIR" 
    log_info "Language resources directory: $LANG_DIR"
    log_info "Log file: $LOG_FILE"
    
    # Set environment variables for Python scripts
    export MODELS_DIR FONTS_DIR LANG_DIR
    
    # Download all components
    download_korean_models
    download_korean_fonts
    download_language_resources
    download_ml_wheels
    
    # Generate final manifest
    log_info "Generating complete manifest..."
    cat > "$SCRIPT_DIR/ai-models-manifest.txt" << EOF
# Korean RAG AI Models & Resources Manifest
# Generated: $(date)

## Models Directory: $MODELS_DIR
$(find "$MODELS_DIR" -type f -name "*.bin" -o -name "*.safetensors" -o -name "*.json" | head -20)

## Fonts Directory: $FONTS_DIR  
$(find "$FONTS_DIR" -name "*.ttf" -o -name "*.ttc" | head -10)

## Language Resources Directory: $LANG_DIR
$(find "$LANG_DIR" -type f | head -10)

## Total Size:
Models: $(du -sh "$MODELS_DIR" 2>/dev/null | cut -f1 || echo "N/A")
Fonts: $(du -sh "$FONTS_DIR" 2>/dev/null | cut -f1 || echo "N/A") 
Language: $(du -sh "$LANG_DIR" 2>/dev/null | cut -f1 || echo "N/A")
EOF
    
    local total_size=$(du -sh "$SCRIPT_DIR" | cut -f1)
    
    log_success "=== ALL AI MODELS AND RESOURCES DOWNLOADED ==="
    log_info "Total size: $total_size"
    log_info "Manifest: $SCRIPT_DIR/ai-models-manifest.txt"
}

# Execute main function
main "$@"