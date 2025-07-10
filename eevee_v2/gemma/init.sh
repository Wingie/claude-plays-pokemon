#!/bin/bash
"""
Pokemon Gemma VLM Training Environment Setup Script
Prepares machine for production-ready training with TRL multi-image pipeline
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Configuration
CONDA_ENV_NAME="pokemon-gemma-vlm"
PYTHON_VERSION="3.10"
CUDA_VERSION="12.1"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log "🎮 Pokemon Gemma VLM Training Environment Setup"
log "================================================"

# Check system requirements
check_system() {
    log "🔍 Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
        log "Platform: macOS (Apple Silicon/Intel)"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PLATFORM="linux"
        log "Platform: Linux"
    else
        error "Unsupported platform: $OSTYPE"
    fi
    
    # Check available memory
    if [[ "$PLATFORM" == "macos" ]]; then
        TOTAL_MEMORY=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    else
        TOTAL_MEMORY=$(grep MemTotal /proc/meminfo | awk '{print int($2/1024/1024)}')
    fi
    
    log "System Memory: ${TOTAL_MEMORY}GB"
    
    if [[ $TOTAL_MEMORY -lt 16 ]]; then
        warn "Low system memory detected. 32GB+ recommended for training."
    fi
    
    # Check for CUDA on Linux
    if [[ "$PLATFORM" == "linux" ]]; then
        if command -v nvidia-smi &> /dev/null; then
            CUDA_AVAILABLE=true
            GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits)
            log "CUDA available: $GPU_INFO"
        else
            warn "NVIDIA GPU not detected. Training will be very slow on CPU."
            CUDA_AVAILABLE=false
        fi
    else
        log "macOS detected: Will use MPS acceleration if available"
        CUDA_AVAILABLE=false
    fi
}

# Install conda if not present
install_conda() {
    if ! command -v conda &> /dev/null; then
        log "📦 Installing Miniconda..."
        
        if [[ "$PLATFORM" == "macos" ]]; then
            if [[ $(uname -m) == "arm64" ]]; then
                MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
            else
                MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
            fi
        else
            MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
        fi
        
        curl -o miniconda.sh "$MINICONDA_URL"
        bash miniconda.sh -b -p "$HOME/miniconda3"
        source "$HOME/miniconda3/bin/activate"
        conda init bash
        rm miniconda.sh
        
        log "✅ Miniconda installed successfully"
    else
        log "✅ Conda already installed"
    fi
}

# Create conda environment
create_environment() {
    log "🐍 Setting up Python environment..."
    
    # Check if environment already exists
    if conda env list | grep -q "$CONDA_ENV_NAME"; then
        log "Environment $CONDA_ENV_NAME already exists. Skipping creation..."
    else
        # Create new environment
        log "Creating new conda environment: $CONDA_ENV_NAME"
        conda create -n "$CONDA_ENV_NAME" python="$PYTHON_VERSION" -y
    fi
    
    # Activate environment
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_NAME"
    
    log "✅ Python environment created and activated"
}

# Install PyTorch with appropriate backend
install_pytorch() {
    log "🔥 Installing PyTorch..."
    
    if [[ "$PLATFORM" == "macos" ]]; then
        # macOS: Use MPS acceleration
        log "Installing PyTorch for macOS with MPS support"
        pip install torch torchvision torchaudio
        
    elif [[ "$CUDA_AVAILABLE" == true ]]; then
        # Linux with CUDA
        log "Installing PyTorch with CUDA $CUDA_VERSION support"
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        
    else
        # CPU-only fallback
        warn "Installing CPU-only PyTorch (training will be very slow)"
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Verify PyTorch installation
    python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
    
    if [[ "$PLATFORM" == "macos" ]]; then
        python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
    elif [[ "$CUDA_AVAILABLE" == true ]]; then
        python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
        python -c "import torch; print(f'CUDA devices: {torch.cuda.device_count()}')" || true
    fi
    
    log "✅ PyTorch installed successfully"
}

# Install TRL from PyPI
install_trl() {
    log "🚀 Installing TRL from PyPI..."
    
    # Install latest stable version from PyPI
    pip install trl
    
    # Verify TRL installation
    python -c "import trl; print(f'TRL version: {trl.__version__}')"
    
    log "✅ TRL installed from PyPI"
}

# Install other dependencies
install_dependencies() {
    log "📦 Installing additional dependencies..."
    
    # Install from requirements.txt
    pip install -r requirements.txt
    
    # Install additional tools
    pip install accelerate transformers datasets
    
    # Install HuggingFace CLI
    pip install --upgrade huggingface_hub
    
    # Install MLX only on macOS (Apple Silicon)
    if [[ "$PLATFORM" == "macos" ]]; then
        log "🍎 Installing MLX dependencies for Apple Silicon..."
        pip install mlx mlx-lm || warn "MLX installation failed (requires Apple Silicon)"
    else
        log "⏭️  Skipping MLX installation (Linux/Windows not supported)"
    fi
    
    log "✅ Dependencies installed successfully"
}

# Setup HuggingFace authentication
setup_huggingface() {
    log "🤗 Setting up HuggingFace authentication..."
    
    if [[ -z "${HF_TOKEN:-}" ]]; then
        warn "HF_TOKEN environment variable not set"
        echo -e "${BLUE}Please set your HuggingFace token:${NC}"
        echo "export HF_TOKEN='your_token_here'"
        echo ""
        echo "Or run: huggingface-cli login"
        echo ""
    else
        echo "$HF_TOKEN" | huggingface-cli login --token stdin
        log "✅ HuggingFace authentication configured"
    fi
    
    # Test model access
    log "Testing Gemma model access..."
    python -c "
from transformers import AutoTokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained('google/gemma-3-4b-it')
    print('✅ Gemma 3-4B model access verified')
except Exception as e:
    print(f'❌ Cannot access Gemma models: {e}')
    print('Please ensure you have accepted the Gemma license and have a valid HF token')
" || warn "Gemma model access test failed"
}

# Configure accelerate
setup_accelerate() {
    log "⚡ Configuring Accelerate..."
    
    # Create accelerate config directory
    mkdir -p accelerate_configs
    
    # Generate basic config
    if [[ "$CUDA_AVAILABLE" == true ]]; then
        log "Configuring for CUDA training"
        accelerate config --config_file accelerate_configs/single_gpu.yaml
    else
        log "Configuring for CPU/MPS training"
        accelerate config --config_file accelerate_configs/cpu_mps.yaml
    fi
    
    log "✅ Accelerate configured"
}

# Setup wandb
setup_wandb() {
    log "📊 Setting up Weights & Biases..."
    
    if [[ -z "${WANDB_API_KEY:-}" ]]; then
        warn "WANDB_API_KEY not set. Run 'wandb login' to configure."
    else
        echo "$WANDB_API_KEY" | wandb login
        log "✅ Wandb authentication configured"
    fi
}

# Validate installation
validate_installation() {
    log "🔍 Validating installation..."
    
    # Test imports
    python -c "
import torch
import transformers
import trl
import accelerate
import datasets
from PIL import Image
import numpy as np

print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ Transformers: {transformers.__version__}')
print(f'✅ TRL: {trl.__version__}')
print(f'✅ Accelerate: {accelerate.__version__}')
print(f'✅ Datasets: {datasets.__version__}')
print('✅ All core dependencies imported successfully')
"
    
    # Check GPU availability
    if [[ "$PLATFORM" == "macos" ]]; then
        python -c "
import torch
if torch.backends.mps.is_available():
    print('✅ MPS acceleration available')
    device = torch.device('mps')
    x = torch.randn(10, 10).to(device)
    print(f'✅ MPS test tensor created: {x.shape}')
else:
    print('❌ MPS not available')
"
    elif [[ "$CUDA_AVAILABLE" == true ]]; then
        python -c "
import torch
if torch.cuda.is_available():
    print(f'✅ CUDA available: {torch.cuda.device_count()} devices')
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        memory_gb = props.total_memory / 1024**3
        print(f'  GPU {i}: {props.name} ({memory_gb:.1f}GB)')
else:
    print('❌ CUDA not available')
"
    fi
    
    log "✅ Installation validation complete"
}

# Print usage instructions
print_usage() {
    log "🎯 Setup Complete! Next Steps:"
    echo ""
    echo -e "${BLUE}1. Activate environment:${NC}"
    echo "   conda activate $CONDA_ENV_NAME"
    echo ""
    echo -e "${BLUE}2. Setup HuggingFace token (if not done):${NC}"
    echo "   export HF_TOKEN='your_token_here'"
    echo "   huggingface-cli login"
    echo ""
    echo -e "${BLUE}3. Setup Wandb (optional):${NC}"
    echo "   export WANDB_API_KEY='your_key_here'"
    echo "   wandb login"
    echo ""
    echo -e "${BLUE}4. Run data conversion:${NC}"
    echo "   python scripts/convert_eevee_data_v2.py \\"
    echo "     --eevee_runs_dir /path/to/eevee/runs \\"
    echo "     --output_file training_data/pokemon_4frame_dataset.jsonl \\"
    echo "     --copy_images"
    echo ""
    echo -e "${BLUE}5. Start training:${NC}"
    echo "   bash scripts/train_gemma3.sh"
    echo ""
    echo -e "${GREEN}Environment ready for Pokemon Gemma VLM training! 🎮${NC}"
}

# Main execution
main() {
    log "Starting setup process..."
    
    # Change to project directory
    cd "$PROJECT_DIR" || error "Cannot access project directory: $PROJECT_DIR"
    
    # Run setup steps
    check_system
    install_conda
    create_environment
    install_pytorch
    install_trl
    install_dependencies
    setup_huggingface
    setup_accelerate
    setup_wandb
    validate_installation
    print_usage
    
    log "🎉 Setup completed successfully!"
}

# Run main function
main "$@"